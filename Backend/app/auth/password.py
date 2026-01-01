"""
Password Hashing and Verification
Uses bcrypt for secure password hashing
"""

import bcrypt
import secrets
import string
from typing import Tuple


class PasswordService:
    """Service for password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        # Generate a salt and hash the password
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds for good security/performance balance
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to check against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Length of password (default: 16)

        Returns:
            Random password
        """
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]

        # Fill the rest with random characters
        all_chars = lowercase + uppercase + digits + special
        password += [secrets.choice(all_chars) for _ in range(length - 4)]

        # Shuffle the password
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a secure random token for password reset.

        Returns:
            Random token (URL-safe)
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a secure random token for email verification.

        Returns:
            Random token (hex)
        """
        return secrets.token_hex(16)

    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, list]:
        """
        Check password strength and return feedback.

        Args:
            password: Password to check

        Returns:
            Tuple of (is_strong, list_of_issues)
        """
        issues = []

        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")

        if len(password) > 128:
            issues.append("Password must be at most 128 characters long")

        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")

        # Check for common passwords (basic check)
        common_passwords = [
            "password", "123456", "12345678", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]

        if password.lower() in common_passwords:
            issues.append("Password is too common, please choose a stronger password")

        is_strong = len(issues) == 0

        return is_strong, issues


# Create a global instance
password_service = PasswordService()
