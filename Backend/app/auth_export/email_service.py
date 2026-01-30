"""
Email Service Module.
Handles sending emails via SMTP with SSL support.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from typing import Optional

try:
    from config import SMTP_USERNAME, SMTP_PASSWORD
except ImportError:
    from .config import SMTP_USERNAME, SMTP_PASSWORD

# Configure module-level logger
logger = logging.getLogger(__name__)

class EmailServiceError(Exception):
    """Custom exception for EmailService failures."""
    pass

class EmailService:
    """
    Service for sending emails using SMTP SSL.
    """

    def __init__(self, smtp_server: str = 'smtp.gmail.com', smtp_port: int = 465):
        """
        Initialize the EmailService.

        Args:
            smtp_server (str): The SMTP server address. Defaults to Gmail.
            smtp_port (int): The SMTP server port (SSL). Defaults to 465.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.error("SMTP credentials are missing in configuration.")

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Sends an HTML email to a specified recipient.

        Args:
            to_email (str): The recipient's email address.
            subject (str): The email subject.
            body (str): The HTML body of the email.

        Returns:
            bool: True if sent successfully, False otherwise.

        Raises:
            EmailServiceError: If a critical error occurs (and is not caught).
        """
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.error("Cannot send email: Missing SMTP credentials.")
            return False

        try:
            msg = MIMEText(body, 'html')
            msg['Subject'] = subject
            msg['From'] = SMTP_USERNAME
            msg['To'] = to_email

            logger.debug(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {e}")
            return False
