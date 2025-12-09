import urllib.request
import threading
import json
import logging
from packaging import version

class UpdateChecker:
    VERSION_URL = "https://raw.githubusercontent.com/Daoductrung/SightSSH/main/version.md"
    
    @staticmethod
    def check_update(current_version):
        """
        Checks version.md from GitHub.
        Expected format:
        v0.4.0
        # Changelog ...
        """
        try:
            with urllib.request.urlopen(UpdateChecker.VERSION_URL, timeout=5) as response:
                if response.status != 200:
                    return False, None, None
                
                content = response.read().decode('utf-8').strip()
                lines = content.split('\n')
                
                if not lines:
                    return False, None, None
                    
                remote_ver_str = lines[0].strip()
                if remote_ver_str.startswith('v'):
                    remote_ver_str = remote_ver_str[1:]
                
                # Compare versions
                # Handle dev versions loosely or strict? 
                # Using simple string compare if parsing fails, else packaging.version
                try:
                    curr = version.parse(current_version)
                    rem = version.parse(remote_ver_str)
                    has_update = rem > curr
                except:
                    # Fallback for simple cases
                    has_update = remote_ver_str != current_version

                changelog = "\n".join(lines[1:]).strip()
                
                return has_update, remote_ver_str, changelog
                
        except Exception as e:
            logging.warning(f"Update Check Failed: {e}")
            return False, None, None
