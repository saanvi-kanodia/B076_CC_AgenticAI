# Email Service Configuration Guide

## Overview

The email service automatically sends AI-generated responses to merchants at three key points:

1. **High Confidence (≥80%)**: Emails sent automatically when response is displayed
2. **Approve Button**: Emails sent when you click "Approve & Send"
3. **Edited Response**: Emails sent when you edit and click "Send"

## Current Setup (Demo Mode)

The system is currently running in **DEMO MODE** which means:

- No actual emails are sent
- Email content is logged to console
- Emails go to: `saanvikanodia05@gmail.com` and `anushkabatte.college@gmail.com`
- All merchant IDs map to these two email addresses

## How to Enable Real Email Sending

### Option 1: Using Gmail (Recommended for Testing)

1. **Create an App Password** (required for Gmail):
   - Go to your Google Account settings
   - Navigate to Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Copy the 16-character password

2. **Set Environment Variables**:

   ```bash
   export SUPPORT_EMAIL="your-gmail@gmail.com"
   export SUPPORT_EMAIL_PASSWORD="your-app-password"
   ```

3. **Restart Streamlit**:
   ```bash
   streamlit run sample_UI.py
   ```

### Option 2: Using Custom SMTP Server

Edit `email_service.py` and modify the `send_email` function parameters:

```python
smtp_server = "your-smtp-server.com"
smtp_port = 587  # or 465 for SSL
```

## Email Content Structure

Each email includes:

- **Professional greeting**
- **AI-generated response** (the exact content from the UI)
- **Incident reference number**
- **Timestamp**
- **Support team signature**

## Merchant Email Database

Located in `email_service.py` as `MERCHANT_EMAIL_DB`:

```python
MERCHANT_EMAIL_DB = {
    'm_001': 'saanvikanodia05@gmail.com',
    'm_002': 'anushkabatte.college@gmail.com',
    # ... more mappings
}
```

To add more merchants, simply add entries to this dictionary.

## Testing

Run the test script:

```bash
python email_service.py
```

This will simulate sending an email and show you the output.

## Integration Points in UI

### 1. High Confidence Auto-Send

```python
# Automatically sends when confidence >= 0.8
email_result = send_incident_response(
    incident_data=selected_incident,
    response_content=message_content,
    is_edited=False
)
```

### 2. Approve Button

```python
# Sends when "Approve & Send" is clicked
if st.button("Approve & Send"):
    email_result = send_incident_response(...)
```

### 3. Edit & Send

```python
# Sends edited version when "Send" is clicked after editing
if st.button("Send"):
    email_result = send_incident_response(
        response_content=edited,
        is_edited=True  # Adds [Reviewed] to subject
    )
```

## Email Status Indicators

The UI shows:

- ✅ Green success message when email is sent
- 📧 Blue info message in demo mode
- Recipient count display

## Security Notes

- Never commit SMTP passwords to git
- Use environment variables for credentials
- Consider using app-specific passwords
- For production, use a dedicated support email address

## Troubleshooting

### "Demo Mode" message appears

- SMTP credentials are not configured
- Set `SUPPORT_EMAIL` and `SUPPORT_EMAIL_PASSWORD` environment variables

### SMTP Authentication Error

- Check your email provider's SMTP settings
- Ensure 2FA app passwords are used for Gmail
- Verify firewall/network settings

### Emails not received

- Check spam/junk folders
- Verify recipient email addresses in `MERCHANT_EMAIL_DB`
- Check email provider's sending limits
