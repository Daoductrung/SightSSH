import wx
import webbrowser
from sightssh.core.i18n import tr

class UpdateDialog(wx.Dialog):
    def __init__(self, parent, current_version, new_version, changelog):
        super().__init__(parent, title="SightSSH Update", size=(500, 400))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Message
        msg = tr("msg_dump_update").format(
            current=current_version,
            new=new_version,
            changelog="" # Changelog handled separately for layout
        )
        
        # Split message to header/changelog for better layout control
        # Actually simplistic approach: format string up to changelog
        header_text = tr("msg_dump_update").split("{changelog}")[0].format(
            current=current_version,
            new=new_version
        )
        
        lbl_header = wx.StaticText(self, label=header_text)
        sizer.Add(lbl_header, 0, wx.ALL | wx.EXPAND, 15)
        
        # Changelog Text (Read Only)
        self.txt_changelog = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.txt_changelog.SetValue(changelog)
        sizer.Add(self.txt_changelog, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_download = wx.Button(self, label=tr("btn_update_download"))
        self.btn_close = wx.Button(self, wx.ID_CANCEL, label=tr("btn_close"))
        
        self.btn_download.Bind(wx.EVT_BUTTON, self.on_download)
        
        btn_sizer.Add(self.btn_download, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_close, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 15)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        
        # Focus changelog for reading
        self.txt_changelog.SetFocus()

    def on_download(self, event):
        webbrowser.open("https://github.com/Daoductrung/SightSSH/releases/latest")
        self.Close()
