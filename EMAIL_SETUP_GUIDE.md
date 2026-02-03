# Email Setup Guide for Quizfy on Render

## Quick Summary
To enable password reset emails, you need to set up an email service. Here are your options (ranked by ease of setup):

---

## Option 1: Brevo (Easiest, Free)

Brevo (formerly Sendinblue) offers 300 free emails/day.

### Steps:
1. Go to https://www.brevo.com and create a free account
2. After login, go to **Settings** → **SMTP & API** → **SMTP**
3. Generate SMTP credentials
4. In Render Dashboard, add these environment variables:
   ```
   EMAIL_HOST = smtp-relay.brevo.com
   EMAIL_PORT = 587
   EMAIL_HOST_USER = your-brevo-login-email
   EMAIL_HOST_PASSWORD = your-smtp-key-from-brevo
   EMAIL_FROM_ADDRESS = your-verified-email@domain.com
   ```

---

## Option 2: SendGrid (Most Reliable)

SendGrid offers 100 free emails/day.

### Steps:
1. Go to https://sendgrid.com and create a free account
2. In SendGrid Dashboard, go to **Settings** → **API Keys**
3. Create an API Key with "Full Access" or at least "Mail Send" permission
4. **Important**: Verify a sender email in **Settings** → **Sender Authentication**
5. In Render Dashboard, add these environment variables:
   ```
   SENDGRID_API_KEY = SG.your-api-key-here
   EMAIL_FROM_ADDRESS = your-verified-sender@domain.com
   ```

---

## Option 3: Gmail SMTP (Not recommended for Render)

⚠️ Gmail often blocks connections from cloud services like Render.

---

## Setting Environment Variables on Render

1. Go to https://dashboard.render.com
2. Select your Quizfy service
3. Click **Environment** tab
4. Add each variable:
   - Click **Add Environment Variable**
   - Enter the key (e.g., `SENDGRID_API_KEY`)
   - Enter the value
5. Click **Save Changes**
6. Render will automatically redeploy with new settings

---

## Testing Email

After setting up, test by:
1. Go to your Quizfy site
2. Click "Forgot Password?" on the login page
3. Enter a valid email address
4. Check the inbox (and spam folder) for the reset email

---

## Troubleshooting

### Email not received?
- Check spam/junk folder
- Verify the sender email is authenticated in your email service
- Check Render logs for error messages

### 500 Error on password reset?
- Make sure all required environment variables are set
- Check that the API key is correct (no extra spaces)

### Console backend active?
If you see emails printed to logs instead of sent, it means no email service is configured. Add the environment variables above.
