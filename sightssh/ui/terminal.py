import wx
import os
import threading
import datetime
import re
from sightssh.core.ssh_client import SightSSHClient
from sightssh.accessibility.speech import SpeechManager
from sightssh.core.config_manager import ConfigManager
from sightssh.core.i18n import tr

class TerminalPanel(wx.Panel):
    def __init__(self, parent, connection_details, existing_client=None):
        super().__init__(parent)
        self.details = connection_details
        self.speech = SpeechManager()
        self.config = ConfigManager()
        self.settings = self.config.get_settings()
        self.line_buffer = ""
        
        # Logging Setup
        self.log_file = None
        if self.settings.get("logging_enabled", False):
            try:
                log_dir = self.config.get_log_dir()
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                profile_name = self.details.get("name", "unknown").replace(" ", "_")
                filename = f"session_{profile_name}_{timestamp}.log"
                filepath = os.path.join(log_dir, filename)
                self.log_file = open(filepath, "a", encoding="utf-8")
                self.log_file.write(f"--- Session Started: {timestamp} ---\n")
            except Exception as e:
                logging.error(f"Logging failed: {e}")

        if existing_client:
            self.client = existing_client
        else:
            self.client = SightSSHClient()
            
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        # Toolbar Buttons (SFTP, Disconnect)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_sftp = wx.Button(self, label=tr("btn_open_sftp"))
        self.btn_disconnect = wx.Button(self, label=tr("btn_disconnect"))
        
        # User requested: SFTP before Disconnect
        btn_sizer.Add(self.btn_sftp, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_disconnect, 0, wx.RIGHT, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.btn_sftp.Bind(wx.EVT_BUTTON, self.on_sftp_click)
        self.btn_disconnect.Bind(wx.EVT_BUTTON, self.on_disconnect_click)

        # Output Area
        self.lbl_output = wx.StaticText(self, label=tr("lbl_messages"))
        self.sizer.Add(self.lbl_output, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        
        self.interaction_mode = self.settings.get("interaction_mode", "dedicated")
        
        # Force Textbox for Standard Mode
        if self.interaction_mode == "standard":
             self.output_type = "textbox"
        else:
             self.output_type = self.settings.get("output_type", "listbox")



        # Font
        face = self.settings.get("font_face", "Consolas")
        size = self.settings.get("font_size", 12)
        font = wx.Font(size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=face)
        if not font.IsOk(): font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        
        if self.output_type == "textbox":
            # Standard Mode: Editable (for SR support) but Input intercepted
            # Dedicated Mode: ReadOnly
             
            style = wx.TE_MULTILINE | wx.TE_RICH2 | wx.TE_PROCESS_ENTER
            
            # TE_PROCESS_TAB ensures Tab doesn't jump focus in Standard Mode (Shell behavior)
            # But in Dedicated mode, we want Tab to navigate between Output and Input.
            if self.interaction_mode == "standard":
                style |= wx.TE_PROCESS_TAB
            else:
                style |= wx.TE_READONLY
                
            self.output_ctrl = wx.TextCtrl(self, style=style, name=tr("lbl_messages"))
            
            if self.interaction_mode == "standard":
                self.output_ctrl.Bind(wx.EVT_CHAR, self.on_term_char)
                self.output_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_term_keydown)
                self.output_ctrl.Bind(wx.EVT_TEXT_PASTE, self.on_term_paste)
                # Block Cut (lambda not picklable usually but fine here, or define method)
                self.output_ctrl.Bind(wx.EVT_TEXT_CUT, lambda e: None) 
            else:
                self.output_ctrl.Bind(wx.EVT_CHAR, self.on_output_char)
        else:
            self.output_ctrl = wx.ListBox(self, style=wx.LB_SINGLE | wx.LB_HSCROLL, name=tr("lbl_messages"))
            self.output_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_list)
            
        self.output_ctrl.SetFont(font)
        self.sizer.Add(self.output_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        # COMMAND INPUT - Only for Dedicated Mode
        if self.interaction_mode != "standard":
            self.lbl_input = wx.StaticText(self, label=tr("lbl_command_input"))
            self.sizer.Add(self.lbl_input, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
            
            self.cmd_input = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.TE_RICH2, name=tr("lbl_command_input"))
            self.cmd_input.SetMinSize((-1, 60)) # Larger input area
            self.cmd_input.SetFont(font)
            self.sizer.Add(self.cmd_input, 0, wx.EXPAND | wx.ALL, 5)
            
            self.cmd_input.Bind(wx.EVT_KEY_DOWN, self.on_key_input)
            self.cmd_input.Bind(wx.EVT_TEXT_ENTER, self.on_enter_cmd) 
        else:
            self.cmd_input = None 
        
        # Status
        status_txt = tr("msg_connecting") if not existing_client else tr("msg_connected")
        self.status = wx.StaticText(self, label=status_txt)
        self.sizer.Add(self.status, 0, wx.EXPAND | wx.ALL, 5)

        # Connect Logic
        if existing_client and existing_client._connected:
            wx.CallAfter(self.on_connected)
        else:
            threading.Thread(target=self.do_connect, daemon=True).start()
            
        self.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.Bind(wx.EVT_SIZE, self.on_resize)

    def on_resize(self, event):
        """Handle window resize and send SIGWINCH."""
        event.Skip()
        if not self.client or not self.client._connected: return
        
        # Calculate rows/cols
        # This is an approximation. For exactness we'd need ClientSize / CharSize
        # But many terminals just send a reasonable guess or let the remote side handle flow.
        # Paramiko resize_pty takes (width=80, height=24) -> (cols, rows)
        
        # We need font metrics.
        dc = wx.ClientDC(self.output_ctrl)
        font = self.output_ctrl.GetFont()
        dc.SetFont(font)
        char_w, char_h = dc.GetTextExtent("M")
        
        if char_w > 0 and char_h > 0:
             w, h = self.output_ctrl.GetClientSize()
             cols = max(80, int(w / char_w))
             rows = max(24, int(h / char_h))
             
             # Debounce or just try fire?
             # Paramiko expects resize_pty(width=cols, height=rows)
             try:
                 # Note: paramiko invokes transport.global_request('window-change', ...)
                 # But we need to use the channel if exposed, or add wrapper in SightSSHClient
                 # self.client.resize_pty(cols, rows) -> We need to verify this method exists!
                 self.client.resize_terminal(cols, rows)
             except: pass

    def on_set_focus(self, event):
        """Explicitly set focus to the correct control when panel gets focus."""
        self.force_focus()
        event.Skip()

    def force_focus(self):
        """Forces focus to the active input element and restores visibility."""
        if self.interaction_mode == "standard" and self.output_ctrl:
            def _restore():
                try:
                    if not self.output_ctrl: return 
                    # Force repaint of the text control itself
                    self.output_ctrl.Refresh()
                    self.output_ctrl.Update()
                    self.output_ctrl.SetFocus()
                    self.output_ctrl.ShowPosition(self.output_ctrl.GetLastPosition())
                except RuntimeError:
                    pass # Control deleted
            wx.CallAfter(_restore)
        elif self.cmd_input:
            def _restore_cmd():
                try: self.cmd_input.SetFocus()
                except RuntimeError: pass
            wx.CallAfter(_restore_cmd)

    def do_connect(self):
        try:
            ka = self.settings.get("keep_alive", 30)
            timeout = self.settings.get("connection_timeout", 10)
            self.client.connect(
                host=self.details['host'],
                port=self.details['port'],
                username=self.details['username'],
                password=self.details.get('secret') if self.details['auth_type'] == 'password' else None,
                key_filename=self.details.get('key_path') if self.details['auth_type'] == 'key' else None,
                passphrase=self.details.get('secret') if self.details['auth_type'] == 'key' else None,
                keep_alive=ka,
                timeout=timeout
            )
            # Register active client with parent
            if hasattr(self.GetParent(), 'active_client'):
                self.GetParent().active_client = self.client
                
            wx.CallAfter(self.on_connected)
        except Exception as e:
            wx.CallAfter(self.on_connect_fail, str(e))

    def on_connected(self):
        self.status.SetLabel(tr("msg_connected"))
        self.speech.speak(tr("msg_term_ready"))
        
        # Standard Mode Help
        if self.settings.get("interaction_mode") == "standard":
             help_msg = tr("msg_standard_help")
             self.append_text(help_msg + "\n")
             self.speech.speak(help_msg)
             
        self.client.start_shell(on_data=self.on_rx_data)
        self.output_ctrl.SetFocus()

    def on_connect_fail(self, error_msg):
        msg = tr("err_connection_failed").format(error=error_msg)
        self.status.SetLabel(msg)
        self.speech.speak(msg)
        wx.MessageBox(msg, tr("err_title"), wx.ICON_ERROR)
        wx.CallAfter(self.GetParent().on_connection_error, self.details)

    def on_rx_data(self, data):
        # Write clean data to log if enabled
        if self.log_file:
            try:
                self.log_file.write(data)
                self.log_file.flush()
            except: pass
            
        wx.CallAfter(self.append_text, data)

    def filter_ansi(self, text):
        # ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Non-printable characters (keep newline/return/tab)
        # Using a simple exclusion: remove chars < 32 except 9, 10, 13
        # But regex is faster if compiled. For now simple char loop or regex.
        # Regex: [\x00-\x08\x0B-\x0C\x0E-\x1F]
        control_chars = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
        text = control_chars.sub('', text)
        
        return text

    def append_text(self, text):
        # Handle Bell (Standard Terminal behavior)
        if '\x07' in text:
             wx.Bell()
             text = text.replace('\x07', '')
             
        # Apply ASCII Filter if enabled
        if self.settings.get("ascii_filter", True):
            text = self.filter_ansi(text)
            
        if not text: return

        # Visual Update: TextBox updates immediately (Character/Partial support)
        if self.output_type == "textbox":
            display_text = text.replace('\r', '')
            try:
                self.output_ctrl.AppendText(display_text)
                self.output_ctrl.ShowPosition(self.output_ctrl.GetLastPosition())
            except RuntimeError:
                pass

        # Speech & ListBox Logic: Buffer until full line (To avoid spamming/fragmentation)
        self.line_buffer += text
        if '\n' in self.line_buffer:
            lines = self.line_buffer.split('\n')
            self.line_buffer = lines[-1]
            complete_lines = lines[:-1]
            
            for line in complete_lines:
                clean_line = line.replace('\r', '')
                self.speech.speak(clean_line, interrupt=False)
                
                # ListBox can only show full lines
                if self.output_type != "textbox":
                     self.output_ctrl.Append(clean_line)
                     
            # ListBox Auto Scroll
            if self.output_type != "textbox":
                 count = self.output_ctrl.GetCount()
                 if count > 0:
                     self.output_ctrl.SetSelection(count - 1)
                     self.output_ctrl.EnsureVisible(count - 1)

        # Prompt Detection (Handle "Display all... (y or n)" etc.)
        # Important for Shell Prompts without newlines
        stripped = self.line_buffer.strip()
        if stripped and (stripped.endswith(("?", ":", ">", "$", "#")) or "(y or n)" in stripped):
             # For Textbox (Standard Mode), we can speak and clear buffer to avoid duplication
             if self.output_type == "textbox":
                  self.speech.speak(stripped, interrupt=False)
                  self.line_buffer = ""
             # For ListBox, we can't clear, but we should speak. 
             # Double speaking might happen when newline finally comes, but better than silence.
             elif self.output_type != "textbox":
                  # We verify we haven't just spoken this? Hard to track.
                  # Accept minor redundancy for ListBox users.
                  self.speech.speak(stripped, interrupt=False)

    def on_key_list(self, event):
        key = event.GetKeyCode()
        modifiers = event.GetModifiers()
        if modifiers == wx.MOD_CONTROL:
            if key == ord('C'):
                self.on_copy(None)
                return
            elif key == ord('A'):
                self.on_select_all(None)
                return
        event.Skip()

    def on_key_input(self, event):
        key = event.GetKeyCode()
        mods = event.GetModifiers()
        
        # Interaction Mode Hotkeys (Standard Mode Only)
        mode = self.settings.get("interaction_mode", "dedicated")
        
        if mode == "standard":
             # Alt+Q = Disconnect
             if mods == wx.MOD_ALT and key == ord('Q'):
                 self.on_disconnect_click(None)
                 return
             # Alt+O = Open SFTP
             if mods == wx.MOD_ALT and key == ord('O'):
                 self.on_sftp_click(None)
                 return
        
        if key == wx.WXK_TAB:
             pass
        event.Skip()

    def on_term_char(self, event):
        """Standard Mode: Send char directly to server"""
        key = event.GetKeyCode()
        
        # Send everything we catch here.
        # This includes Enter (13), Backspace (8), and regular chars.
        # We do NOT call event.Skip() to prevent local text ctrl update.
        # ALLOW UNICODE: key can be > 255 (e.g. Vietnamese)
        try:
            self.client.send(chr(key).encode('utf-8'))
        except: pass

    def on_term_paste(self, event):
        """Standard Mode: Paste clipboard to server"""
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                wx.TheClipboard.GetData(data)
                text = data.GetText()
                if text:
                    # Normalize newlines to \n for consistent sending?
                    # Or keep as is? Sending raw is usually best.
                    self.client.send(text.encode('utf-8'))
            wx.TheClipboard.Close()

    def on_term_keydown(self, event):
        """Standard Mode: Handle special keys and hotkeys"""
        key = event.GetKeyCode()
        modifiers = event.GetModifiers()
        
        # Hotkeys
        if event.AltDown():
             if key == ord('Q'):
                 self.on_disconnect_click(None)
                 return
             if key == ord('O'):
                 self.on_sftp_click(None)
                 return
                 
        # Paste: Ctrl+Shift+V or Ctrl+V
        # User asked for Ctrl+Shift+V specifically, but typically Ctrl+V is comfortable?
        # Standard Terminals: Ctrl+Shift+V often.
        if (key == ord('V') and modifiers == (wx.MOD_CONTROL | wx.MOD_SHIFT)):
             self.on_term_paste(None)
             return

        # Navigation & Special Keys
        payload = None
        if key == wx.WXK_UP: payload = b'\x1b[A'
        elif key == wx.WXK_DOWN: payload = b'\x1b[B'
        elif key == wx.WXK_RIGHT: payload = b'\x1b[C'
        elif key == wx.WXK_LEFT: payload = b'\x1b[D'
        elif key == wx.WXK_HOME: payload = b'\x1b[1~'
        elif key == wx.WXK_END: payload = b'\x1b[4~'
        elif key == wx.WXK_DELETE: payload = b'\x1b[3~'
        elif key == wx.WXK_INSERT: payload = b'\x1b[2~'
        elif key == wx.WXK_PAGEUP: payload = b'\x1b[5~'
        elif key == wx.WXK_PAGEDOWN: payload = b'\x1b[6~'
        elif key == wx.WXK_TAB: payload = b'\t'
        elif key == wx.WXK_BACK: payload = b'\x08' # Explicitly consume Backspace in KeyDown
        
        if payload:
             try:
                 self.client.send(payload)
             except: pass
             # Consume event!
        else:
             # Allow printable chars to go to Char event.
             # Block Ctrl+A+Delete by ensuring Delete was consumed above.
             # What about standard Ctrl+C?
             # Ctrl+C -> KeyDown 'C' + Modifiers.
             # We should probably catch Ctrl+C here and send \x03.
             if modifiers == wx.MOD_CONTROL and key == ord('C'):
                 try: self.client.send(b'\x03')
                 except: pass
                 return

             event.Skip()

    def on_enter_cmd(self, event):
        # Handle Shift+Enter for newline in dedicated input
        if wx.GetKeyState(wx.WXK_SHIFT):
             self.cmd_input.WriteText("\n")
             return

        cmd = self.cmd_input.GetValue()
        self.cmd_input.Clear()
        if cmd:
            # If command has newlines, they are sent as is.
            # We append one final newline to execute.
            self.client.send(cmd.encode('utf-8') + b'\n')

    def on_output_char(self, event):
        """Forwards typing in read-only output to command input."""
        key_code = event.GetKeyCode()
        uni_key = event.GetUnicodeKey()
        
        # Ignore modifiers alone or Shortcuts (Ctrl+C, etc)
        if event.CmdDown() or event.AltDown() or key_code == wx.WXK_NONE:
            event.Skip()
            return
            
        # Only forward printable characters (and Backspace)
        # GetUnicodeKey returns WXK_NONE (0) for special keys (Arrows, F1-12, Home/End...)
        
        should_forward = False
        char_to_append = ""
        is_backspace = False
        
        if key_code == wx.WXK_BACK:
             should_forward = True
             is_backspace = True
        elif uni_key != wx.WXK_NONE: 
             # It is a true character (ASCII or Unicode)
             # Filter out control codes < 32 (like Enter=13, Esc=27) if they end up here?
             # Usually Char event handles them. We might want to pass Enter?
             # If user presses Enter in Output, they might expect command execution?
             # But Enter is key_code 13.
             if uni_key >= 32:
                 should_forward = True
                 char_to_append = chr(uni_key)
             
        if should_forward:
             self.cmd_input.SetFocus()
             self.cmd_input.SetInsertionPointEnd()
             
             if is_backspace:
                 val = self.cmd_input.GetValue()
                 if val: 
                     self.cmd_input.SetValue(val[:-1])
                     self.cmd_input.SetInsertionPointEnd()
             elif char_to_append:
                 self.cmd_input.AppendText(char_to_append)
                 self.cmd_input.SetInsertionPointEnd()
        else:
             # It is a special key (Arrow, PageUp, etc) or unhandled control char
             # Allow default behavior (Navigation/Scrolling)
             event.Skip()

    def on_copy(self, event):
        if self.output_type == "textbox":
            # TextCtrl handles copy natively usually, but if called explicitly:
            self.output_ctrl.Copy()
            self.speech.speak(tr("msg_copied"))
            return

        sel = self.output_ctrl.GetSelection()
        if sel != wx.NOT_FOUND:
            text = self.output_ctrl.GetString(sel)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(text))
                wx.TheClipboard.Close()
                self.speech.speak(tr("msg_copied"))

    def on_select_all(self, event):
        if self.output_type == "textbox":
            # Emulate "Copy All" behavior of ListBox implementation
            text = self.output_ctrl.GetValue()
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(text))
                wx.TheClipboard.Close()
                self.speech.speak(tr("msg_copied_all"))
            return

        count = self.output_ctrl.GetCount()
        full_text = []
        for i in range(count):
            full_text.append(self.output_ctrl.GetString(i))
        all_content = "\n".join(full_text)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(all_content))
            wx.TheClipboard.Close()
            self.speech.speak(tr("msg_copied_all"))

    def on_disconnect_click(self, event):
        # Helper to check setting
        if self.settings.get("confirm_disconnect", False):
            if wx.MessageBox(tr("msg_confirm_disconnect"), tr("app_title"), wx.YES_NO | wx.ICON_QUESTION) != wx.YES:
                return

        if self.log_file:
            try:
                self.log_file.write("\n--- Session Disconnected ---\n")
                self.log_file.close()
                self.log_file = None
            except: pass
            
        self.client.disconnect()
        self.speech.speak(tr("msg_disconnected"))
        self.GetParent().show_welcome_screen()

    def on_sftp_click(self, event):
        # We don't close log here, as we might return.
        # But if SFTP uses same connection, we should be fine?
        # Actually SFTP opens new channel, but it's same session.
        self.GetParent().switch_to_sftp(self.client, self.details)

    def cleanup(self):
         if self.log_file:
            try:
                self.log_file.close()
            except: pass
