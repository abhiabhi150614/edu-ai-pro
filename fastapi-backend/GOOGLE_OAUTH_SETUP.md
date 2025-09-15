# Google OAuth Setup Guide

## Prerequisites
1. A Google Cloud Console account
2. A Google Cloud Project

## Setup Steps

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google OAuth2 API

### 2. Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "EduAI Learning Platform"
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes:
   - `openid` (required for Google OAuth)
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `https://www.googleapis.com/auth/youtube`

### 3. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:3000/auth/google/callback` (for development)
   - `https://yourdomain.com/auth/google/callback` (for production)
5. Copy the Client ID and Client Secret

### 4. Environment Variables
Add these to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

### 5. Frontend Environment Variables
Add to your React app's `.env` file:

```env
REACT_APP_GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

## Security Notes
- Never commit your `.env` file to version control
- Use environment variables in production
- Regularly rotate your client secrets
- Monitor OAuth usage in Google Cloud Console

## Testing
1. Start your FastAPI backend
2. Start your React frontend
3. Try registering/signing in with Google
4. Check that the callback URL works correctly

## Troubleshooting
- Ensure all required Google APIs are enabled
- Verify redirect URIs match exactly (including protocol and port)
- Check that your OAuth consent screen is configured correctly
- Monitor Google Cloud Console logs for any errors
- Make sure the `openid` scope is included in your OAuth consent screen