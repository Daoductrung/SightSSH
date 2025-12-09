import wx
from sightssh.core.i18n import tr

class PermissionsDialog(wx.Dialog):
    def __init__(self, parent, current_mode, show_recursive=False):
        super().__init__(parent, title=tr("lbl_permissions"), size=(350, 450))
        self.mode = current_mode
        self.result_mode = current_mode
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Helper to create group box
        def create_group(label, offset):
            sb = wx.StaticBox(self, label=label)
            sb_sizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            
            chk_r = wx.CheckBox(sb, label=tr("lbl_read"), name=f"{label} {tr('lbl_read')}")
            chk_w = wx.CheckBox(sb, label=tr("lbl_write"), name=f"{label} {tr('lbl_write')}")
            chk_x = wx.CheckBox(sb, label=tr("lbl_execute"), name=f"{label} {tr('lbl_execute')}")
            
            # Set initial values based on mode bitmask
            # Mode structure: ... rwx rwx rwx (Owner, Group, Others)
            # Offsets: Owner=6, Group=3, Others=0 (shifts)
            chk_r.SetValue((self.mode >> (offset + 2)) & 1)
            chk_w.SetValue((self.mode >> (offset + 1)) & 1)
            chk_x.SetValue((self.mode >> offset) & 1)
            
            sb_sizer.Add(chk_r, 0, wx.ALL, 5)
            sb_sizer.Add(chk_w, 0, wx.ALL, 5)
            sb_sizer.Add(chk_x, 0, wx.ALL, 5)
            
            chk_r.Bind(wx.EVT_CHECKBOX, self.on_check)
            chk_w.Bind(wx.EVT_CHECKBOX, self.on_check)
            chk_x.Bind(wx.EVT_CHECKBOX, self.on_check)
            
            return sb_sizer, chk_r, chk_w, chk_x

        # Create Groups
        self.grp_owner = create_group(tr("lbl_owner"), 6)
        self.grp_group = create_group(tr("lbl_group"), 3)
        self.grp_others = create_group(tr("lbl_others"), 0)
        
        sizer.Add(self.grp_owner[0], 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.grp_group[0], 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.grp_others[0], 0, wx.EXPAND | wx.ALL, 10)
        
        # Numeric Value
        num_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lbl_num = wx.StaticText(self, label=tr("lbl_octal"))
        self.txt_octal = wx.TextCtrl(self, value=oct(self.mode & 0o777)[2:])
        self.txt_octal.Bind(wx.EVT_TEXT, self.on_text)
        
        num_sizer.Add(lbl_num, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        num_sizer.Add(self.txt_octal, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(num_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Recursive Checkbox
        self.chk_recursive = wx.CheckBox(self, label=tr("chk_recursive"))
        if not show_recursive:
            self.chk_recursive.Hide()
        sizer.Add(self.chk_recursive, 0, wx.ALL, 10)
        
        # Buttons
        btns = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_save = wx.Button(self, wx.ID_OK, label=tr("btn_save"))
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, label=tr("btn_cancel"))
        
        btns.Add(self.btn_save, 0, wx.RIGHT, 10)
        btns.Add(self.btn_cancel, 0)
        
        sizer.Add(btns, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.CenterOnParent()
        
        # Set Focus to Octal Input for convenience
        self.txt_octal.SetFocus()

    def on_check(self, event):
        # Re-calculate mode from checkboxes
        new_mode = 0
        
        # Owner
        if self.grp_owner[1].GetValue(): new_mode |= 0o400
        if self.grp_owner[2].GetValue(): new_mode |= 0o200
        if self.grp_owner[3].GetValue(): new_mode |= 0o100
        
        # Group
        if self.grp_group[1].GetValue(): new_mode |= 0o040
        if self.grp_group[2].GetValue(): new_mode |= 0o020
        if self.grp_group[3].GetValue(): new_mode |= 0o010
        
        # Others
        if self.grp_others[1].GetValue(): new_mode |= 0o004
        if self.grp_others[2].GetValue(): new_mode |= 0o002
        if self.grp_others[3].GetValue(): new_mode |= 0o001
        
        self.result_mode = new_mode
        self.txt_octal.ChangeValue(oct(new_mode)[2:])

    def on_text(self, event):
        val = self.txt_octal.GetValue()
        try:
            if len(val) > 4: return # Simple Validation
            mode = int(val, 8)
            
            # Update Checkboxes safely
            def update_grp(grp, offset):
                grp[1].SetValue((mode >> (offset + 2)) & 1)
                grp[2].SetValue((mode >> (offset + 1)) & 1)
                grp[3].SetValue((mode >> offset) & 1)
                
            update_grp(self.grp_owner, 6)
            update_grp(self.grp_group, 3)
            update_grp(self.grp_others, 0)
            
            self.result_mode = mode
        except ValueError:
            pass # Ignore invalid input while typing

    def GetMode(self):
        return self.result_mode

    def IsRecursive(self):
        # Checkbox might be hidden
        return self.chk_recursive.IsShown() and self.chk_recursive.GetValue()
