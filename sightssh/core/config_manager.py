import os
import json
import base64
import platformdirs
from .security import SecurityManager

class ConfigManager:
    APP_NAME = "sightssh"
    APP_AUTHOR = "ddt.one"

    def __init__(self):
        self.config_dir = platformdirs.user_data_dir(self.APP_NAME, self.APP_AUTHOR, roaming=True)
        self.profiles_file = os.path.join(self.config_dir, "profiles.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self.logs_dir = os.path.join(self.config_dir, "logs")
        self._ensure_config_dir()
        self._ensure_log_dir()
        self._ensure_default_settings()

    def _ensure_log_dir(self):
        if not os.path.exists(self.logs_dir):
            try:
                os.makedirs(self.logs_dir)
            except: pass

    def _ensure_default_settings(self):
        defaults = {
            "language": "en",
            "show_hidden": True,
            "confirm_delete": False,
            "restore_last_path": True,
            "ascii_filter": True,
            "keep_alive": 30,
            "logging_enabled": False,
            "interaction_mode": "dedicated", 
            "output_type": "listbox",
            "notification_mode": "both",
            "verbosity": ["size", "type", "permissions", "owner", "group"],
            "check_updates_on_startup": True,
            "timeout": 10,
            "confirm_disconnect": False
        }
        
        current = self.get_settings()
        updated = False
        for key, value in defaults.items():
            if key not in current:
                current[key] = value
                updated = True
        
        if updated:
            self.save_settings(current)

    def get_settings(self):
        if not os.path.exists(self.settings_file):
            return {}
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Backup corrupted file
            try:
                import shutil
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = f"{self.settings_file}.corrupt_{ts}"
                shutil.copy2(self.settings_file, backup)
                import logging
                logging.error(f"Settings file corrupted. Backed up to {backup}")
            except: pass
            return {}

    def _atomic_write(self, filepath, data):
        """Writes data to a temp file then renames to target for atomicity."""
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            # Atomic replace
            os.replace(tmp_path, filepath)
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise e

    def save_settings(self, settings):
        self._atomic_write(self.settings_file, settings)

    def _ensure_config_dir(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def get_log_dir(self):
        return self.logs_dir

    def get_profiles(self):
        """Returns a dict of profiles: {name: profile_data_summary}."""
        if not os.path.exists(self.profiles_file):
            return {}
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
             # Backup corrupted file
            try:
                import shutil
                from datetime import datetime
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = f"{self.profiles_file}.corrupt_{ts}"
                shutil.copy2(self.profiles_file, backup)
                import logging
                logging.error(f"Profiles file corrupted. Backed up to {backup}")
            except: pass
            return {}

    def save_profile(self, name, host, port, username, auth_type, secret, key_path, profile_password):
        """
        Saves a profile.
        secret: Password or Key Passphrase (plaintext).
        profile_password: The password to lock this profile.
        """
        profiles = self.get_profiles()
        
        # Generate Salt for this profile
        salt = SecurityManager.generate_salt()
        salt_b64 = base64.urlsafe_b64encode(salt).decode('utf-8')

        # Encrypt the SSH secret (password/key_passphrase) using the Profile Password
        encrypted_secret = SecurityManager.encrypt_data(secret, profile_password, salt)

        # Create a verification token to verify the profile password later
        # We encrypt a known string "SIGHTSSH_VALID"
        verification_token = SecurityManager.encrypt_data("SIGHTSSH_VALID", profile_password, salt)

        profiles[name] = {
            "host": host,
            "port": port,
            "username": username,
            "auth_type": auth_type, # 'password' or 'key'
            "secret": encrypted_secret,
            "key_path": key_path, # We don't encrypt path usually, but we could if needed. Leaving plaintext for now.
            "salt": salt_b64,
            "verification_token": verification_token
        }

        self._atomic_write(self.profiles_file, profiles)

    def verify_profile_password(self, name, profile_password):
        """Verifies if the provided profile_password is correct for the profile."""
        profiles = self.get_profiles()
        if name not in profiles:
            return False
        
        profile = profiles[name]
        try:
            salt = base64.urlsafe_b64decode(profile['salt'])
            token = profile['verification_token']
            return SecurityManager.verify_password(profile_password, salt, token)
        except Exception:
            return False

    def get_profile_details(self, name, profile_password):
        """
        Returns full profile details including decrypted secret.
        Raises ValueError if password incorrect.
        """
        # Lazy import to avoid circular dependency if set_language was in init
        from sightssh.core.i18n import tr
        
        if not self.verify_profile_password(name, profile_password):
            raise ValueError(tr("err_invalid_prof_pass"))

        profiles = self.get_profiles()
        profile = profiles[name]
        salt = base64.urlsafe_b64decode(profile['salt'])
        
        # Decrypt secret
        decrypted_secret = SecurityManager.decrypt_data(profile['secret'], profile_password, salt)
        
        return {
            "name": name, # Ensure name is included
            "host": profile['host'],
            "port": profile['port'],
            "username": profile['username'],
            "auth_type": profile['auth_type'],
            "secret": decrypted_secret,
            "key_path": profile['key_path'],
            "last_local_path": profile.get("last_local_path"),
            "last_remote_path": profile.get("last_remote_path")
        }

    def update_profile_paths(self, name, local_path, remote_path):
        """Updates the last used paths for a profile without re-encrypting."""
        profiles = self.get_profiles()
        if name in profiles:
            profiles[name]["last_local_path"] = local_path
            profiles[name]["last_remote_path"] = remote_path
            self._atomic_write(self.profiles_file, profiles)

    def delete_profile(self, name):
        profiles = self.get_profiles()
        if name in profiles:
            del profiles[name]
            self._atomic_write(self.profiles_file, profiles)
