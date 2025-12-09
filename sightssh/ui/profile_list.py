import wx
from sightssh.core.config_manager import ConfigManager
from sightssh.ui.dialogs import PasswordDialog
from sightssh.accessibility.speech import SpeechManager
from sightssh.core.i18n import tr

class ProfileListPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.config = ConfigManager()
        self.speech = SpeechManager()
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.SetSizer(self.sizer)

        label = wx.StaticText(self, label=tr("lbl_select_profile"))
        self.sizer.Add(label, 0, wx.ALL, 10)

        # Profile List
        self.profiles = self.config.get_profiles()
        self.profile_names = list(self.profiles.keys())
        self.list_box = wx.ListBox(self, choices=self.profile_names)
        self.sizer.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_connect = wx.Button(self, label=tr("btn_connect_enter"))
        self.btn_edit = wx.Button(self, label=tr("btn_edit"))
        self.btn_delete = wx.Button(self, label=tr("btn_delete"))
        self.btn_back = wx.Button(self, label=tr("btn_back_esc"))

        btn_sizer.Add(self.btn_connect, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_edit, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_delete, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_back, 0, wx.RIGHT, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)

        # Bindings
        self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self.on_connect)
        # Handle Enter key specifically in ListBox to connect
        self.list_box.Bind(wx.EVT_KEY_DOWN, self.on_list_key)
        
        self.btn_connect.Bind(wx.EVT_BUTTON, self.on_connect)
        self.btn_edit.Bind(wx.EVT_BUTTON, self.on_edit)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete)
        self.btn_back.Bind(wx.EVT_BUTTON, self.on_back)

        # Hotkeys
        # REMOVED global Enter accelerator to allow buttons to handle Enter naturally
        accel = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_ESCAPE, self.btn_back.GetId())
        ])
        self.SetAcceleratorTable(accel)
        
        if self.profile_names:
            self.list_box.SetSelection(0)
            self.list_box.SetFocus()

    def on_list_key(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.on_connect(None)
        else:
            event.Skip()

    def get_selected_profile(self):
        sel = self.list_box.GetSelection()
        if sel != wx.NOT_FOUND:
            return self.profile_names[sel]
        return None

    def prompt_profile_password(self, profile_name):
        """Returns True if password correct or (future) no password needed."""
        # Try unlocking with default key first (Unprotected)
        default_key = "UNPROTECTED_SIGHTSSH_DEFAULT_KEY"
        if self.config.verify_profile_password(profile_name, default_key):
            self.speech.speak(tr("msg_profile_unlocked"))
            return default_key

        dlg = PasswordDialog(self, title=f"Unlock {profile_name}", message=f"Enter password for profile '{profile_name}':")
        if dlg.ShowModal() == wx.ID_OK:
            pwd = dlg.get_password()
            dlg.Destroy()
            
            if self.config.verify_profile_password(profile_name, pwd):
                self.speech.speak("Password correct.")
                return pwd
            else:
                self.speech.speak("Incorrect password.")
                wx.MessageBox("Incorrect password", "Error")
                return None
        dlg.Destroy()
        return None

    def on_connect(self, event):
        name = self.get_selected_profile()
        if not name:
            self.speech.speak("No profile selected.")
            return

        self.speech.speak(tr("msg_verifying"))
        pwd = self.prompt_profile_password(name)
        if pwd:
            try:
                # Decrypt details
                details = self.config.get_profile_details(name, pwd)
                details['name'] = name # Inject name for error handling
                self.speech.speak(tr("msg_connecting_to").format(name=name))
                
                # Delegate connection to MainFrame
                if hasattr(self.GetParent(), 'start_session'):
                    self.GetParent().start_session(details)
                else:
                    wx.MessageBox("Connection logic implementation pending.", "Info")

            except Exception as e:
                 wx.MessageBox(f"Failed to load profile: {e}", "Error")

    def on_edit(self, event):
        name = self.get_selected_profile()
        if not name:
            return
            
        pwd = self.prompt_profile_password(name)
        if pwd:
             # Load details to pass to editor
             details = self.config.get_profile_details(name, pwd)
             from sightssh.ui.profile_editor import ProfileEditorPanel
             self.GetParent().switch_to_panel(ProfileEditorPanel, profile_name=name, existing_data=details, profile_password=pwd)

    def on_delete(self, event):
        name = self.get_selected_profile()
        if not name:
            return
            
        pwd = self.prompt_profile_password(name)
        if pwd:
            confirm = wx.MessageBox(f"Are you sure you want to delete '{name}'?", "Confirm", wx.YES_NO | wx.ICON_WARNING)
            if confirm == wx.YES:
                self.config.delete_profile(name)
                # Refresh list
                self.profiles = self.config.get_profiles()
                self.profile_names = list(self.profiles.keys())
                self.list_box.Set(self.profile_names)
                if self.profile_names:
                    self.list_box.SetSelection(0)
                self.speech.speak("Profile deleted.")

    def on_back(self, event):
        # Go back to Welcome Screen
        # MainFrame has show_welcome_screen
        self.GetParent().show_welcome_screen()
