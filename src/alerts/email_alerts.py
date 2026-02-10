"""
Email Notification Module for Anomaly Alerts
=============================================

Sends email alerts to admin when anomalies are detected in CCTV footage.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Config file path for persistence (in project root)
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'email_config.json')

# Default email configuration
DEFAULT_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "admin_emails": [],
    "enabled": False
}


def _load_config() -> Dict[str, Any]:
    """Load email config from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure enabled flag is set correctly
                config["enabled"] = bool(
                    config.get("sender_email") and 
                    config.get("sender_password") and 
                    config.get("admin_emails")
                )
                return config
        except Exception as e:
            logger.error(f"Error loading email config: {e}")
    return DEFAULT_CONFIG.copy()


def _save_config(config: Dict[str, Any]):
    """Save email config to file"""
    try:
        # Don't save the password in plain text - just save a placeholder
        save_config = config.copy()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(save_config, f, indent=2)
        logger.info("Email configuration saved")
    except Exception as e:
        logger.error(f"Error saving email config: {e}")


# Load config on module import
EMAIL_CONFIG = _load_config()


def configure_email(
    smtp_server: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
    admin_emails: List[str]
):
    """Configure email settings and save to file"""
    global EMAIL_CONFIG
    EMAIL_CONFIG["smtp_server"] = smtp_server
    EMAIL_CONFIG["smtp_port"] = smtp_port
    EMAIL_CONFIG["sender_email"] = sender_email
    EMAIL_CONFIG["sender_password"] = sender_password
    EMAIL_CONFIG["admin_emails"] = admin_emails
    EMAIL_CONFIG["enabled"] = bool(sender_email and sender_password and admin_emails)
    
    # Save to file for persistence
    _save_config(EMAIL_CONFIG)
    
    return EMAIL_CONFIG["enabled"]


def send_anomaly_alert(
    anomaly_types: List[str],
    details: List[str],
    video_filename: str,
    frame_screenshot: Optional[bytes] = None,
    video_id: Optional[int] = None
) -> bool:
    """
    Send email alert when anomaly is detected
    
    Args:
        anomaly_types: List of anomaly type names
        details: List of detail messages
        video_filename: Name of the video file
        frame_screenshot: Optional screenshot bytes (JPEG)
        video_id: Optional video ID in database
        
    Returns:
        True if email sent successfully
    """
    if not EMAIL_CONFIG["enabled"]:
        logger.warning("Email alerts not configured - skipping notification")
        return False
    
    if not EMAIL_CONFIG["admin_emails"] or not EMAIL_CONFIG["admin_emails"][0]:
        logger.warning("No admin emails configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = ", ".join(EMAIL_CONFIG["admin_emails"])
        msg["Subject"] = f"🚨 ANOMALY ALERT: {', '.join(anomaly_types)}"
        
        # Create HTML body
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 10px;">
                <h1 style="margin: 0;">🚨 Anomaly Detected!</h1>
            </div>
            
            <div style="padding: 20px; background: #f5f5f5; margin-top: 20px; border-radius: 10px;">
                <h2>Alert Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Time:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{timestamp}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Video:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{video_filename}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Anomaly Types:</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                            {''.join([f'<span style="background:#e74c3c;color:white;padding:5px 10px;border-radius:3px;margin-right:5px;">{t}</span>' for t in anomaly_types])}
                        </td>
                    </tr>
                </table>
                
                <h3>Details:</h3>
                <ul>
                    {''.join([f'<li>{d}</li>' for d in details])}
                </ul>
                
                {f'<p><a href="http://localhost:8000/history/{video_id}">View Video Analysis</a></p>' if video_id else ''}
            </div>
            
            <p style="color: #666; margin-top: 20px;">
                This is an automated alert from the CCTV Anomaly Detection System.
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, "html"))
        
        # Attach screenshot if provided
        if frame_screenshot:
            image = MIMEImage(frame_screenshot, name="anomaly_screenshot.jpg")
            image.add_header('Content-ID', '<screenshot>')
            msg.attach(image)
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.send_message(msg)
        
        logger.info(f"Alert email sent to {EMAIL_CONFIG['admin_emails']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email alert: {str(e)}")
        return False


def get_email_status() -> Dict[str, Any]:
    """Get current email configuration status"""
    return {
        "enabled": EMAIL_CONFIG["enabled"],
        "smtp_server": EMAIL_CONFIG["smtp_server"],
        "sender_configured": bool(EMAIL_CONFIG["sender_email"]),
        "admin_emails_count": len([e for e in EMAIL_CONFIG["admin_emails"] if e])
    }
