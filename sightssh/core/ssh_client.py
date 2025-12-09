import threading
import paramiko
import time
import logging

class SightSSHClient:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.channel = None
        self.transport = None
        self._connected = False
        self._reading = False
        self.on_data_callback = None
        self.on_error_callback = None
        self.on_disconnected_callback = None

    def connect(self, host, port, username, password=None, key_filename=None, passphrase=None, keep_alive=30):
        """
        Connects to the SSH server.
        Raises paramiko exceptions on failure.
        """
        try:
            logging.info(f"Connecting to {host}:{port} as {username} (Auth: {'Key' if key_filename else 'Password'})...")
            self.client.connect(
                hostname=host,
                port=int(port),
                username=username,
                password=password,
                key_filename=key_filename,
                passphrase=passphrase,
                timeout=10,
                allow_agent=False, # cleaner for now, explicit control
                look_for_keys=False
            )
            self.transport = self.client.get_transport()
            self._connected = True
            logging.info("SSH Connection Established.")
            
            # Start keepalive to prevent timeouts
            if keep_alive > 0:
                self.transport.set_keepalive(keep_alive)
            
        except Exception as e:
            logging.error(f"SSH Connection Failed: {e}")
            self._connected = False
            raise e

    def start_shell(self, on_data, on_error=None, on_disconnected=None):
        """
        Starts an interactive shell and spawns a thread to read output.
        on_data: callback(str) for stdout/data
        on_error: callback(str) for stderr/errors (optional)
        on_disconnected: callback() when connection closes
        """
        if not self._connected:
            raise Exception("Not connected")

        self.on_data_callback = on_data
        self.on_error_callback = on_error
        self.on_disconnected_callback = on_disconnected
        
        # invoke_shell creates a Channel
        self.channel = self.client.invoke_shell(term='xterm', width=80, height=24)
        self._reading = True
        
        # Start reader thread
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def _reader_loop(self):
        """Background loop to read data from channel."""
        while self._reading and self.channel and not self.channel.closed:
            if self.channel.recv_ready():
                try:
                    data = self.channel.recv(4096)
                    if len(data) == 0:
                        break # EOF
                    # Decode might lag if we get partial utf-8 bytes. 
                    # For simplicity, using replace errors, but ideally we buffer partials.
                    text = data.decode('utf-8', errors='replace')
                    if self.on_data_callback:
                        self.on_data_callback(text)
                except Exception as e:
                    # Connection lost or decode error
                    break
            
            time.sleep(0.01) # minimal sleep to prevent 100% cpu on quick loops

        # When loop ends, notify disconnection/eof
        self._connected = False
        if self.on_disconnected_callback:
             try: self.on_disconnected_callback()
             except: pass

    def send(self, data):
        """Sends data to the shell."""
        if self.channel and not self.channel.closed:
            self.channel.send(data)

    def resize(self, width, height):
        if self.channel and not self.channel.closed:
            self.channel.resize_pty(width=width, height=height)

    def resize_terminal(self, cols, rows):
        """Alias for resize to match UI calls."""
        self.resize(cols, rows)

    def open_sftp(self):
        """Returns an SFTPClient session."""
        if self._connected and self.transport:
            return self.transport.open_sftp_client()
        return None

    def disconnect(self):
        self._reading = False
        if self.channel:
            self.channel.close()
        if self.transport:
            self.transport.close()
        if self.client:
            self.client.close()
        self._connected = False
