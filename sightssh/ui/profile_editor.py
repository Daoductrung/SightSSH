import wx
from sightssh.core.config_manager import ConfigManager
from sightssh.accessibility.speech import SpeechManager
from sightssh.core.i18n import tr

class ProfileEditorPanel(wx.Panel):
    def __init__(self, parent, profile_name=None, existing_data=None, profile_password=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.speech = SpeechManager()
        
        self.profile_name = profile_name
        self.is_editing = profile_name is not None
        
        self.init_ui(existing_data)
        
    def init_ui(self, data):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        title = tr("lbl_edit_profile") if self.is_editing else tr("lbl_new_profile")
        header = wx.StaticText(self, label=title)
        sizer.Add(header, 0, wx.ALL, 10)

        # Form Layout
        # Use rows=0 to allow dynamic number of rows based on added items
        form_sizer = wx.FlexGridSizer(rows=0, cols=2, vgap=10, hgap=10)
        
        # Name
        form_sizer.Add(wx.StaticText(self, label=tr("lbl_profile_name")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.txt_name = wx.TextCtrl(self, value=self.profile_name if self.profile_name else "")
        if self.is_editing:
            self.txt_name.Disable() # Don't allow renaming for now to keep ID simple
        form_sizer.Add(self.txt_name, 1, wx.EXPAND)

        # Host
        form_sizer.Add(wx.StaticText(self, label=tr("lbl_host")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.txt_host = wx.TextCtrl(self, value=data['host'] if data else "")
        form_sizer.Add(self.txt_host, 1, wx.EXPAND)

        # Port
        form_sizer.Add(wx.StaticText(self, label=tr("lbl_port")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.txt_port = wx.TextCtrl(self, value=str(data['port']) if data else "22")
        form_sizer.Add(self.txt_port, 1, wx.EXPAND)

        # Username
        form_sizer.Add(wx.StaticText(self, label=tr("lbl_username")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.txt_user = wx.TextCtrl(self, value=data['username'] if data else "")
        form_sizer.Add(self.txt_user, 1, wx.EXPAND)

        # Auth Type
        form_sizer.Add(wx.StaticText(self, label=tr("lbl_auth_type")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.radio_auth = wx.RadioBox(self, choices=[tr("val_password"), tr("val_key_file")])
        if data and data.get('auth_type') == 'key':
            self.radio_auth.SetSelection(1)
        form_sizer.Add(self.radio_auth, 1, wx.EXPAND)
        self.radio_auth.Bind(wx.EVT_RADIOBOX, self.on_auth_type_changed)

        # SSH Password / Key Info
        self.lbl_secret = wx.StaticText(self, label=tr("lbl_ssh_pass"))
        form_sizer.Add(self.lbl_secret, 0, wx.ALIGN_CENTER_VERTICAL)
        # Using TextCtrl even for Key Path for now (simple), ideally FilePicker for Key
        self.txt_secret = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=data['secret'] if data else "")
        form_sizer.Add(self.txt_secret, 1, wx.EXPAND)

        # Profile Lock Checkbox
        form_sizer.Add(wx.StaticText(self, label=tr("lbl_security")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.chk_protected = wx.CheckBox(self, label=tr("chk_protect_profile"))
        form_sizer.Add(self.chk_protected, 1, wx.EXPAND)
        self.chk_protected.Bind(wx.EVT_CHECKBOX, self.on_protect_changed)

        # Profile Lock Password
        self.lbl_prof_pass = wx.StaticText(self, label=tr("lbl_lock_pass"))
        form_sizer.Add(self.lbl_prof_pass, 0, wx.ALIGN_CENTER_VERTICAL)
        self.txt_profile_pass = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        form_sizer.Add(self.txt_profile_pass, 1, wx.EXPAND)
        
        # Confirm Profile Lock
        self.lbl_prof_pass_conf = wx.StaticText(self, label=tr("lbl_confirm_pass"))
        form_sizer.Add(self.lbl_prof_pass_conf, 0, wx.ALIGN_CENTER_VERTICAL)
        self.txt_profile_pass_confirm = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        form_sizer.Add(self.txt_profile_pass_confirm, 1, wx.EXPAND)

        # Logic to initialize states
        self.on_auth_type_changed(None)
        
        # If we passed existing profile_password, maybe pre-check/pre-fill?
        # Actually in this flow, we usually edit with known password.
        # Ideally we allow changing it.
        # Providing a way to 'Keep Current' or 'Change'?
        # For simplicity MVP: If protected, user must re-enter new password or we keep old effectively?
        # Current save logic requires password if protected.
        # Let's simple: Checked = enabled fields. Unchecked = disabled.
        self.chk_protected.SetValue(True) # Default secure?
        if data:
            # How do we know if it WAS protected? 
            # Our config saves encrypted secret always?
            # If secret is non-empty, we used a key.
            # Users wanted OPTIONAL.
            # If optional, we use a default key or no encryption?
            # Requirement: "khong bat buoc".
            # If checked, enable pass fields.
            pass
        
        self.on_protect_changed(None) # Refresh UI state

        sizer.Add(form_sizer, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_save = wx.Button(self, label=tr("btn_save"))
        self.btn_cancel = wx.Button(self, label=tr("btn_cancel"))
        
        btn_sizer.Add(self.btn_save, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_cancel, 0)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # Bindings
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        # Sizer setup
        form_sizer.AddGrowableCol(1, 1) # Expand text fields
        self.SetSizer(sizer)
        self.Layout()
        self.Fit() # Ensure it fits
        
        # Initial focus
        self.txt_name.SetFocus()

    def on_auth_type_changed(self, event):
        if self.radio_auth.GetSelection() == 0:
            self.lbl_secret.SetLabel(tr("lbl_ssh_pass"))
        else:
            self.lbl_secret.SetLabel(tr("lbl_key_path"))
            
    def on_protect_changed(self, event):
        is_protected = self.chk_protected.GetValue()
        
        # Enable/Disable is good, but hiding might be cleaner if requested?
        # User said "vẫn hiển thị" implies they shouldn't be valid targets.
        
        self.lbl_prof_pass.Show(is_protected)
        self.txt_profile_pass.Show(is_protected)
        self.lbl_prof_pass_conf.Show(is_protected)
        self.txt_profile_pass_confirm.Show(is_protected)
        
        if not is_protected:
            self.txt_profile_pass.Clear()
            self.txt_profile_pass_confirm.Clear()
        
        # Re-layout to adjust space if hidden (GridSizer doesn't auto-collapse well without help)
        # FlexGridSizer doesn't fully collapse headers if we just Hide keys. 
        # But for now Show/Hide is better than just Gray.
        self.Layout()

    def on_save(self, event):
        name = self.txt_name.GetValue().strip()
        host = self.txt_host.GetValue().strip()
        port = self.txt_port.GetValue().strip()
        user = self.txt_user.GetValue().strip()
        auth_type = "password" if self.radio_auth.GetSelection() == 0 else "key"
        secret = self.txt_secret.GetValue()
        
        is_protected = self.chk_protected.GetValue()
        prof_pass = self.txt_profile_pass.GetValue()
        prof_pass_conf = self.txt_profile_pass_confirm.GetValue()

        if not name or not host or not user or not port:
            wx.MessageBox(tr("msg_fill_required"), tr("app_title"), wx.ICON_WARNING)
            return

        final_prof_pass = ""
        if is_protected:
            if not prof_pass:
                wx.MessageBox(tr("msg_pass_required"), tr("app_title"), wx.ICON_WARNING)
                return
            if prof_pass != prof_pass_conf:
                wx.MessageBox(tr("msg_pass_mismatch"), tr("app_title"), wx.ICON_WARNING)
                return
            final_prof_pass = prof_pass
        else:
            # Unprotected: Use a hardcoded default system key or empty string?
            # ConfigManager expects a password to derive key.
            # We can use a default internal key for "unprotected" profiles.
            final_prof_pass = "UNPROTECTED_SIGHTSSH_DEFAULT_KEY"

        try:
            self.config.save_profile(
                name=name,
                host=host,
                port=int(port),
                username=user,
                auth_type=auth_type,
                secret=secret,
                key_path="", 
                profile_password=final_prof_pass
            )
            self.speech.speak(tr("msg_profile_saved"))
            self.on_cancel(None) # Go back
        except Exception as e:
            wx.MessageBox(tr("err_save_profile").format(error=e), tr("app_title"), wx.ICON_ERROR)

    def on_cancel(self, event):
        # Go back to previous screen
        # If we came from View Profiles, go there. If from Start, go there.
        # For simplicity, go to Start or View Profiles depending on context?
        # Let's go to View Profiles if we were editing, or Start if creating? 
        # Actually MainFrame logic is simpler if we just go back to Welcome or Profile List.
        # Let's default to Welcome for now, or ProfileList if we can.
        
        from sightssh.ui.profile_list import ProfileListPanel
        # Ideally check where we came from.
        # If we just saved, we probably want to see the list.
        self.GetParent().switch_to_panel(ProfileListPanel)
