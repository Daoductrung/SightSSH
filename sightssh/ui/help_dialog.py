import wx
from sightssh.core.i18n import tr

class HelpDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=tr("dlg_help_title"), size=(500, 450))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.lbl_intro = wx.StaticText(self, label=tr("msg_help_intro"))
        sizer.Add(self.lbl_intro, 0, wx.ALL | wx.EXPAND, 15)
        
        # Shortcuts List
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, tr("col_shortcut"), width=150)
        self.list_ctrl.InsertColumn(1, tr("col_description"), width=300)
        
        shortcuts = [
            ("Alt + V", tr("hlp_view_profiles")),
            ("Alt + C", tr("hlp_create_profile")),
            ("Alt + S", tr("hlp_settings")),
            ("Alt + Q", tr("hlp_disconnect")),
            ("Alt + O", tr("hlp_open_sftp")),
            ("Ctrl + Shift + V", tr("hlp_paste")),
            ("F2", tr("hlp_rename")),
            ("Delete", tr("hlp_delete")),
            ("F5", tr("hlp_refresh")),
            ("Backspace", tr("hlp_back_dir")),
            ("Shift + Enter", tr("hlp_multiline")),
            ("Alt + H", tr("btn_shortcuts"))
        ]
        
        for i, (key, desc) in enumerate(shortcuts):
            self.list_ctrl.InsertItem(i, key)
            self.list_ctrl.SetItem(i, 1, desc)
            
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        btn_close = wx.Button(self, wx.ID_OK, label=tr("btn_close"))
        sizer.Add(btn_close, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        self.list_ctrl.SetFocus()
