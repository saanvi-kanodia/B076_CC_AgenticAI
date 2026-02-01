
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import os
from datetime import datetime

# Mock merchant database - maps merchant IDs to email addresses
MERCHANT_EMAIL_DB = {
    'm_001': 'saanvikanodia05@gmail.com',
    'm_002': 'anushkabatte.college@gmail.com',
    'm_003': 'saanvikanodia05@gmail.com',
    'm_004': 'anushkabatte.college@gmail.com',
    'm_005': 'saanvikanodia05@gmail.com',
    'm_006': 'anushkabatte.college@gmail.com',
    'm_007': 'saanvikanodia05@gmail.com',
    'm_008': 'anushkabatte.college@gmail.com',
    'm_009': 'saanvikanodia05@gmail.com',
    'm_010': 'anushkabatte.college@gmail.com',
    'm_011': 'saanvikanodia05@gmail.com',
    'm_012': 'anushkabatte.college@gmail.com',
    'm_013': 'saanvikanodia05@gmail.com',
    'm_014': 'anushkabatte.college@gmail.com',
    'm_015': 'saanvikanodia05@gmail.com',
    'm_016': 'anushkabatte.college@gmail.com',
    'm_017': 'saanvikanodia05@gmail.com',
    'm_018': 'anushkabatte.college@gmail.com',
    'm_019': 'saanvikanodia05@gmail.com',
    'm_020': 'anushkabatte.college@gmail.com',
}

def get_merchant_emails(merchant_ids: List[str]) -> List[str]:
    """
    Get email addresses for a list of merchant IDs
    
    Args:
        merchant_ids: List of merchant IDs
        
    Returns:
        List of unique email addresses
    """
    emails = []
    for merchant_id in merchant_ids:
        email = MERCHANT_EMAIL_DB.get(merchant_id)
        if email and email not in emails:
            emails.append(email)
    return emails


def format_email_body(message_content: str, incident_id: str = None) -> str:
    """
    Format the AI response into a professional email body
    
    Args:
        message_content: The AI-generated response
        incident_id: Optional incident ID for reference
        
    Returns:
        Formatted email body
    """
    email_body = f"""
Dear Merchant,

We are reaching out regarding a recent support inquiry. Our AI support system has analyzed your issue and generated the following response:

{message_content}

---

If you have any further questions or need additional assistance, please don't hesitate to reach out to our support team.

Best regards,
Headless Migration Support Team

{f"Reference: Incident {incident_id}" if incident_id else ""}
Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    return email_body


def send_email(
    to_emails: List[str],
    subject: str,
    message_content: str,
    incident_id: str = None,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    sender_email: str = None,
    sender_password: str = None
) -> Dict[str, any]:
    """
    Send email notification to merchants
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject line
        message_content: The AI-generated response message
        incident_id: Optional incident ID for reference
        smtp_server: SMTP server address
        smtp_port: SMTP server port
        sender_email: Sender email address (defaults to env var)
        sender_password: Sender password (defaults to env var)
        
    Returns:
        Dictionary with success status and details
    """
    # Get credentials from environment variables if not provided
    sender_email = sender_email or os.getenv('SUPPORT_EMAIL', 'support@example.com')
    sender_password = sender_password or os.getenv('SUPPORT_EMAIL_PASSWORD', '')
    
    if not sender_password:
        # For demo purposes, we'll simulate sending
        print(f"📧 [DEMO MODE] Would send email to: {', '.join(to_emails)}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Message preview:\n{message_content[:200]}...")
        return {
            'success': True,
            'demo_mode': True,
            'recipients': to_emails,
            'message': 'Email simulation completed (no SMTP credentials configured)'
        }
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Format and attach body
        body = format_email_body(message_content, incident_id)
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to: {', '.join(to_emails)}")
        return {
            'success': True,
            'demo_mode': False,
            'recipients': to_emails,
            'message': 'Email sent successfully'
        }
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        # Fallback to demo mode
        print(f"📧 [DEMO MODE] Email content for: {', '.join(to_emails)}")
        print(f"📧 Subject: {subject}")
        print(f"📧 Message:\n{message_content}")
        return {
            'success': True,
            'demo_mode': True,
            'error': str(e),
            'recipients': to_emails,
            'message': 'Email simulated due to SMTP error'
        }


def send_incident_response(
    incident_data: Dict,
    response_content: str,
    is_edited: bool = False
) -> Dict[str, any]:
    """
    Send incident response to affected merchants
    
    Args:
        incident_data: Dictionary containing incident information
        response_content: The response message to send
        is_edited: Whether the response was edited by human
        
    Returns:
        Dictionary with sending status
    """
    # Extract merchant IDs from incident
    merchant_ids = incident_data.get('affected_merchants', [])
    incident_id = incident_data.get('incident_id', 'Unknown')
    
    if not merchant_ids:
        return {
            'success': False,
            'message': 'No merchant IDs found in incident data'
        }
    
    # Get email addresses
    emails = get_merchant_emails(merchant_ids)
    
    if not emails:
        return {
            'success': False,
            'message': 'No email addresses found for merchants'
        }
    
    # Create subject line
    subject = f"Support Update: {incident_data.get('summary', 'Issue Resolution')[:50]}"
    if is_edited:
        subject = f"[Reviewed] {subject}"
    
    # Send email
    result = send_email(
        to_emails=emails,
        subject=subject,
        message_content=response_content,
        incident_id=incident_id
    )
    
    return result


# Demo/test function
if __name__ == "__main__":
    # Test the email service
    print("Testing Email Service...")
    
    test_incident = {
        'incident_id': 'INC_001',
        'summary': 'CORS error on checkout page',
        'affected_merchants': ['m_001', 'm_006']
    }
    
    test_response = """
Hello,

We've identified that your CORS issue is due to missing origin whitelisting.

To resolve this:
1. Navigate to your API settings
2. Add your frontend domain to the allowed origins list
3. Restart your application

This should resolve the CORS errors you're experiencing.

Best regards,
Support Team
"""
    
    result = send_incident_response(test_incident, test_response)
    print(f"\nResult: {result}")
