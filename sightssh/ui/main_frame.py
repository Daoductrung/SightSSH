import wx
from sightssh.accessibility.speech import SpeechManager
from sightssh.core.i18n import tr
from sightssh import __version__

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title=f"SightSSH v{__version__}", size=(800, 600))
        self.speech = SpeechManager()
        self.panel = wx.Panel(self)
        
        # Sizers
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        # Menu Bar
        # Menu Bar
        menu_bar = wx.MenuBar()
        
        # Settings
        settings_menu = wx.Menu()
        settings_item = settings_menu.Append(wx.ID_PREFERENCES, tr("menu_settings"), "Configure SightSSH")
        menu_bar.Append(settings_menu, tr("menu_settings"))
        
        # Help
        help_menu = wx.Menu()
        help_item = help_menu.Append(wx.ID_HELP, tr("dlg_help_title"), "View Shortcuts")
        about_item = help_menu.Append(wx.ID_ABOUT, tr("btn_about"), "About SightSSH")
        menu_bar.Append(help_menu, tr("menu_help"))

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.on_settings, settings_item)
        self.Bind(wx.EVT_MENU, self.on_help, help_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

        self._init_ui()
        self.Centre()
        
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)
        
        # Announce title on start
        wx.CallAfter(self.speech.speak, tr("msg_welcome_speech"))

    def on_activate(self, event):
        if event.GetActive() and self.panel:
             # Fix for Alt-Tab freezing: Force Update
             try:
                 self.panel.Refresh()
                 self.panel.Update()
             except: pass
             
             # Cancel previous timer if pending
             if hasattr(self, '_activation_timer') and self._activation_timer.IsRunning():
                 self._activation_timer.Stop()

             # Restore Focus with DELAY
             target = self.panel.force_focus if hasattr(self.panel, 'force_focus') else self.panel.SetFocus
             self._activation_timer = wx.CallLater(250, target)
        event.Skip()

    
    def on_settings(self, event):
        try:
            from sightssh.ui.settings_dialog import SettingsDialog
            from sightssh.core.i18n import tr
            
            # Singleton Pattern: Create once, reuse forever.
            # This avoids crash-on-destroy issues with wxPython/Windows Accessibility.
            if not getattr(self, 'settings_dlg', None):
                self.settings_dlg = SettingsDialog(self)
            
            # Refresh values in case config changed or previous edit was cancelled
            self.settings_dlg.populate_values()
            
            res = self.settings_dlg.ShowModal()
            
            # DO NOT DESTROY DIALOG
            # Just focus back to main frame
            self.Raise()
            self.SetFocus()
            
            if res == wx.ID_OK:
                wx.MessageBox(tr("msg_settings_saved"), tr("app_title"), parent=self)
                
                # Update current panel if it supports it
                if hasattr(self.panel, 'update_settings'):
                    self.panel.update_settings()
                
        except Exception as e:
            import logging
            logging.error(f"Error opening settings: {e}", exc_info=True)
            wx.MessageBox(f"Error opening settings: {e}", "Error")

    def on_help(self, event):
        from sightssh.ui.help_dialog import HelpDialog
        dlg = HelpDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.Raise()
        self.SetFocus()

    def on_about(self, event):
        from sightssh.ui.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.Raise()
        self.SetFocus()

    def _init_ui(self):
        """Initialize the Start Screen."""
        self.show_welcome_screen()

    def show_welcome_screen(self):
        if self.panel:
            self.panel.Hide()
            self.panel.Destroy()
        
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        welcome_text = wx.StaticText(self.panel, label=tr("msg_welcome"))
        self.sizer.Add(welcome_text, 0, wx.ALL | wx.CENTER, 20)

        # Buttons
        btn_view_profiles = wx.Button(self.panel, label=tr("btn_view_profiles"))
        btn_create_profile = wx.Button(self.panel, label=f"{tr('btn_create')} (Alt+C)")
        btn_shortcuts = wx.Button(self.panel, label=tr("btn_shortcuts"))
        btn_about = wx.Button(self.panel, label=tr("btn_about"))
        btn_settings = wx.Button(self.panel, label=f"{tr('menu_settings')} (Alt+S)")
        btn_exit = wx.Button(self.panel, label=tr("btn_exit_app"))

        # Add to sizer
        for btn in [btn_view_profiles, btn_create_profile, btn_shortcuts, btn_about, btn_settings, btn_exit]:
            self.sizer.Add(btn, 0, wx.ALL | wx.EXPAND, 10)

        # Bindings
        btn_view_profiles.Bind(wx.EVT_BUTTON, self.on_view_profiles)
        btn_create_profile.Bind(wx.EVT_BUTTON, self.on_create_profile)
        btn_settings.Bind(wx.EVT_BUTTON, self.on_settings)
        btn_shortcuts.Bind(wx.EVT_BUTTON, self.on_help)
        btn_about.Bind(wx.EVT_BUTTON, self.on_about)
        btn_exit.Bind(wx.EVT_BUTTON, self.on_exit)

        # Accelerators (Hotkeys)
        # Note: Accelerators are usually frame-global, might need management if panels change.
        # Ideally we clear old ones.
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('V'), btn_view_profiles.GetId()),
            (wx.ACCEL_ALT, ord('C'), btn_create_profile.GetId()),
            (wx.ACCEL_ALT, ord('S'), btn_settings.GetId()),
            (wx.ACCEL_ALT, ord('H'), btn_shortcuts.GetId()),
            (wx.ACCEL_ALT, ord('A'), btn_about.GetId())
        ])
        self.SetAcceleratorTable(accel_tbl)
        
        btn_view_profiles.SetFocus()
        self.panel.Layout()
        self.speech.speak(tr("msg_welcome_speech"))

    def on_view_profiles(self, event):
        from sightssh.ui.profile_list import ProfileListPanel
        self.switch_to_panel(ProfileListPanel)

    def on_create_profile(self, event):
        from sightssh.ui.profile_editor import ProfileEditorPanel
        self.switch_to_panel(ProfileEditorPanel)

    def on_exit(self, event):
        # Clean up settings dialog
        dlg = getattr(self, 'settings_dlg', None)
        if dlg:
            dlg.Destroy()
            
        # Attempt graceful close
        self.Close()
        
        # Force kill after short delay if threads hang
        import os
        os._exit(0)

    def switch_to_panel(self, panel_class, **kwargs):
        """Switches the content of the main frame to a new panel."""
        self.panel.DestroyChildren()
        self.panel.SetSizer(None)
        
        self.panel.Hide()
        self.panel.Destroy()
        
        self.panel = panel_class(self, **kwargs)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        # We rely on the panel setting its own sizer or just filling the frame.
        # Because we destroyed the old self.panel, and assigned a new one, 
        # we need to make sure the FRAME sizer (if any) knows about it, or the frame itself manages size.
        # Actually MainFrame is a Frame. We should probably use SetSizer on the FRAME containing the panel?
        # Or just rely on default Frame behavior (one child = fill).
        
        self.panel.Show()
        self.Layout()
        self.panel.SetFocus()

    def start_session(self, connection_details):
        # Start a fresh session
        if hasattr(self, 'active_client') and self.active_client:
            self.active_client.disconnect()
        self.active_client = None # Will be set by TerminalPanel on connect
        
        from sightssh.ui.terminal import TerminalPanel
        self.switch_to_panel(TerminalPanel, connection_details=connection_details)

    def switch_to_sftp(self, client, details):
        from sightssh.ui.sftp import SFTPPanel
        self.switch_to_panel(SFTPPanel, ssh_client=client, connection_details=details)

    def switch_to_terminal(self, client, details):
        from sightssh.ui.terminal import TerminalPanel
        self.switch_to_panel(TerminalPanel, connection_details=details, existing_client=client)

    def on_connection_error(self, connection_details):
        profile_name = connection_details.get('name')
        if profile_name:
             from sightssh.ui.profile_editor import ProfileEditorPanel
             self.switch_to_panel(ProfileEditorPanel, profile_name=profile_name, existing_data=connection_details, profile_password=None) 
        else:
             wx.MessageBox("Unknown profile error.", "Error")
             self.show_welcome_screen()
