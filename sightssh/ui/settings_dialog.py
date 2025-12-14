import wx
import os
from sightssh.core.i18n import tr
from sightssh.core.config_manager import ConfigManager

class SettingsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=tr("dlg_settings_title"), size=(500, 600))
        self.config = ConfigManager()
        self.settings = self.config.get_settings()
        
        # Main Sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Notebook
        self.notebook = wx.Notebook(self)
        
        self.tab_general = wx.Panel(self.notebook)
        self.tab_terminal = wx.Panel(self.notebook)
        self.tab_accessibility = wx.Panel(self.notebook)
        
        self.setup_general_tab()
        self.setup_terminal_tab()
        self.setup_accessibility_tab()
        
        self.notebook.AddPage(self.tab_general, tr("tab_general"))
        self.notebook.AddPage(self.tab_terminal, tr("tab_terminal"))
        self.notebook.AddPage(self.tab_accessibility, tr("tab_accessibility"))
        
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_save = wx.Button(self, label=tr("btn_save"))
        self.btn_cancel = wx.Button(self, label=tr("btn_cancel"))
        
        btn_sizer.Add(self.btn_save, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.btn_cancel, 0)
        
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        
        # Bindings
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        
        self.CenterOnParent()
        
        # Initial Population
        self.populate_values()
        
        # Set focus to first meaningful element
        self.cmb_language.SetFocus()

    def populate_values(self):
        """Refreshes the UI with current settings from config."""
        self.settings = self.config.get_settings()
        
        # General
        current_lang = self.settings.get("language", "en")
        self.cmb_language.SetSelection(1 if current_lang == "vi" else 0)
        self.chk_hidden.SetValue(self.settings.get("show_hidden", True))
        self.chk_confirm.SetValue(self.settings.get("confirm_delete", False))
        self.chk_confirm_disconnect.SetValue(self.settings.get("confirm_disconnect", False))
        self.chk_restore_path.SetValue(self.settings.get("restore_last_path", True))
        self.chk_ascii.SetValue(self.settings.get("ascii_filter", True))
        
        # Terminal
        self.chk_keep_alive.SetValue(self.settings.get("keep_alive", 30) > 0)
        self.spin_keep_alive.SetValue(self.settings.get("keep_alive", 30))
        self.spin_timeout.SetValue(self.settings.get("connection_timeout", 10))
        self.chk_logging.SetValue(self.settings.get("logging_enabled", False))
        
        modes = ["dedicated", "standard"]
        curr_mode = self.settings.get("interaction_mode", "dedicated")
        self.cmb_mode.SetSelection(modes.index(curr_mode) if curr_mode in modes else 0)
        
        out_types = ["listbox", "textbox"]
        curr_out = self.settings.get("output_type", "listbox")
        self.cmb_output.SetSelection(out_types.index(curr_out) if curr_out in out_types else 0)
        
        # Accessibility
        notif_vals = ["silent", "beep", "voice", "both"]
        curr_notif = self.settings.get("notification_mode", "both")
        self.cmb_notif.SetSelection(notif_vals.index(curr_notif) if curr_notif in notif_vals else 3)
        
        verb_opts = ["size", "type", "modified", "permissions", "owner", "group"]
        current_verb = self.settings.get("verbosity", verb_opts)
        for opt, chk in self.chk_verbosity.items():
            chk.SetValue(opt in current_verb)
            
        # Update dependent UI states
        self.on_mode_change(None)
        self.on_toggle_keep_alive(None)

    def add_lbl(self, parent, sizer, label_key):
        """Helper to create and add a label."""
        lbl = wx.StaticText(parent, label=tr(label_key))
        lbl.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(lbl, 0, wx.TOP | wx.LEFT | wx.RIGHT, 5)
        return lbl

    def _get_help_text(self, desc_key):
        return tr(desc_key) if desc_key else ""

    def setup_general_tab(self):
        panel = self.tab_general
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Language
        # Create Label FIRST
        self.add_lbl(panel, sizer, "lbl_language")
        
        choices = ["English", "Tiếng Việt"]
        desc = self._get_help_text("desc_language")
        # Name includes description for backup
        acc_name = f"{tr('lbl_language')}. {desc}"
        
        self.cmb_language = wx.Choice(panel, choices=choices, name=acc_name)
        current_lang = self.settings.get("language", "en")
        self.cmb_language.SetSelection(1 if current_lang == "vi" else 0)
        self.cmb_language.SetToolTip(desc)
        
        sizer.Add(self.cmb_language, 0, wx.EXPAND | wx.ALL, 10)
        
        # Show Hidden
        # Checkbox handles its own label
        label_text = f"{tr('lbl_show_hidden')}. {tr('desc_show_hidden')}"
        self.chk_hidden = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_hidden.SetValue(self.settings.get("show_hidden", True))
        self.chk_hidden.SetToolTip(tr("desc_show_hidden"))
        sizer.Add(self.chk_hidden, 0, wx.EXPAND | wx.ALL, 10)
        
        # Confirm Delete
        label_text = f"{tr('lbl_confirm_delete')}. {tr('desc_confirm_delete')}"
        self.chk_confirm = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_confirm.SetValue(self.settings.get("confirm_delete", False))
        self.chk_confirm.SetValue(self.settings.get("confirm_delete", False))
        self.chk_confirm.SetToolTip(tr("desc_confirm_delete"))
        sizer.Add(self.chk_confirm, 0, wx.EXPAND | wx.ALL, 10)

        # Confirm Disconnect
        label_text = f"{tr('lbl_confirm_disconnect')}. {tr('desc_confirm_disconnect')}"
        self.chk_confirm_disconnect = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_confirm_disconnect.SetValue(self.settings.get("confirm_disconnect", False))
        self.chk_confirm_disconnect.SetToolTip(tr("desc_confirm_disconnect"))
        sizer.Add(self.chk_confirm_disconnect, 0, wx.EXPAND | wx.ALL, 10)

        # Restore Last Path
        label_text = f"{tr('lbl_restore_path')}. {tr('desc_restore_path')}"
        self.chk_restore_path = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_restore_path.SetValue(self.settings.get("restore_last_path", True))
        self.chk_restore_path.SetToolTip(tr("desc_restore_path"))
        sizer.Add(self.chk_restore_path, 0, wx.EXPAND | wx.ALL, 10)
        
        # ASCII Filter
        label_text = f"{tr('lbl_ascii_filter')}. {tr('desc_ascii_filter')}"
        self.chk_ascii = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_ascii.SetValue(self.settings.get("ascii_filter", True))
        self.chk_ascii.SetToolTip(tr("desc_ascii_filter"))
        sizer.Add(self.chk_ascii, 0, wx.EXPAND | wx.ALL, 10)
        

        
        # Check Updates
        label_text = f"{tr('lbl_check_updates')}. {tr('desc_check_updates')}"
        self.chk_updates = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_updates.SetValue(self.settings.get("check_updates_on_startup", True))
        self.chk_updates.SetToolTip(tr("desc_check_updates"))
        sizer.Add(self.chk_updates, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)

    def setup_terminal_tab(self):
        panel = self.tab_terminal
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Font (Grouped)
        sb_font = wx.StaticBox(panel, label=tr("lbl_font"))
        font_sizer = wx.StaticBoxSizer(sb_font, wx.VERTICAL)
        
        self.picker_font = wx.FontPickerCtrl(panel, style=wx.FNTP_FONTDESC_AS_LABEL | wx.FNTP_USEFONT_FOR_LABEL, name=tr("lbl_font"))
        
        # Load current font
        curr_face = self.settings.get("font_face", "Consolas")
        curr_size = self.settings.get("font_size", 12)
        font = wx.Font(curr_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=curr_face)
        if not font.IsOk():
            font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            
        self.picker_font.SetSelectedFont(font)
        self.picker_font.SetToolTip(tr("desc_font"))
        
        font_sizer.Add(self.picker_font, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(font_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Keep Alive
        ka_text = tr("lbl_keep_alive")
        ka_desc = tr("desc_keep_alive")
        full_ka = f"{ka_text}. {ka_desc}"
        
        # Sizer for row
        ka_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.chk_keep_alive = wx.CheckBox(panel, label=full_ka, name=full_ka)
        self.chk_keep_alive.SetValue(self.settings.get("keep_alive", 30) > 0)
        self.chk_keep_alive.Bind(wx.EVT_CHECKBOX, self.on_toggle_keep_alive)
        self.chk_keep_alive.SetToolTip(ka_desc)
        
        self.spin_keep_alive = wx.SpinCtrl(panel, min=0, max=3600, initial=self.settings.get("keep_alive", 30), name=full_ka)
        self.spin_keep_alive.SetToolTip(ka_desc)
        
        ka_sizer.Add(self.chk_keep_alive, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        ka_sizer.Add(self.spin_keep_alive, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(ka_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Timeout
        tm_text = tr("lbl_timeout")
        tm_desc = tr("desc_timeout")
        full_tm = f"{tm_text}. {tm_desc}"
        
        tm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        lbl_tm = wx.StaticText(panel, label=tm_text)
        lbl_tm.SetToolTip(tm_desc)
        
        self.spin_timeout = wx.SpinCtrl(panel, min=5, max=120, initial=self.settings.get("connection_timeout", 10), name=full_tm)
        self.spin_timeout.SetToolTip(tm_desc)
        
        tm_sizer.Add(lbl_tm, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        tm_sizer.Add(self.spin_timeout, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(tm_sizer, 0, wx.EXPAND | wx.ALL, 10)
        

        # Logging
        # Checkbox handles its own label
        log_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label_text = f"{tr('lbl_logging')}. {tr('desc_logging')}"
        self.chk_logging = wx.CheckBox(panel, label=label_text, name=label_text)
        self.chk_logging.SetValue(self.settings.get("logging_enabled", False))
        self.chk_logging.SetToolTip(tr("desc_logging"))
        
        log_sizer.Add(self.chk_logging, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self.btn_open_logs = wx.Button(panel, label=tr("btn_open_logs"))
        self.btn_clear_logs = wx.Button(panel, label=tr("btn_clear_logs"))
        
        self.btn_open_logs.Bind(wx.EVT_BUTTON, self.on_open_logs)
        self.btn_clear_logs.Bind(wx.EVT_BUTTON, self.on_clear_logs)
        
        log_sizer.Add(self.btn_open_logs, 0, wx.RIGHT, 5)
        log_sizer.Add(self.btn_clear_logs, 0)
        
        sizer.Add(log_sizer, 0, wx.EXPAND | wx.ALL, 10)

        sizer.Add(log_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Interaction Mode
        self.add_lbl(panel, sizer, "lbl_interaction_mode")
        
        modes = ["dedicated", "standard"]
        mode_labels = [tr("val_dedicated"), tr("val_standard")]
        desc = self._get_help_text("desc_interaction_mode")
        acc_name = f"{tr('lbl_interaction_mode')}. {desc}"
        
        self.cmb_mode = wx.Choice(panel, choices=mode_labels, name=acc_name)
        curr_mode = self.settings.get("interaction_mode", "dedicated")
        self.cmb_mode.SetSelection(modes.index(curr_mode) if curr_mode in modes else 0)
        self.cmb_mode.SetToolTip(desc)
        self.cmb_mode.Bind(wx.EVT_CHOICE, self.on_mode_change)
        
        sizer.Add(self.cmb_mode, 0, wx.EXPAND | wx.ALL, 10)
        
        # Output Type (Container handled manually for visibility)
        self.output_container = wx.BoxSizer(wx.VERTICAL)
        
        lbl_out = wx.StaticText(panel, label=tr("lbl_output_type"))
        lbl_out.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.output_container.Add(lbl_out, 0, wx.TOP | wx.LEFT | wx.RIGHT, 5)
        
        out_types = ["listbox", "textbox"]
        out_labels = [tr("val_listbox"), tr("val_textbox")]
        desc = self._get_help_text("desc_output_type")
        acc_name = f"{tr('lbl_output_type')}. {desc}"
        
        self.cmb_output = wx.Choice(panel, choices=out_labels, name=acc_name)
        curr_out = self.settings.get("output_type", "listbox")
        self.cmb_output.SetSelection(out_types.index(curr_out) if curr_out in out_types else 0)
        self.cmb_output.SetToolTip(desc)
        
        self.output_container.Add(self.cmb_output, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.output_container, 0, wx.EXPAND)
        
        self.on_mode_change(None)
        self.on_toggle_keep_alive(None)
        panel.SetSizer(sizer)

    def on_open_logs(self, event):
        log_dir = self.config.get_log_dir()
        if os.path.exists(log_dir):
            os.startfile(log_dir)

    def on_clear_logs(self, event):
        if wx.MessageBox(tr("msg_confirm_clear_logs"), tr("app_title"), wx.YES_NO | wx.ICON_WARNING) == wx.YES:
             log_dir = self.config.get_log_dir()
             if os.path.exists(log_dir):
                 for f in os.listdir(log_dir):
                     if f.endswith(".log"):
                         try:
                             os.remove(os.path.join(log_dir, f))
                         except: pass
                 wx.MessageBox(tr("msg_logs_cleared"), tr("app_title"))

    def on_toggle_keep_alive(self, event):
        enabled = self.chk_keep_alive.GetValue()
        self.spin_keep_alive.Enable(enabled)
        # We don't hide it, just disable.

    def on_mode_change(self, event):
        try:
            is_standard = (self.cmb_mode.GetSelection() == 1)
            # Show/Hide items manually
            show = not is_standard
            for i in range(self.output_container.GetItemCount()):
                self.output_container.GetItem(i).Show(show)
            self.tab_terminal.Layout()
        except Exception as e:
            logging.error(f"Error in on_mode_change: {e}")

    def setup_accessibility_tab(self):
        panel = self.tab_accessibility
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Notification
        self.add_lbl(panel, sizer, "lbl_notification")
        
        notif_vals = ["silent", "beep", "voice", "both"]
        notif_labels = [tr("val_silent"), tr("val_beep"), tr("val_voice"), tr("val_both")]
        desc = self._get_help_text("desc_notification")
        acc_name = f"{tr('lbl_notification')}. {desc}"
        
        self.cmb_notif = wx.Choice(panel, choices=notif_labels, name=acc_name)
        curr_notif = self.settings.get("notification_mode", "both")
        self.cmb_notif.SetSelection(notif_vals.index(curr_notif) if curr_notif in notif_vals else 3)
        self.cmb_notif.SetToolTip(desc)
        
        sizer.Add(self.cmb_notif, 0, wx.EXPAND | wx.ALL, 10)
        
        # Verbosity (Group Box)
        # We use StaticBoxSizer which provides a group context for screen readers
        sb_title = f"{tr('lbl_verbosity')}. {tr('desc_verbosity')}"
        sb = wx.StaticBox(panel, label=sb_title)
        sb_sizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        verb_opts = ["size", "type", "modified", "permissions", "owner", "group"]
        current_verb = self.settings.get("verbosity", verb_opts)
        
        self.chk_verbosity = {}
        for opt in verb_opts:
            # Checkbox label using translation
            label = tr("val_" + opt)
            chk = wx.CheckBox(panel, label=label, name=label)
            chk.SetValue(opt in current_verb)
            self.chk_verbosity[opt] = chk # Store for saving
            sb_sizer.Add(chk, 0, wx.LEFT | wx.BOTTOM, 5)
            
        sizer.Add(sb_sizer, 0, wx.ALL | wx.EXPAND, 10)
        
        panel.SetSizer(sizer)

    def on_save(self, event):
        try:
            # Gather data
            new_settings = self.settings.copy()
            
            # General
            new_settings["language"] = "vi" if self.cmb_language.GetSelection() == 1 else "en"
            new_settings["show_hidden"] = self.chk_hidden.GetValue()
            new_settings["confirm_delete"] = self.chk_confirm.GetValue()
            new_settings["confirm_disconnect"] = self.chk_confirm_disconnect.GetValue()
            new_settings["restore_last_path"] = self.chk_restore_path.GetValue()
            new_settings["ascii_filter"] = self.chk_ascii.GetValue()
            new_settings["check_updates_on_startup"] = self.chk_updates.GetValue()
            
            # Terminal
            ka_val = self.spin_keep_alive.GetValue() if self.chk_keep_alive.GetValue() else 0
            new_settings["keep_alive"] = ka_val
            new_settings["connection_timeout"] = self.spin_timeout.GetValue()
            new_settings["logging_enabled"] = self.chk_logging.GetValue()
            new_settings["interaction_mode"] = "standard" if self.cmb_mode.GetSelection() == 1 else "dedicated"
            new_settings["output_type"] = "textbox" if self.cmb_output.GetSelection() == 1 else "listbox"
            
            # Accessibility
            notif_vals = ["silent", "beep", "voice", "both"]
            new_settings["notification_mode"] = notif_vals[self.cmb_notif.GetSelection()]
            
            verb_list = []
            for opt, chk in self.chk_verbosity.items():
                if chk.GetValue():
                    verb_list.append(opt)
            new_settings["verbosity"] = verb_list

            # Font
            font = self.picker_font.GetSelectedFont()
            if font.IsOk():
                new_settings["font_face"] = font.GetFaceName()
                new_settings["font_size"] = font.GetPointSize()

            
            # Save
            self.config.save_settings(new_settings)
            
            self.EndModal(wx.ID_OK)
            
        except Exception as e:
            wx.MessageBox(tr("err_save_settings").format(error=e), tr("app_title"), wx.ICON_ERROR)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
