import threading
import config
import wx
import gui
import globalPluginHandler
import ui
import addonHandler
import webbrowser
from scriptHandler import script
from . import google_currency as gc

# Initialize translation for the add-on
addonHandler.initTranslation()

# Currency code dictionary
currency_codes = {}
for key, value in gc.CODES.items():
    currency_codes[value] = key

# Configuration specification
SECTION_NAME = "CurrencyConverter"
configspec = {
    "from": "string(default=USD)",
    "to": "string(default=NPR)"
}
config.conf.spec[SECTION_NAME] = configspec

class WelcomeDialog(wx.Dialog):
    def __init__(self, parent=None):
        super(WelcomeDialog, self).__init__(parent or gui.mainFrame, title=_("Developed by: Sujan Rai"))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        message = _("Hi, join my Telegram channel for new tools, resources, and software.\nRead my blogs for the latest tutorials on technology.")
        self.messageCtrl = wx.StaticText(self, label=message)
        mainSizer.Add(self.messageCtrl, proportion=0, flag=wx.ALL, border=10)
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.telegramBtn = wx.Button(self, label=_("Join Telegram"))
        self.blogBtn = wx.Button(self, label=_("Read Blogs"))
        self.noThanksBtn = wx.Button(self, label=_("No Thanks"))
        
        buttonSizer.Add(self.telegramBtn, flag=wx.RIGHT, border=5)
        buttonSizer.Add(self.blogBtn, flag=wx.RIGHT, border=5)
        buttonSizer.Add(self.noThanksBtn, flag=wx.RIGHT, border=5)
        
        mainSizer.Add(buttonSizer, flag=wx.ALL | wx.CENTER, border=10)
        
        self.telegramBtn.Bind(wx.EVT_BUTTON, self.onTelegram)
        self.blogBtn.Bind(wx.EVT_BUTTON, self.onBlog)
        self.noThanksBtn.Bind(wx.EVT_BUTTON, self.onNoThanks)
        
        self.SetSizerAndFit(mainSizer)
        self.noThanksBtn.SetFocus()
        
    def onTelegram(self, event):
        webbrowser.open("https://t.me/techvisionary")
        self.Close()
        
    def onBlog(self, event):
        webbrowser.open("https://techvisionaryarticles.blogspot.com")
        self.Close()
        
    def onNoThanks(self, event):
        self.Close()

class TextWindow(wx.Dialog):
    def __init__(self, text, title):
        super(TextWindow, self).__init__(gui.mainFrame, title=title)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # Currency selection
        self.fromLabel = wx.StaticText(self, label=_("Select the currency that you want to convert from"))
        self.fromChoice = wx.Choice(self, name="from_currency")
        mainSizer.Add(self.fromLabel, flag=wx.ALL, border=5)
        mainSizer.Add(self.fromChoice, flag=wx.ALL | wx.EXPAND, border=5)
        
        self.toLabel = wx.StaticText(self, label=_("Select the currency that you want to convert to"))
        self.toChoice = wx.Choice(self, name="to_currency")
        mainSizer.Add(self.toLabel, flag=wx.ALL, border=5)
        mainSizer.Add(self.toChoice, flag=wx.ALL | wx.EXPAND, border=5)
        
        # Amount input
        self.amountLabel = wx.StaticText(self, label=_("Amount"))
        self.amountCtrl = wx.SpinCtrl(self, min=1, max=1000000, initial=text)
        mainSizer.Add(self.amountLabel, flag=wx.ALL, border=5)
        mainSizer.Add(self.amountCtrl, flag=wx.ALL | wx.EXPAND, border=5)
        
        # Buttons
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.convertBtn = wx.Button(self, label=_("Convert"))
        self.exitBtn = wx.Button(self, label=_("Exit"))
        buttonSizer.Add(self.convertBtn, flag=wx.RIGHT, border=5)
        buttonSizer.Add(self.exitBtn, flag=wx.RIGHT, border=5)
        
        mainSizer.Add(buttonSizer, flag=wx.ALL | wx.CENTER, border=10)
        
        self.convertBtn.Bind(wx.EVT_BUTTON, self.onConvert)
        self.exitBtn.Bind(wx.EVT_BUTTON, self.onExit)
        self.Bind(wx.EVT_CHAR_HOOK, self.onHook)
        
        self.setChoices()
        self.amountCtrl.SetFocus()
        self.SetSizerAndFit(mainSizer)
        
    def setChoices(self):
        self.fromChoice.Set(list(currency_codes.keys()))
        self.toChoice.Set(list(currency_codes.keys()))
        try:
            self.fromChoice.SetStringSelection(gc.CODES[config.conf[SECTION_NAME]["from"]])
            self.toChoice.SetStringSelection(gc.CODES[config.conf[SECTION_NAME]["to"]])
        except KeyError:
            self.fromChoice.SetStringSelection(gc.CODES["USD"])
            self.toChoice.SetStringSelection(gc.CODES["NPR"])
        
    def onHook(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Destroy()
        event.Skip()
        
    def onConvert(self, event):
        config.conf[SECTION_NAME]["from"] = currency_codes[self.fromChoice.GetStringSelection()]
        config.conf[SECTION_NAME]["to"] = currency_codes[self.toChoice.GetStringSelection()]
        try:
            amount = self.amountCtrl.GetValue()
            result = gc.convert(config.conf[SECTION_NAME]["from"], config.conf[SECTION_NAME]["to"], amount)
            output = _("Hi, {} {} is equivalently {} {}").format(
                amount,
                config.conf[SECTION_NAME]["from"],
                result,
                config.conf[SECTION_NAME]["to"]
            )
            ResultDialog(output, _("Conversion Result"))
        except Exception as e:
            ResultDialog(_("Error: {}").format(str(e)), _("Error"))
        self.Close()
        
    def onExit(self, event):
        self.Destroy()

class ResultDialog(wx.Dialog):
    def __init__(self, text, title):
        super(ResultDialog, self).__init__(gui.mainFrame, title=title)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.outputCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.outputCtrl.Bind(wx.EVT_KEY_DOWN, self.onOutputKeyDown)
        mainSizer.Add(self.outputCtrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.backBtn = wx.Button(self, label=_("Back"))
        self.exitBtn = wx.Button(self, label=_("Exit"))
        buttonSizer.Add(self.backBtn, flag=wx.RIGHT, border=5)
        buttonSizer.Add(self.exitBtn, flag=wx.RIGHT, border=5)
        
        mainSizer.Add(buttonSizer, flag=wx.ALL | wx.CENTER, border=10)
        
        self.backBtn.Bind(wx.EVT_BUTTON, self.onBack)
        self.exitBtn.Bind(wx.EVT_BUTTON, self.onExit)
        
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.outputCtrl.SetValue(text)
        self.outputCtrl.SetFocus()
        self.Maximize()
        
    def onOutputKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        event.Skip()
        
    def onBack(self, event):
        self.Close()
        TextWindow(1, _("Currency Dialog"))
        
    def onExit(self, event):
        self.Destroy()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("Currency Converter")
    
    def __init__(self):
        super().__init__()
        self.toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
        self.menuItem = self.toolsMenu.Append(wx.ID_ANY, _("Currency Converter"), _("Open currency converter dialog"))
        gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.script_openConverter, self.menuItem)
        # Show WelcomeDialog on add-on initialization
        wx.CallAfter(WelcomeDialog().Show)
        
    @script(gesture="kb:NVDA+alt+c")
    def script_openConverter(self, gesture):
        # Show WelcomeDialog before opening the currency converter
        welcome = WelcomeDialog()
        welcome.Show()
        # Wait for WelcomeDialog to close before showing TextWindow
        welcome.Bind(wx.EVT_CLOSE, lambda evt: self.showTextWindow(evt))
        
    def showTextWindow(self, event):
        event.Skip()
        wx.CallAfter(TextWindow, 1, _("Currency Dialog"))
        
    script_openConverter.__doc__ = _("Open currency converter dialog")
    
    def terminate(self):
        try:
            self.toolsMenu.Remove(self.menuItem)
        except Exception:
            pass
