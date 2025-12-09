import unittest
import shutil
import os
from sightssh.core.security import SecurityManager
from sightssh.core.config_manager import ConfigManager

class TestSecurity(unittest.TestCase):
    def test_encryption_cycle(self):
        salt = SecurityManager.generate_salt()
        pwd = "testpassword"
        data = "SecretData123"
        
        enc = SecurityManager.encrypt_data(data, pwd, salt)
        dec = SecurityManager.decrypt_data(enc, pwd, salt)
        
        self.assertEqual(data, dec)

    def test_verify_false(self):
        salt = SecurityManager.generate_salt()
        enc = SecurityManager.encrypt_data("test", "correct", salt)
        
        try:
             SecurityManager.decrypt_data(enc, "wrong", salt)
             self.fail("Should have failed")
        except Exception:
             pass

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Use a temporary dir for config
        self.cm = ConfigManager()
        self.cm.config_dir = "test_config_dir"
        self.cm.profiles_file = os.path.join(self.cm.config_dir, "profiles.json")
        self.cm._ensure_config_dir()
        
    def tearDown(self):
        if os.path.exists("test_config_dir"):
            shutil.rmtree("test_config_dir")

    def test_save_load_profile(self):
        self.cm.save_profile("test1", "localhost", 22, "user", "password", "ssh_secret", "", "profile_lock")
        
        profiles = self.cm.get_profiles()
        self.assertIn("test1", profiles)
        self.assertEqual(profiles["test1"]["host"], "localhost")
        
        # Verify secret is encrypted
        self.assertNotEqual(profiles["test1"]["secret"], "ssh_secret")
        
        # Verify password check
        self.assertTrue(self.cm.verify_profile_password("test1", "profile_lock"))
        self.assertFalse(self.cm.verify_profile_password("test1", "wrong"))
        
        # Verify details load
        details = self.cm.get_profile_details("test1", "profile_lock")
        self.assertEqual(details["secret"], "ssh_secret")

if __name__ == '__main__':
    unittest.main()
