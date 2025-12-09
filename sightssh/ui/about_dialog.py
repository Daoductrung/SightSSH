import wx
import wx.adv
import webbrowser
from sightssh.core.i18n import tr
from sightssh import __version__

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=tr("dlg_about_title"), size=(400, 350))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title / Intro
        lbl_msg = wx.StaticText(self, label=tr("msg_about_intro"))
        lbl_msg.Wrap(350)
        sizer.Add(lbl_msg, 0, wx.ALL | wx.CENTER, 15)
        
        # Version
        lbl_ver = wx.StaticText(self, label=f"Version: {__version__}")
        sizer.Add(lbl_ver, 0, wx.ALL | wx.CENTER, 5)
        
        lbl_created = wx.StaticText(self, label=tr("lbl_created_by"))
        sizer.Add(lbl_created, 0, wx.ALL | wx.CENTER, 5)
        
        # Contact Info Group
        sb = wx.StaticBox(self, label=tr("lbl_contact_info"))
        sb_sizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        # Email
        self.lbl_email = wx.TextCtrl(sb, value="trung@ddt.one", style=wx.TE_READONLY | wx.TE_CENTER | wx.BORDER_NONE)
        self.lbl_email.SetBackgroundColour(self.GetBackgroundColour())
        
        # Website Link
        self.lbl_website = wx.adv.HyperlinkCtrl(sb, label="ddt.one/contact", url="https://ddt.one/contact")
        
        sb_sizer.Add(wx.StaticText(sb, label=tr("lbl_email") + ":"), 0, wx.ALIGN_CENTER | wx.TOP, 10)
        sb_sizer.Add(self.lbl_email, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        sb_sizer.Add(wx.StaticText(sb, label=tr("lbl_website") + ":"), 0, wx.ALIGN_CENTER | wx.TOP, 10)
        sb_sizer.Add(self.lbl_website, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        sizer.Add(sb_sizer, 0, wx.EXPAND | wx.ALL, 15)
        
        btn_close = wx.Button(self, wx.ID_OK, label=tr("btn_close"))
        sizer.Add(btn_close, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        btn_close.SetFocus()
