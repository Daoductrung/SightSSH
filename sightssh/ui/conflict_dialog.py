import wx
from sightssh.core.i18n import tr

class ConflictDialog(wx.Dialog):
    def __init__(self, parent, filename):
        super().__init__(parent, title=tr("dlg_conflict_title"), size=(450, 250))
        self.filename = filename
        self.action = "cancel"
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Message
        msg = tr("msg_conflict_exist").format(filename=filename)
        lbl = wx.StaticText(self, label=msg)
        lbl.Wrap(400)
        sizer.Add(lbl, 0, wx.ALL | wx.EXPAND, 15)
        
        # New Name Input (Hidden by default, used for Rename)
        self.rename_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lbl_rename = wx.StaticText(self, label=tr("lbl_new_name"))
        self.txt_rename = wx.TextCtrl(self, value=f"copy_{filename}")
        self.rename_sizer.Add(self.lbl_rename, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.rename_sizer.Add(self.txt_rename, 1, wx.EXPAND)
        
        # We don't show rename input immediately in this design?
        # Standard conflict dialogs usually have 'Rename' as a button that prompts or auto-renames.
        # Let's keep it simple: Click Rename -> Dialog closes -> Caller handles logic (maybe showing another prompt or auto-rename).
        # OR: We show the input field IF 'Rename' is selected? 
        # Simpler for v0.3: Rename button just returns 'rename' action. 
        # The upload logic can then prompt for a name or append _copy.
        # Adding an input field inside this dialog is cleaner though.
        
        # Let's stick to simple buttons first.
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_overwrite = wx.Button(self, label=tr("btn_overwrite"))
        self.btn_skip = wx.Button(self, label=tr("btn_skip"))
        self.btn_rename = wx.Button(self, label=tr("btn_rename"))
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, label=tr("btn_cancel"))
        
        self.btn_overwrite.Bind(wx.EVT_BUTTON, lambda e: self.on_action("overwrite"))
        self.btn_skip.Bind(wx.EVT_BUTTON, lambda e: self.on_action("skip"))
        self.btn_rename.Bind(wx.EVT_BUTTON, lambda e: self.on_action("rename"))
        
        btn_sizer.Add(self.btn_overwrite, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_skip, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_rename, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_cancel, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 15)
        
        # Apply to all
        self.chk_apply_all = wx.CheckBox(self, label=tr("chk_apply_all"))
        sizer.Add(self.chk_apply_all, 0, wx.ALL | wx.ALIGN_LEFT, 15)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        
        # Default focus
        self.btn_overwrite.SetFocus()

    def on_action(self, action):
        self.action = action
        self.EndModal(wx.ID_OK)

    def GetAction(self):
        return self.action

    def IsApplyAll(self):
        return self.chk_apply_all.GetValue()
