# OpenAI Chatbot Setup Guide

## 🔧 Setup Instructions

### 1. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in with your OpenAI account
3. Click "Create new secret key"
4. Copy the generated API key (starts with `sk-`)

### 2. Add to Environment Variables

Add the following to your `.env` file in the `fastapi-backend` directory:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 3. Install Dependencies

The `openai` package has been added to requirements. Install it:

```bash
cd fastapi-backend
pip install openai
```

### 4. Test the Integration

Start your FastAPI server:

```bash
python start_server.py
```

You should see output like:
```
✅ Agent memory system initialized
✅ OpenAI chatbot initialized
```

### 5. Available Models

Choose from these OpenAI models:

- `gpt-4o-mini` - Fast and cost-effective (recommended)
- `gpt-4o` - Most capable model
- `gpt-3.5-turbo` - Fastest response times

## 🎯 Features

The chatbot includes:

- **Always Visible**: Fixed position at bottom-right corner
- **Toggle Button**: Click to open/close chat window
- **Real-time Chat**: Powered by OpenAI GPT models
- **Session Management**: Maintains conversation context per user
- **Clear Chat**: Option to clear conversation history
- **Loading States**: Visual feedback during AI processing
- **Responsive Design**: Works on all screen sizes
- **LinkedIn Integration**: Share learning progress with one click

## 🤖 Chatbot Capabilities

The EduAI assistant can help with:

- **Learning Strategies**: Study tips and techniques
- **Programming Help**: Code examples and explanations
- **YouTube Integration**: Find and organize learning videos
- **Google Drive Notes**: Manage learning notes automatically
- **LinkedIn Sharing**: Share learning achievements
- **Progress Tracking**: Monitor learning journey
- **General Questions**: Any educational or learning-related queries

## 🔒 Security

- **Authentication Required**: Only authenticated users can access the chatbot
- **User Isolation**: Each user has their own chat session
- **API Key Protection**: Stored securely in environment variables

## 🐛 Troubleshooting

### If chatbot doesn't respond:
1. Check that `OPENAI_API_KEY` is set in `.env`
2. Verify the API key is valid and starts with `sk-`
3. Check your OpenAI account has sufficient credits
4. Check backend logs for errors
5. Ensure you're logged in to the application

### Common Issues:
- **"AI assistant not configured"**: Add `OPENAI_API_KEY` to your `.env` file
- **"Invalid API key"**: Verify your OpenAI API key is correct
- **"Rate limit exceeded"**: Check your OpenAI usage limits
- **"Import error"**: Run `pip install openai` to install dependencies

## 📝 Usage

1. **Open Chat**: Click the chat bubble icon at bottom-right
2. **Send Message**: Type your question and press Enter or click send
3. **Get Response**: AI will respond with helpful learning advice
4. **LinkedIn Share**: Ask "Share my learning progress on LinkedIn"
5. **YouTube Videos**: Ask "Find videos about Python programming"
6. **Clear Chat**: Click the trash icon to start fresh
7. **Close Chat**: Click the X button to minimize

## 🚀 Recent Features

- **OpenAI Integration**: Switched from Gemini to OpenAI for better performance
- **LinkedIn Sharing**: Zero-config LinkedIn post generation
- **YouTube Integration**: Video search and playlist management
- **Google Drive Notes**: Automatic note creation and management
- **Memory System**: Context-aware conversations
- **Tool Orchestration**: AI can use multiple tools simultaneously

The chatbot is designed to be educational, encouraging, and highly interactive - perfect for students seeking comprehensive learning assistance!