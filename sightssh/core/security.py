import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class SecurityManager:
    """
    Handles encryption and decryption of sensitive data using a password-derived key.
    Also handles password hashing for verification.
    """
    
    @staticmethod
    def generate_salt():
        """Generates a random 16-byte salt."""
        return os.urandom(16)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derives a url-safe base64-encoded key from the password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt_data(data: str, password: str, salt: bytes) -> str:
        """
        Encrypts string data using a key derived from password and salt.
        Returns the encrypted bytes as a base64 string.
        """
        key = SecurityManager.derive_key(password, salt)
        f = Fernet(key)
        encrypted_bytes = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')

    @staticmethod
    def decrypt_data(encrypted_data: str, password: str, salt: bytes) -> str:
        """
        Decrypts base64 encoded encrypted data using password and salt.
        Returns the original string.
        """
        key = SecurityManager.derive_key(password, salt)
        f = Fernet(key)
        # encrypted_data is expected to be a base64 string, convert to bytes
        # but Fernet expects bytes so we decode the wrapper if needed? 
        # Actually Fernet.encrypt returns bytes.
        # We stored it as base64 string, so we need to decode that first?
        # Wait, f.encrypt returns bytes. In encrypt_data I did base64.urlsafe_b64encode(enc_bytes).
        # So here:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
        decrypted_bytes = f.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')

    @staticmethod
    def verify_password(password: str, salt: bytes, encrypted_check_data: str) -> bool:
        """
        Verifies if a password is correct by attempting to decrypt a known check value.
        This uses the encryption mechanism itself as verification (if we can decrypt, the password is right).
        """
        try:
            # We don't necessarily need a separate hash if we just test decryption.
            # But normally we might store a hash to verify before trying real decryption.
            # For simplicity in this app, we can just use try-decrypt.
            # However, providing a robust check is better.
            # Let's assume we store a 'check' string like "SIGHTSSH_OK" encrypted.
            decrypted = SecurityManager.decrypt_data(encrypted_check_data, password, salt)
            return decrypted == "SIGHTSSH_VALID"
        except Exception:
            return False
