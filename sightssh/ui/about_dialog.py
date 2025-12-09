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
        lbl_ver = wx.StaticText(self, label=tr("lbl_version").format(version=__version__))
        sizer.Add(lbl_ver, 0, wx.ALL | wx.CENTER, 5)
        
        lbl_created = wx.StaticText(self, label=tr("lbl_created_by"))
        sizer.Add(lbl_created, 0, wx.ALL | wx.CENTER, 5)
        
        # Contact Info (List)
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, tr("lbl_type"), width=100)
        self.list_ctrl.InsertColumn(1, tr("col_description"), width=250)
        
        # Data
        self.contacts = [
            (tr("lbl_email"), "trung@ddt.one", "mailto:trung@ddt.one"),
            (tr("lbl_website"), "ddt.one/contact", "https://ddt.one/contact")
        ]
        
        for i, (kind, display, url) in enumerate(self.contacts):
            self.list_ctrl.InsertItem(i, kind)
            self.list_ctrl.SetItem(i, 1, display)
            
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 15)
        
        # Bindings
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        
        btn_close = wx.Button(self, wx.ID_OK, label=tr("btn_close"))
        sizer.Add(btn_close, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        self.list_ctrl.SetFocus()

    def on_item_activated(self, event):
        idx = event.GetIndex()
        if idx != wx.NOT_FOUND:
            url = self.contacts[idx][2]
            webbrowser.open(url)
