import wx
import os
import threading
import stat
import shutil
import shutil
from sightssh.accessibility.speech import SpeechManager
from sightssh.core.i18n import tr
from sightssh.ui.transfer_dialog import TransferProgressDialog
from sightssh.core.config_manager import ConfigManager
from sightssh.ui.permissions_dialog import PermissionsDialog
from sightssh.ui.conflict_dialog import ConflictDialog

class SFTPPanel(wx.Panel):
    def __init__(self, parent, ssh_client, connection_details):
        super().__init__(parent)
        self.ssh_client = ssh_client
        self.details = connection_details
        self.speech = SpeechManager()
        self.config = ConfigManager()
        self.settings = self.config.get_settings()
        self.sftp = None
        self.transfer_dlg = None
        self.local_path = os.path.expanduser("~")
        self.remote_path = "."
        
        # Restore Paths
        if self.settings.get("restore_last_path", True):
             last_local = self.details.get("last_local_path")
             last_remote = self.details.get("last_remote_path")
             
             if last_local and os.path.exists(last_local):
                 self.local_path = last_local
             if last_remote:
                 self.remote_path = last_remote

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        # Toolbar
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_refresh = wx.Button(self, label=tr("btn_refresh"))
        self.btn_back_term = wx.Button(self, label=tr("btn_back_term"))
        self.btn_disconnect = wx.Button(self, label=tr("btn_disconnect"))
        
        btn_sizer.Add(self.btn_refresh, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_back_term, 0, wx.RIGHT, 5)
        btn_sizer.Add(self.btn_disconnect, 0, wx.RIGHT, 5)
        self.sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # Splitter (Dual Pane)
        self.splitter = wx.SplitterWindow(self)
        self.left_panel = wx.Panel(self.splitter)
        self.right_panel = wx.Panel(self.splitter)
        
        # Left (Local) - ListCtrl
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(wx.StaticText(self.left_panel, label=tr("lbl_local_comp")), 0, wx.ALL, 5)
        self.local_list = wx.ListCtrl(self.left_panel, style=wx.LC_REPORT)
        left_sizer.Add(self.local_list, 1, wx.EXPAND)
        self.left_panel.SetSizer(left_sizer)

        # Right (Remote) - ListCtrl
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer.Add(wx.StaticText(self.right_panel, label=tr("lbl_remote_server")), 0, wx.ALL, 5)
        self.remote_list = wx.ListCtrl(self.right_panel, style=wx.LC_REPORT)
        right_sizer.Add(self.remote_list, 1, wx.EXPAND)
        self.right_panel.SetSizer(right_sizer)

        self.splitter.SplitVertically(self.left_panel, self.right_panel)
        self.splitter.SetSashGravity(0.5)
        self.sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)

        # Init Columns
        self.update_columns()


        # Events
        self.btn_back_term.Bind(wx.EVT_BUTTON, self.on_back_term)
        self.btn_refresh.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.btn_disconnect.Bind(wx.EVT_BUTTON, self.on_disconnect)
        
        # Local List Events
        self.local_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_local_enter)
        self.local_list.Bind(wx.EVT_LIST_KEY_DOWN, self.on_local_key)
        self.local_list.Bind(wx.EVT_CONTEXT_MENU, self.on_local_menu)
        self.local_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_local_select)
        self.local_list.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.on_local_focus) 
        self.local_list.Bind(wx.EVT_CHAR, self.on_list_char)

        # Remote List Events
        self.remote_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_remote_enter)
        self.remote_list.Bind(wx.EVT_LIST_KEY_DOWN, self.on_remote_key)
        self.remote_list.Bind(wx.EVT_CONTEXT_MENU, self.on_remote_menu)
        self.remote_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_remote_select)
        self.remote_list.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.on_remote_focus)
        self.remote_list.Bind(wx.EVT_CHAR, self.on_list_char)

        # Initialize
        wx.CallAfter(self.init_sftp)
        
        # Context Menu IDs
        self.ID_UPLOAD = wx.NewIdRef()
        self.ID_OPEN = wx.NewIdRef()
        self.ID_L_DELETE = wx.NewIdRef()
        self.ID_L_RENAME = wx.NewIdRef()
        self.ID_L_MKDIR = wx.NewIdRef()
        
        self.ID_DOWNLOAD = wx.NewIdRef()
        self.ID_R_DELETE = wx.NewIdRef()
        self.ID_R_RENAME = wx.NewIdRef()
        self.ID_R_MKDIR = wx.NewIdRef()
        self.ID_PERMS = wx.NewIdRef()
        
        # Bind Context Menus ONCE
        self.Bind(wx.EVT_MENU, self.do_upload, id=self.ID_UPLOAD)
        self.Bind(wx.EVT_MENU, lambda e: self.on_local_enter(type('obj', (object,), {'GetIndex': lambda: self.local_list.GetFirstSelected()})()), id=self.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.do_local_delete, id=self.ID_L_DELETE)
        self.Bind(wx.EVT_MENU, self.do_local_rename, id=self.ID_L_RENAME)
        self.Bind(wx.EVT_MENU, self.do_local_mkdir, id=self.ID_L_MKDIR)
        
        self.Bind(wx.EVT_MENU, self.do_download, id=self.ID_DOWNLOAD)
        self.Bind(wx.EVT_MENU, self.do_remote_delete, id=self.ID_R_DELETE)
        self.Bind(wx.EVT_MENU, self.do_remote_rename, id=self.ID_R_RENAME)
        self.Bind(wx.EVT_MENU, self.do_remote_mkdir, id=self.ID_R_MKDIR)
        self.Bind(wx.EVT_MENU, self.do_remote_permissions, id=self.ID_PERMS)

    def init_sftp(self):
        try:
            self.sftp = self.ssh_client.open_sftp()
            if not self.sftp: raise Exception(tr("err_sftp_failed"))
            try:
                # Try to Restore, else default to .
                self.sftp.chdir(self.remote_path)
                self.remote_path = self.sftp.getcwd()
            except: 
                # Fallback
                self.sftp.chdir('.')
                self.remote_path = self.sftp.getcwd()
            
            self.refresh_lists()
            self.local_list.SetFocus()
            self.speech.speak(tr("msg_sftp_ready_speech"))
        except Exception as e:
            wx.MessageBox(tr("err_sftp_gen_error").format(error=e), tr("err_title"))
            self.on_back_term(None)

    def refresh_lists(self):
        # Reload settings on refresh to catch any changes
        self.settings = self.config.get_settings()
        self.update_columns() # Update column visibility
        self.refresh_local()
        self.refresh_remote()
        
    def update_columns(self):
        """Rebuilds ListCtrl columns based on verbosity settings."""
        verbosity = self.settings.get("verbosity", [])
        if not verbosity: verbosity = []
        
        # Local
        self.local_list.DeleteAllColumns()
        self.local_list.InsertColumn(0, tr("lbl_name"), width=150)
        self.local_indices = [] # Stores which data index goes to which column (starting from col 1)
        
        # Local Map: (key, label, data_index)
        # Data Indicies: 0=Name, 1=Size, 2=Type, 3=Modified
        local_defs = [("size", "lbl_size", 1), ("type", "lbl_type", 2), ("modified", "lbl_modified", 3)]
        
        col_idx = 1
        for key, lbl, dat_idx in local_defs:
            if key in verbosity:
                self.local_list.InsertColumn(col_idx, tr(lbl), width=100)
                self.local_indices.append(dat_idx)
                col_idx += 1
                
        # Remote
        self.remote_list.DeleteAllColumns()
        self.remote_list.InsertColumn(0, tr("lbl_name"), width=150)
        self.remote_indices = []
        
        # Remote Data Indices: 0=Name, 1=Size, 2=Type, 3=Modified, 4=Perms, 5=Owner, 6=Group
        remote_defs = [
            ("size", "lbl_size", 1), 
            ("type", "lbl_type", 2), 
            ("modified", "lbl_modified", 3),
            ("permissions", "lbl_permissions", 100),
            ("owner", "lbl_owner", 5),
            ("group", "lbl_group", 6)
        ]
        
        col_idx = 1
        for key, lbl, dat_idx in remote_defs:
            if key in verbosity:
                # Special handling if needed? No.
                self.remote_list.InsertColumn(col_idx, tr(lbl), width=100)
                self.remote_indices.append(dat_idx)
                col_idx += 1

    def _populate_list(self, ctrl, items, indices):
        # items is list of tuples: (name, size, type, modified, [perms, owner, group])
        # indices is list of data_indices to map to columns 1, 2, 3...
        ctrl.DeleteAllItems()
        for i, data in enumerate(items):
            # First item is Name (always index 0)
            list_idx = ctrl.InsertItem(i, data[0])
            
            # Set other columns based on indices
            for col_pos, data_pos in enumerate(indices, 1):
                if data_pos < len(data):
                    ctrl.SetItem(list_idx, col_pos, str(data[data_pos]))
                    
        if ctrl.GetItemCount() > 0:
            ctrl.SetItemState(0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED, 
                              wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
            ctrl.EnsureVisible(0)

    def _format_size(self, size):
        if size == 0: return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size, 1024)))
        p = math.pow(1024, i)
        s = round(size / p, 2)
        return "%s %s" % (s, size_name[i])

    def _format_time(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')

    def _format_perms(self, mode):
        return stat.filemode(mode)

    def refresh_local(self):
        try:
            show_hidden = self.settings.get("show_hidden", True)
            items = os.listdir(self.local_path)
            
            data_list = []
            
            # Add Parent Dir first
            data_list.append(("[..]", "", "DIR", ""))

            # Separate dirs and files
            dirs = []
            files = []

            for name in items:
                if not show_hidden and name.startswith(".") and name not in [".", ".."]: continue
                
                full_path = os.path.join(self.local_path, name)
                try:
                    stats = os.stat(full_path)
                    sz = self._format_size(stats.st_size)
                    tm = self._format_time(stats.st_mtime)
                    
                    if os.path.isdir(full_path):
                        dirs.append((f"[{name}]", "", "DIR", tm))
                    else:
                        files.append((name, sz, "FILE", tm))
                except:
                     files.append((name, "", "", ""))
            
            # Sort by name
            dirs.sort(key=lambda x: x[0])
            files.sort(key=lambda x: x[0])
            
            self._populate_list(self.local_list, data_list + dirs + files, self.local_indices)
        except Exception as e:
            self.speech.speak(tr("err_local").format(error=e))

    def refresh_remote(self):
        try:
            if not self.sftp: return
            show_hidden = self.settings.get("show_hidden", True)
            attrs = self.sftp.listdir_attr(self.remote_path)
            
            data_list = []
            data_list.append(("[..]", "", "DIR", "", "", "", ""))
            
            dirs = []
            files = []
            
            for attr in attrs:
                name = attr.filename
                if name in ('.', '..'): continue
                if not show_hidden and name.startswith('.'): continue
                
                sz = self._format_size(attr.st_size)
                tm = self._format_time(attr.st_mtime)
                perms = self._format_perms(attr.st_mode)
                
                # Default to ID
                uid = str(attr.st_uid)
                gid = str(attr.st_gid)
                
                # Try to parse longname for Owner/Group
                # Format: -rw-r--r-- 1 owner group size ...
                if attr.longname:
                    try:
                        parts = attr.longname.split()
                        # parts[0]=perms, parts[1]=links, parts[2]=owner, parts[3]=group
                        if len(parts) > 3:
                            uid = parts[2]
                            gid = parts[3]
                    except: pass
                
                if stat.S_ISDIR(attr.st_mode):
                    dirs.append((f"[{name}]", "", "DIR", tm, perms, uid, gid))
                else:
                    files.append((name, sz, "FILE", tm, perms, uid, gid))
            
            dirs.sort(key=lambda x: x[0])
            files.sort(key=lambda x: x[0])
            
            self._populate_list(self.remote_list, data_list + dirs + files, self.remote_indices)
        except Exception as e:
            self.speech.speak(tr("err_remote").format(error=e))

    def play_beep(self, pitch="start"):
        import winsound
        try:
            if pitch == "start": winsound.Beep(400, 200)
            elif pitch == "end": winsound.Beep(800, 200)
            elif pitch == "error": winsound.Beep(200, 500)
        except: pass

    def on_list_char(self, event):
        key = event.GetKeyCode()
        if key < 32 or key > 126:
            event.Skip()
            return
            
        char = chr(key).lower()
        obj = event.GetEventObject()
        
        count = obj.GetItemCount()
        start = -1
        idx = obj.GetFirstSelected()
        if idx != -1: start = idx
        
        found = -1
        
        for i in range(start + 1, count):
            text = self.strip_brackets(obj.GetItemText(i)).lower()
            if text.startswith(char):
                found = i
                break
        
        if found == -1:
             for i in range(0, start + 1):
                text = self.strip_brackets(obj.GetItemText(i)).lower()
                if text.startswith(char):
                    found = i
                    break
        
        if found != -1:
            sel = obj.GetFirstSelected()
            while sel != -1:
                obj.SetItemState(sel, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
                sel = obj.GetNextSelected(sel)
            
            obj.SetItemState(found, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED, 
                              wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
            obj.EnsureVisible(found)

    def update_settings(self):
        """Called by MainFrame when settings are changed."""
        self.settings = self.config.get_settings()
        self.refresh_lists()

    # EVENTS AND AUDIO
    def _read_item(self, ctrl, event, is_remote=False):
        idx = event.GetIndex()
        # Name always read (Column 0)
        text = self.strip_brackets(ctrl.GetItemText(idx))
        
        verbosity = self.settings.get("verbosity", [])
        if not verbosity: verbosity = []
        
        speech_parts = [text]
        col_idx = 1 # Start checking from column 1
        
        # Must match exact order in update_columns
        if not is_remote:
             # Local: size, type, modified
             defs = ["size", "type", "modified"]
        else:
             # Remote: size, type, modified, permissions, owner, group
             defs = ["size", "type", "modified", "permissions", "owner", "group"]
             
        for key in defs:
             if key in verbosity:
                 # Because we rebuild columns in this exact order, 
                 # the visual column index increments sequentially.
                 val = ctrl.GetItemText(idx, col_idx)
                 if val: speech_parts.append(val)
                 col_idx += 1
                 
        self.speech.speak(", ".join(speech_parts))

    def on_local_focus(self, event):
        self._read_item(self.local_list, event, is_remote=False)
        
    def on_remote_focus(self, event):
        self._read_item(self.remote_list, event, is_remote=True)

    def on_local_select(self, event):
        if wx.GetKeyState(wx.WXK_CONTROL):
             item = event.GetItem()
             text = self.strip_brackets(item.GetText())
             self.speech.speak(tr("msg_selected").format(text=text))
        elif wx.GetKeyState(wx.WXK_SHIFT):
             self.speech.speak(tr("msg_selection_extended"))

    def on_remote_select(self, event):
        if wx.GetKeyState(wx.WXK_CONTROL):
             item = event.GetItem()
             text = self.strip_brackets(item.GetText())
             self.speech.speak(tr("msg_selected").format(text=text))
        elif wx.GetKeyState(wx.WXK_SHIFT):
             self.speech.speak(tr("msg_selection_extended"))

    # TRANSFER OPERATIONS
    def do_upload(self, event):
        items = self.get_selected_items(self.local_list)
        if not items: return
        
        self.transfer_dlg = TransferProgressDialog(self, tr("msg_uploading"))
        dlg = self.transfer_dlg
        dlg.Show()
        
        def run_upload():
            last_error = None
            # Conflict state for this batch
            batch_action = None # 'overwrite', 'skip'
            
            try:
                self.play_beep("start")
                count = 0
                
                # Helper for recursion
                def _r_upload(local_dir, remote_dir):
                    nonlocal batch_action, count
                    try: 
                        self.sftp.stat(remote_dir)
                    except:
                        self.sftp.mkdir(remote_dir)
                        
                    for name in os.listdir(local_dir):
                        if dlg.is_cancelled: raise Exception(tr("err_cancelled"))
                        l_path = os.path.join(local_dir, name)
                        r_path = remote_dir + "/" + name
                        
                        if os.path.isdir(l_path):
                            _r_upload(l_path, r_path)
                        else:
                            # Check conflict
                            action = "overwrite"
                            try:
                                self.sftp.stat(r_path)
                                # Exists
                                if batch_action:
                                    action = batch_action
                                else:
                                    res_act, res_all = self.resolve_conflict(name)
                                    if res_act == 'cancel': raise Exception("Cancelled")
                                    if res_all: batch_action = res_act
                                    action = res_act
                            except IOError: pass # Does not exist
                            
                            if action == 'skip': continue
                            if action == 'rename':
                                new_name = self.prompt_rename(name)
                                if not new_name: raise Exception("Cancelled")
                                r_path = remote_dir + "/" + new_name
                                
                            dlg.set_filename(name)
                            self.sftp.put(l_path, r_path, callback=progress_cb)
                            count += 1 # Internal count for recursion? Main loop counts too.
                            
                def progress_cb(cur, tot):
                    dlg.update_progress(cur, tot)
                    if dlg.is_cancelled: raise Exception("Cancelled")

                for item in items:
                    if dlg.is_cancelled: break
                    if item == "[..]": continue
                    
                    name = self.strip_brackets(item)
                    local_path = os.path.join(self.local_path, name)
                    remote_path = self.remote_path + "/" + name
                    
                    try:
                        if os.path.isdir(local_path):
                            _r_upload(local_path, remote_path)
                        else:
                            # Check conflict
                            action = "overwrite"
                            try:
                                self.sftp.stat(remote_path)
                                if batch_action:
                                    action = batch_action
                                else:
                                    res_act, res_all = self.resolve_conflict(name)
                                    if res_act == 'cancel': raise Exception("Cancelled")
                                    if res_all: batch_action = res_act
                                    action = res_act
                            except IOError: pass
                            
                            if action == 'skip': continue
                            if action == 'rename':
                                new_name = self.prompt_rename(name)
                                if not new_name: raise Exception("Cancelled")
                                remote_path = self.remote_path + "/" + new_name

                            dlg.set_filename(name)
                            self.sftp.put(local_path, remote_path, callback=progress_cb)
                            count += 1
                    except Exception as e:
                        last_error = str(e)
                        if "Cancelled" in str(e): break

                wx.CallAfter(dlg.Destroy)
                if count > 0:
                    self.play_beep("end")
                    wx.CallAfter(self.refresh_remote)
                    wx.CallAfter(self.speech.speak, tr("msg_uploaded").format(count=count))
                elif last_error:
                    wx.CallAfter(wx.MessageBox, tr("err_upload").format(error=last_error), tr("app_title"), wx.ICON_ERROR)
                else:
                    wx.CallAfter(self.speech.speak, tr("err_transfer_cancelled"))
            except Exception as e:
                wx.CallAfter(dlg.Destroy)
                wx.CallAfter(wx.MessageBox, str(e), tr("err_title"))
                
        threading.Thread(target=run_upload, daemon=True).start()

    def do_download(self, event):
        items = self.get_selected_items(self.remote_list)
        if not items: return
        
        self.transfer_dlg = TransferProgressDialog(self, tr("msg_downloading"))
        dlg = self.transfer_dlg
        dlg.Show()
        
        def run_download():
            last_error = None
            batch_action = None
            
            try:
                self.play_beep("start")
                count = 0
                
                def _r_download(remote_dir, local_dir):
                    nonlocal batch_action, count
                    if not os.path.exists(local_dir): os.makedirs(local_dir)
                    for attr in self.sftp.listdir_attr(remote_dir):
                        if dlg.is_cancelled: raise Exception("Cancelled")
                        name = attr.filename
                        if name in ('.', '..'): continue
                        
                        r_path = remote_dir + "/" + name
                        l_path = os.path.join(local_dir, name)
                        
                        if stat.S_ISDIR(attr.st_mode):
                            _r_download(r_path, l_path)
                        else:
                            # Conflict Check
                            action = "overwrite"
                            if os.path.exists(l_path):
                                if batch_action:
                                    action = batch_action
                                else:
                                    res_act, res_all = self.resolve_conflict(name)
                                    if res_act == 'cancel': raise Exception("Cancelled")
                                    if res_all: batch_action = res_act
                                    action = res_act
                            
                            if action == 'skip': continue
                            if action == 'rename':
                                new_name = self.prompt_rename(name)
                                if not new_name: raise Exception("Cancelled")
                                l_path = os.path.join(local_dir, new_name)

                            dlg.set_filename(name)
                            self.sftp.get(r_path, l_path, callback=progress_cb)
                            count += 1

                def progress_cb(cur, tot):
                     dlg.update_progress(cur, tot)
                     if dlg.is_cancelled: raise Exception("Cancelled")

                for item in items:
                    if dlg.is_cancelled: break
                    if item == "[..]": continue
                    
                    name = self.strip_brackets(item)
                    
                    remote_path = self.remote_path + "/" + name
                    local_path = os.path.join(self.local_path, name)
                    
                    try:
                        # Check if it is a directory
                        is_dir = False
                        try:
                            attr = self.sftp.stat(remote_path)
                            if stat.S_ISDIR(attr.st_mode): is_dir = True
                        except: pass
                        
                        if is_dir:
                            _r_download(remote_path, local_path)
                        else:
                            # Conflict Check
                            action = "overwrite"
                            if os.path.exists(local_path):
                                if batch_action:
                                    action = batch_action
                                else:
                                    res_act, res_all = self.resolve_conflict(name)
                                    if res_act == 'cancel': raise Exception("Cancelled")
                                    if res_all: batch_action = res_act
                                    action = res_act

                            if action == 'skip': continue
                            if action == 'rename':
                                new_name = self.prompt_rename(name)
                                if not new_name: raise Exception("Cancelled")
                                local_path = os.path.join(self.local_path, new_name)

                            dlg.set_filename(name)
                            self.sftp.get(remote_path, local_path, callback=progress_cb)
                            count += 1
                    except Exception as e:
                        last_error = str(e)
                        if "Cancelled" in str(e): break
                
                wx.CallAfter(dlg.Destroy)
                if count > 0:
                    self.play_beep("end")
                    wx.CallAfter(self.refresh_local)
                    wx.CallAfter(self.speech.speak, tr("msg_downloaded").format(count=count))
                elif last_error:
                    wx.CallAfter(wx.MessageBox, tr("err_download").format(error=last_error), tr("app_title"), wx.ICON_ERROR)
                else:
                    wx.CallAfter(self.speech.speak, tr("err_transfer_cancelled"))
            except Exception as e:
                 wx.CallAfter(dlg.Destroy)
                 wx.CallAfter(wx.MessageBox, str(e), tr("err_title"))

        threading.Thread(target=run_download, daemon=True).start()
        
    def on_local_enter(self, event):
        idx = event.GetIndex()
        item = self.local_list.GetItemText(idx)
        
        if item == "[..]":
            self.local_path = os.path.dirname(self.local_path)
            self.refresh_local()
            self.speech.speak(tr("msg_up_to").format(name=os.path.basename(self.local_path)))
        elif item.startswith("[") and item.endswith("]"):
            dirname = item[1:-1]
            self.local_path = os.path.join(self.local_path, dirname)
            self.refresh_local()
            self.speech.speak(tr("msg_entered").format(name=dirname))
        else:
            path = os.path.join(self.local_path, item)
            try:
                os.startfile(path)
                self.speech.speak(tr("msg_opening_file"))
            except Exception as e:
                wx.MessageBox(str(e), tr("err_title"))

    def on_remote_enter(self, event):
        idx = event.GetIndex()
        item = self.remote_list.GetItemText(idx)
        
        if item == "[..]":
            try:
                self.sftp.chdir("..")
                self.remote_path = self.sftp.getcwd()
                self.refresh_remote()
                self.speech.speak(tr("msg_up_dir"))
            except Exception as e:
                self.play_beep("error")
                wx.MessageBox(str(e), tr("err_title"))
        elif item.startswith("[") and item.endswith("]"):
            dirname = item[1:-1]
            try:
                self.sftp.chdir(dirname)
                self.remote_path = self.sftp.getcwd()
                self.refresh_remote()
                self.speech.speak(tr("msg_entered").format(name=dirname))
            except Exception as e:
                self.play_beep("error")
                wx.MessageBox(str(e), tr("err_title"))
        else:
            self.do_download(None)

    def on_local_key(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_BACK:
            self.local_path = os.path.dirname(self.local_path)
            self.refresh_local()
        elif key == wx.WXK_DELETE:
            self.do_local_delete(None)
        elif key == wx.WXK_F2:
            self.do_local_rename(None)
        elif key == wx.WXK_F5:
            self.on_refresh(None)
        else:
            event.Skip()

    def on_remote_key(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_BACK:
            try:
                self.sftp.chdir("..")
                self.remote_path = self.sftp.getcwd()
                self.refresh_remote()
            except: pass
        elif key == wx.WXK_DELETE:
            self.do_remote_delete(None)
        elif key == wx.WXK_F2:
            self.do_remote_rename(None)
        elif key == wx.WXK_F5:
            self.on_refresh(None)
        else:
            event.Skip()

    def get_selected_items(self, ctrl):
        items = []
        idx = ctrl.GetFirstSelected()
        while idx != -1:
            items.append(ctrl.GetItemText(idx))
            idx = ctrl.GetNextSelected(idx)
        return items

    def strip_brackets(self, name):
        if name.startswith("[") and name.endswith("]"): return name[1:-1]
        return name

    def on_local_menu(self, event):
        menu = wx.Menu()
        menu.Append(self.ID_UPLOAD, tr("ctx_upload"))
        menu.Append(self.ID_OPEN, tr("ctx_open"))
        menu.Append(self.ID_L_DELETE, tr("ctx_delete"))
        menu.Append(self.ID_L_RENAME, tr("ctx_rename"))
        menu.Append(self.ID_L_MKDIR, tr("ctx_mkdir"))
        
        self.PopupMenu(menu)

    def do_local_rename(self, event):
        items = self.get_selected_items(self.local_list)
        if not items: return
        if len(items) > 1:
            self.speech.speak(tr("msg_cannot_rename_multi"))
            wx.MessageBox(tr("msg_cannot_rename_multi"), tr("app_title"), wx.ICON_WARNING)
            return
            
        old_name = self.strip_brackets(items[0])
        
        dlg = wx.TextEntryDialog(self, tr("dlg_rename_msg"), tr("dlg_rename_title"), old_name)
        if dlg.ShowModal() == wx.ID_OK:
            new_name = dlg.GetValue()
            try:
                os.rename(os.path.join(self.local_path, old_name), os.path.join(self.local_path, new_name))
                self.refresh_local()
                self.speech.speak(tr("msg_renamed"))
            except Exception as e: wx.MessageBox(tr("err_local").format(error=e), tr("err_title"))

    def on_remote_menu(self, event):
        menu = wx.Menu()
        menu.Append(self.ID_DOWNLOAD, tr("ctx_download"))
        menu.Append(self.ID_R_DELETE, tr("ctx_delete"))
        menu.Append(self.ID_R_RENAME, tr("ctx_rename"))
        menu.Append(self.ID_R_MKDIR, tr("ctx_mkdir"))
        menu.AppendSeparator()
        menu.Append(self.ID_PERMS, tr("lbl_permissions"))
        
        self.PopupMenu(menu)

    def do_remote_permissions(self, event):
        items = self.get_selected_items(self.remote_list)
        if not items: return
        
        # Check for directories to enable recursive option
        has_dir = False
        first_mode = 0o755 # Default
        
        try:
             # Get stats for first item to populate dialog
             first_name = self.strip_brackets(items[0])
             path = self.remote_path + "/" + first_name
             attr = self.sftp.stat(path)
             first_mode = attr.st_mode
             
             # fast check if any is dir
             for item in items:
                 if item.startswith("["): 
                     has_dir = True
                     break
        except Exception as e:
            wx.MessageBox(tr("err_attr_read").format(error=e), tr("err_title"))
            return

        dlg = PermissionsDialog(self, first_mode, show_recursive=has_dir)
        if dlg.ShowModal() == wx.ID_OK:
            new_mode = dlg.GetMode()
            recursive = dlg.IsRecursive()
            
            error_msg = ""
            count = 0
            
            def _r_chmod(sftp, remote_path, mode):
                try:
                    sftp.chmod(remote_path, mode)
                    if stat.S_ISDIR(sftp.stat(remote_path).st_mode):
                         for attr in sftp.listdir_attr(remote_path):
                             name = attr.filename
                             if name in ('.', '..'): continue
                             _r_chmod(sftp, remote_path + "/" + name, mode)
                except Exception as e:
                    raise e

            # Apply Logic
            # Note: chmod takes integer mode
            for item in items:
                 name = self.strip_brackets(item)
                 path = self.remote_path + "/" + name
                 try:
                     if recursive and item.startswith("["):
                         _r_chmod(self.sftp, path, new_mode)
                     else:
                         self.sftp.chmod(path, new_mode)
                     count += 1
                 except Exception as e:
                     error_msg += f"{name}: {e}\n"
            
            if error_msg:
                wx.MessageBox(tr("err_multi_errors").format(errors=error_msg), tr("err_title"))
            
            if count > 0:
                self.speech.speak(tr("msg_perm_updated"))
                self.refresh_remote()
                
        dlg.Destroy()

    def do_remote_rename(self, event):
        items = self.get_selected_items(self.remote_list)
        if not items: return
        if len(items) > 1:
            self.speech.speak(tr("msg_cannot_rename_multi"))
            wx.MessageBox(tr("msg_cannot_rename_multi"), tr("app_title"), wx.ICON_WARNING)
            return

        old_name = self.strip_brackets(items[0])
        
        dlg = wx.TextEntryDialog(self, tr("dlg_rename_msg"), tr("dlg_rename_title"), old_name)
        if dlg.ShowModal() == wx.ID_OK:
            new_name = dlg.GetValue()
            try:
                self.sftp.rename(self.remote_path + "/" + old_name, self.remote_path + "/" + new_name)
                self.refresh_remote()
                self.speech.speak(tr("msg_renamed"))
            except Exception as e: wx.MessageBox(tr("err_remote").format(error=e), tr("err_title"))

    def do_local_delete(self, event):
        items = self.get_selected_items(self.local_list)
        if not items: return
        
        # Check setting
        confirm = self.settings.get("confirm_delete", False)
        if confirm:
            if wx.MessageBox(tr("msg_confirm_del_items").format(count=len(items)), tr("app_title"), wx.YES_NO) != wx.YES: return
            
        success_count = 0
        error_msg = ""
        
        for item in items:
            if item == "[..]": continue
            name = self.strip_brackets(item)
            path = os.path.join(self.local_path, name)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                success_count += 1
            except Exception as e:
                 error_msg += f"{name}: {str(e)}\n"
        
        self.refresh_local()
        if error_msg:
             wx.MessageBox(tr("err_local").format(error=error_msg), tr("app_title"))
        else:
             self.speech.speak(tr("msg_deleted_count").format(count=success_count))

    def do_remote_delete(self, event):
        items = self.get_selected_items(self.remote_list)
        if not items: return
        
        # Check setting
        confirm = self.settings.get("confirm_delete", False)
        if confirm:
            if wx.MessageBox(tr("msg_confirm_del_items").format(count=len(items)), tr("app_title"), wx.YES_NO) != wx.YES: return
            
        success_count = 0
        error_msg = ""

        def _r_remote_delete(sftp, remote_path):
             # Recursively delete a remote directory
             try:
                 attrs = sftp.listdir_attr(remote_path)
                 for attr in attrs:
                     name = attr.filename
                     if name in ('.', '..'): continue
                     r_path = remote_path + "/" + name
                     if stat.S_ISDIR(attr.st_mode):
                         _r_remote_delete(sftp, r_path)
                     else:
                         sftp.remove(r_path)
                 sftp.rmdir(remote_path)
             except Exception as e:
                 raise e

        for item in items:
            if item == "[..]": continue
            name = self.strip_brackets(item)
            path = self.remote_path + "/" + name
            try:
                if item.startswith("["): # Directory
                     _r_remote_delete(self.sftp, path)
                else:
                     self.sftp.remove(path)
                success_count += 1
            except Exception as e:
                 error_msg += f"{name}: {str(e)}\n"
        
        self.refresh_remote()
        if error_msg:
             wx.MessageBox(tr("err_remote").format(error=error_msg), tr("app_title"))
        else:
             self.speech.speak(tr("msg_deleted_count").format(count=success_count))

    def do_local_mkdir(self, event):
         dlg = wx.TextEntryDialog(self, tr("dlg_rename_msg"), tr("ctx_mkdir"))
         if dlg.ShowModal() == wx.ID_OK:
             try:
                 os.mkdir(os.path.join(self.local_path, dlg.GetValue()))
                 self.refresh_local()
             except Exception as e: wx.MessageBox(tr("err_local").format(error=e), tr("err_title"))

    def do_remote_mkdir(self, event):
         dlg = wx.TextEntryDialog(self, tr("dlg_rename_msg"), tr("ctx_mkdir"))
         if dlg.ShowModal() == wx.ID_OK:
             try:
                 self.sftp.mkdir(self.remote_path + "/" + dlg.GetValue())
                 self.refresh_remote()
             except Exception as e: wx.MessageBox(str(e), tr("err_title"), wx.ICON_ERROR)

    def save_session_paths(self):
        if self.settings.get("restore_last_path", True):
             profile_name = self.details.get("name")
             if profile_name:
                 self.config.update_profile_paths(profile_name, self.local_path, self.remote_path)

    def on_back_term(self, event):
         self.save_session_paths()
         if self.sftp:
             try: self.sftp.close()
             except: pass
         self.GetParent().switch_to_terminal(self.ssh_client, self.details)

    def on_disconnect(self, event):
        self.save_session_paths()
        if self.transfer_dlg:
            self.transfer_dlg.on_cancel(None)
        if self.ssh_client: self.ssh_client.disconnect()
        self.GetParent().show_welcome_screen()

    def on_refresh(self, event):
        self.refresh_lists()
        self.speech.speak(tr("msg_lists_refreshed"))

    def can_close(self):
        # Check if transfer dialog is active/visible
        if self.transfer_dlg and self.transfer_dlg.IsShown():
            res = wx.MessageBox(
                tr("msg_confirm_exit_transfer"), 
                tr("title_confirm_exit"), 
                wx.YES_NO | wx.ICON_WARNING
            )
            return res == wx.YES
        return True

    def resolve_conflict(self, filename):
        """
        Shows ConflictDialog on main thread and waits for result.
        Returns: (action, apply_all)
        action: 'overwrite', 'skip', 'rename', 'cancel'
        """
        result_container = {}
        event = threading.Event()
        
        def show():
            dlg = ConflictDialog(self, filename)
            if dlg.ShowModal() == wx.ID_OK:
                result_container['action'] = dlg.GetAction()
                result_container['apply_all'] = dlg.IsApplyAll()
            else:
                result_container['action'] = 'cancel'
                result_container['apply_all'] = False
            dlg.Destroy()
            event.set()
            
        wx.CallAfter(show)
        event.wait()
        return result_container.get('action', 'cancel'), result_container.get('apply_all', False)

    def prompt_rename(self, filename):
        """Thread-safe rename prompt."""
        result_container = {}
        event = threading.Event()
        
        def show():
            dlg = wx.TextEntryDialog(self, tr("msg_conflict_exist").format(filename=filename), tr("dlg_conflict_title"), f"copy_{filename}")
            if dlg.ShowModal() == wx.ID_OK:
                result_container['name'] = dlg.GetValue()
            else:
                result_container['name'] = None
            dlg.Destroy()
            event.set()
            
        wx.CallAfter(show)
        event.wait()
        return result_container.get('name')
