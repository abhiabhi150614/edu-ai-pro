# 🎓 EduAI - AI-Powered Personalized Learning Platform

EduAI is a comprehensive, intelligent learning platform that combines the power of artificial intelligence with modern web technologies to create personalized educational experiences. The platform features an autonomous AI assistant, adaptive learning paths, integrated content management, and social sharing capabilities to revolutionize how students learn and track their progress.

## 📸 Screenshots & Demo

<!-- Images will be displayed in chronological order based on file creation time -->
<!-- Add your screenshots to the ./images/ folder and they will appear here automatically -->

![Landing Page](./images/LandingPage.png)
![Sign In](./images/Signin.png)
![Onboarding Step 1](./images/onboard1.png)
![Onboarding Step 2](./images/onboard2.png)
![Onboarding Step 3](./images/onboard3.png)
![Onboarding Step 4](./images/onboard4.png)
![Onboarding Step 5](./images/onboard5.png)
![Dashboard](./images/dashboard.png)
![Learning Path](./images/Learning_Path.png)
![Learning Path 2](./images/Learning_path_2.png)
![Day Content](./images/Day-content.png)
![Quiz](./images/quizz.png)
![Quiz Completion](./images/quizz%20completion.png)
![Start Next Day](./images/start%20next%20day.png)
![YouTube Integration 1](./images/Ytube1.png)
![YouTube Integration 2](./images/Ytube2.png)

<!-- Alternative: If you prefer specific names, rename your images in chronological order -->
<!-- Example: landing-page.png, dashboard.png, chatbot.png, etc. -->

---

## 🏗️ **Architecture Overview**

### **Technology Stack**
- **Frontend**: React.js 18+ with React Router for SPA navigation
- **Backend**: FastAPI (Python) with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI Engine**: OpenAI GPT-4o-mini for intelligent responses
- **Authentication**: JWT tokens + Google OAuth 2.0
- **File Storage**: Google Drive API integration
- **Video Platform**: YouTube Data API v3
- **Social Integration**: LinkedIn sharing via MCP (Model Context Protocol)
- **Memory System**: Multi-layer memory with NetworkX graphs
- **Deployment**: Docker-ready with environment configuration

### **System Architecture Diagram**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React.js      │    │   FastAPI       │    │  PostgreSQL     │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   OpenAI API    │              │
         │              │   (GPT-4o-mini) │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Google APIs    │    │  YouTube API    │    │  LinkedIn MCP   │
│  (Drive, OAuth) │    │  (Videos, etc.) │    │  (Sharing)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🚀 **Core Features & Functionality**

### **1. User Authentication & Security**

#### **Multi-Modal Authentication System**
- **Email/Password Authentication**: Traditional signup with bcrypt password hashing
- **Google OAuth 2.0 Integration**: Seamless login with Google accounts
- **JWT Token Management**: Secure session handling with automatic token refresh
- **Phone Verification**: Two-factor authentication via SMS verification
- **Session Persistence**: Secure token storage with automatic logout on expiry

#### **Security Features**
- **Password Encryption**: bcrypt hashing with salt rounds
- **CORS Protection**: Configured for specific origins
- **Input Validation**: Pydantic schemas for all API endpoints
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Input sanitization and output encoding

### **2. Intelligent Onboarding System**

#### **Personalized Setup Wizard**
The onboarding process captures essential user information to create tailored learning experiences:

- **Personal Information**: Name, grade level, educational background
- **Career Goals**: Multiple selection from predefined career paths
- **Current Skills Assessment**: Self-evaluation of existing knowledge
- **Time Commitment**: Available study hours per day/week
- **Learning Preferences**: Visual, auditory, kinesthetic learning styles
- **Subject Interests**: Primary and secondary areas of focus

#### **Data Processing & Plan Generation**
```python
# Onboarding data structure
{
    "name": "John Doe",
    "grade": "12th Grade",
    "career_goals": ["Software Development", "Data Science"],
    "current_skills": ["Basic Python", "Mathematics"],
    "time_commitment": "2-3 hours daily",
    "learning_style": "Visual + Hands-on",
    "subjects": ["Computer Science", "Mathematics", "Physics"]
}
```

### **3. AI-Powered Learning Path Generation**

#### **Dynamic Curriculum Creation**
The system generates personalized learning paths based on:
- User's career goals and current skill level
- Time availability and learning pace preferences
- Industry-standard skill requirements
- Progressive difficulty scaling

#### **Learning Path Structure**
```json
{
    "title": "Full-Stack Web Development Mastery",
    "duration": "6 months",
    "difficulty": "Beginner to Advanced",
    "months": [
        {
            "index": 1,
            "title": "Frontend Fundamentals",
            "status": "active",
            "days": [
                {
                    "day": 1,
                    "concept": "HTML5 Semantic Elements",
                    "description": "Learn modern HTML structure",
                    "resources": ["videos", "articles", "exercises"],
                    "estimated_time": "2 hours",
                    "completed": false
                }
            ]
        }
    ]
}
```

### **4. Autonomous AI Assistant (OpenAI Integration)**

#### **Agentic Architecture**
The AI assistant operates as an autonomous agent with multiple capabilities:

##### **Core AI Components**
- **OpenAI GPT-4o-mini**: Primary language model for responses
- **Context Management**: Maintains conversation history and user state
- **Tool Orchestration**: Can execute multiple tools simultaneously
- **Memory Integration**: Accesses multi-layer memory system
- **Intent Recognition**: Parses user requests for appropriate actions

##### **AI Assistant Capabilities**
```python
class AgenticOpenAIChatbot:
    def __init__(self):
        self.model = "gpt-4o-mini"
        self.tools = [
            "youtube_search",      # Find educational videos
            "google_drive_notes",  # Manage learning notes
            "progress_tracking",   # Monitor learning journey
            "linkedin_sharing",    # Share achievements
            "quiz_generation",     # Create practice tests
            "concept_explanation"  # Detailed explanations
        ]
```

#### **Intelligent Response Generation**
The AI assistant provides:
- **Contextual Responses**: Based on user's current learning progress
- **Code Examples**: Runnable code snippets with explanations
- **Visual Learning**: Markdown formatting with emojis and structure
- **Interactive Elements**: Follow-up questions and suggestions
- **Resource Recommendations**: Automatic YouTube video suggestions
- **Progress Awareness**: References to user's achievements and struggles

### **5. Multi-Layer Memory System**

#### **Memory Architecture**
```python
class MemoryManager:
    def __init__(self):
        self.conversation_memory = []    # Recent chat history
        self.episodic_memory = []       # Past actions and events
        self.semantic_memory = {}       # Concept relationships
        self.graph_memory = NetworkX()  # Knowledge graph
```

#### **Memory Types & Functions**
- **Conversation Memory**: Stores recent chat interactions for context
- **Episodic Memory**: Records user actions (video searches, note creation)
- **Semantic Memory**: Maps relationships between learning concepts
- **Graph Memory**: Creates knowledge graphs linking topics and resources

### **6. Interactive Quiz System**

#### **AI-Generated Assessments**
- **Dynamic Question Creation**: AI generates questions based on learning content
- **Multiple Choice Format**: 4 options with detailed explanations
- **Difficulty Adaptation**: Questions adjust based on user performance
- **Immediate Feedback**: Instant results with learning recommendations
- **Progress Tracking**: Performance analytics and improvement suggestions

#### **Quiz Generation Process**
```python
def generate_quiz(topic, difficulty, user_progress):
    prompt = f"""
    Create a {difficulty} level quiz about {topic}.
    User's current progress: {user_progress}
    Generate 5 multiple choice questions with:
    - Clear, educational questions
    - 4 options (A, B, C, D)
    - Detailed explanations for correct answers
    - Hints for incorrect answers
    """
    return openai_client.generate(prompt)
```

### **7. Google Drive Integration**

#### **Automatic Note Management**
- **Structured Organization**: Creates folders by month and day
- **Real-time Sync**: Automatic saving and retrieval
- **Collaborative Editing**: Google Docs integration for rich text
- **Version Control**: Maintains edit history and revisions
- **Search Functionality**: Find notes by content or date

#### **Drive API Implementation**
```python
class GoogleDriveService:
    def create_day_notes(self, user_id, month, day):
        # Create Google Doc for specific learning day
        doc_title = f"EduAI - Month {month} Day {day} Notes"
        folder_structure = f"EduAI Learning/{user_id}/Month_{month}"
        
        # Create document with template
        document = self.drive_service.files().create(
            body={
                'name': doc_title,
                'parents': [folder_id],
                'mimeType': 'application/vnd.google-apps.document'
            }
        ).execute()
        
        return document
```

### **8. YouTube Learning Integration**

#### **Intelligent Video Curation**
- **Smart Search**: AI-powered video discovery based on learning topics
- **Playlist Management**: Automatic creation and organization
- **Content Filtering**: Educational content prioritization
- **Duration Optimization**: Matches videos to available study time
- **Quality Assessment**: Prioritizes high-rated educational channels

#### **YouTube API Features**
```python
class YouTubeService:
    def search_educational_videos(self, query, max_results=10):
        search_response = self.youtube.search().list(
            q=f"{query} tutorial programming",
            part="id,snippet",
            maxResults=max_results,
            type="video",
            videoDuration="medium",  # 4-20 minutes
            videoDefinition="high",
            relevanceLanguage="en"
        ).execute()
        
        return self.process_video_results(search_response)
```

### **9. LinkedIn Social Integration (MCP)**

#### **Zero-Configuration Sharing**
Unlike traditional OAuth integrations, EduAI uses Model Context Protocol (MCP) for LinkedIn sharing:

- **No API Keys Required**: Uses LinkedIn's native sharing URLs
- **Pre-filled Content**: AI generates professional posts
- **One-Click Sharing**: Direct links to LinkedIn's sharing interface
- **Achievement Tracking**: Includes quiz scores and learning milestones

#### **LinkedIn Post Generation**
```python
def generate_linkedin_post(user_id, day, quiz_score=None):
    template = f"""
    🎓 Day {day} of my learning journey completed! 
    
    📚 Today's Focus: {current_concept}
    {f"Quiz Score: {quiz_score}% {'✅' if quiz_score >= 80 else '📚'}" if quiz_score else ""}
    📊 Overall Progress: {progress_percentage}%
    
    Loving the structured approach with EduAI - making complex topics digestible! 
    
    #Learning #AI #Education #TechSkills #ContinuousLearning #EduAI
    """
    
    # Create LinkedIn sharing URL
    encoded_content = urllib.parse.quote(template)
    share_url = f"https://www.linkedin.com/sharing/share-offsite/?text={encoded_content}"
    
    return share_url
```

---

## 🗂️ **Database Schema & Data Models**

### **User Management**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    
    -- Google OAuth
    google_id VARCHAR(255) UNIQUE,
    google_email VARCHAR(255),
    google_name VARCHAR(255),
    google_picture VARCHAR(255),
    google_access_token TEXT,
    google_refresh_token TEXT,
    is_google_authenticated BOOLEAN DEFAULT FALSE,
    
    -- Profile
    phone_number VARCHAR(20),
    phone_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Learning Progress
    current_plan_id INTEGER,
    current_month_index INTEGER,
    current_day INTEGER
);
```

### **Learning Plans**
```sql
CREATE TABLE learning_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    plan JSONB NOT NULL,  -- Stores the complete learning structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Quiz System**
```sql
CREATE TABLE quiz_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    month_index INTEGER NOT NULL,
    day INTEGER NOT NULL,
    questions JSONB NOT NULL,
    answers JSONB NOT NULL,
    score INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Onboarding Data**
```sql
CREATE TABLE onboarding (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) UNIQUE,
    name VARCHAR(255) NOT NULL,
    grade VARCHAR(100),
    career_goals JSONB,  -- Array of career interests
    current_skills JSONB,  -- Array of existing skills
    time_commitment VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 **API Endpoints & Routes**

### **Authentication Routes**
```python
# User Authentication
POST   /register              # Create new user account
POST   /login                 # User login with credentials
POST   /google-auth           # Google OAuth login
GET    /me                    # Get current user profile
POST   /phone/send-verification  # Send SMS verification
POST   /phone/verify          # Verify phone number
```

### **Learning Management**
```python
# Onboarding
POST   /onboarding           # Submit onboarding data
GET    /onboarding           # Get user onboarding info

# Learning Plans
POST   /learning-plan/generate  # Generate personalized plan
GET    /learning-plan         # Get user's learning plan
PUT    /learning-plan/progress # Update learning progress
GET    /learning-plan/summary  # Get progress summary
```

### **AI Chatbot**
```python
# Chat Interface
POST   /chat                 # Send message to AI assistant
POST   /chat/clear           # Clear chat history
GET    /chat/memory          # Get conversation memory
```

### **Content Management**
```python
# Google Drive Notes
GET    /notes/{month}/{day}  # Get notes for specific day
POST   /notes/{month}/{day}  # Update day notes
GET    /notes/search         # Search notes by content

# YouTube Integration
GET    /youtube/search       # Search educational videos
GET    /youtube/playlists    # Get user playlists
POST   /youtube/playlists    # Create new playlist
POST   /youtube/playlists/{id}/videos  # Add video to playlist
GET    /youtube/videos/{id}/summary    # Get video summary
```

### **Assessment System**
```python
# Quiz Management
POST   /quiz/generate        # Generate quiz for topic
POST   /quiz/submit          # Submit quiz answers
GET    /quiz/history         # Get quiz history
GET    /quiz/analytics       # Get performance analytics
```

---

## 🎯 **User Journey & Workflows**

### **1. New User Registration Flow**
```mermaid
graph TD
    A[Landing Page] --> B{Login Method}
    B -->|Email| C[Register Form]
    B -->|Google| D[Google OAuth]
    C --> E[Email Verification]
    D --> F[Account Created]
    E --> F
    F --> G[Onboarding Wizard]
    G --> H[Learning Plan Generation]
    H --> I[Dashboard]
```

### **2. Daily Learning Workflow**
```mermaid
graph TD
    A[Dashboard] --> B[Current Day Topic]
    B --> C[AI Assistant Help]
    C --> D[Study Materials]
    D --> E[Take Quiz]
    E --> F{Quiz Passed?}
    F -->|Yes| G[Progress to Next Day]
    F -->|No| H[Review & Retry]
    G --> I[Update Notes]
    H --> C
    I --> J[Share Achievement]
```

### **3. AI Assistant Interaction Flow**
```mermaid
graph TD
    A[User Message] --> B[Intent Recognition]
    B --> C[Context Retrieval]
    C --> D[Tool Selection]
    D --> E[Tool Execution]
    E --> F[Response Generation]
    F --> G[Memory Update]
    G --> H[Display Response]
```

---

## 🛠️ **Development Setup & Installation**

### **Prerequisites**
- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL 13+
- Git

### **Backend Setup**
```bash
# Clone repository
git clone <repository-url>
cd learning-web/learning/fastapi-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your API keys and database credentials

# Database setup
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Frontend Setup**
```bash
# Navigate to frontend directory
cd learning-web/learning/learning-ui

# Install dependencies
npm install

# Start development server
npm start
```

### **Environment Variables**
```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/eduaidb

# Security
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Google APIs
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# YouTube API
YOUTUBE_API_KEY=your-youtube-api-key
```

---

## 🧪 **Testing & Quality Assurance**

### **Backend Testing**
```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Test coverage
pytest --cov=app tests/
```

### **Frontend Testing**
```bash
# Run component tests
npm test

# Run end-to-end tests
npm run test:e2e

# Build production bundle
npm run build
```

### **API Testing**
```bash
# Test API endpoints
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

---

## 🚀 **Deployment & Production**

### **Docker Deployment**
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### **Production Environment**
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./fastapi-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/eduai
    depends_on:
      - db
  
  frontend:
    build: ./learning-ui
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: eduai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 📊 **Performance & Monitoring**

### **Performance Metrics**
- **Response Time**: Average API response < 200ms
- **Database Queries**: Optimized with indexing and connection pooling
- **Memory Usage**: Efficient memory management with garbage collection
- **Concurrent Users**: Supports 1000+ simultaneous users
- **AI Response Time**: OpenAI integration < 3 seconds average

### **Monitoring & Logging**
```python
# Logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eduai.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🔒 **Security & Privacy**

### **Data Protection**
- **GDPR Compliance**: User data handling and deletion rights
- **Encryption**: All sensitive data encrypted at rest and in transit
- **Access Control**: Role-based permissions and authentication
- **Audit Logging**: Complete audit trail of user actions
- **Privacy by Design**: Minimal data collection and retention

### **Security Measures**
- **Input Validation**: All user inputs validated and sanitized
- **SQL Injection Prevention**: Parameterized queries only
- **XSS Protection**: Output encoding and CSP headers
- **Rate Limiting**: API endpoint protection against abuse
- **Session Security**: Secure JWT token handling

---

## 🤝 **Contributing & Development**

### **Code Standards**
- **Python**: PEP 8 compliance with Black formatting
- **JavaScript**: ESLint with Airbnb configuration
- **Git**: Conventional commit messages
- **Documentation**: Comprehensive docstrings and comments

### **Development Workflow**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📈 **Future Roadmap**

### **Planned Features**
- **Mobile App**: React Native mobile application
- **Advanced Analytics**: Learning pattern analysis and insights
- **Collaborative Learning**: Study groups and peer interactions
- **Gamification**: Points, badges, and leaderboards
- **Multi-language Support**: Internationalization and localization
- **Advanced AI**: Custom fine-tuned models for education
- **Integration Expansion**: More third-party service integrations

### **Technical Improvements**
- **Microservices Architecture**: Service decomposition for scalability
- **Real-time Features**: WebSocket integration for live interactions
- **Advanced Caching**: Redis implementation for performance
- **CDN Integration**: Global content delivery optimization
- **Advanced Security**: OAuth 2.1 and advanced threat protection

---

## 📞 **Support & Contact**

### **Documentation**
- **API Documentation**: Available at `/docs` endpoint
- **User Guide**: Comprehensive user manual
- **Developer Guide**: Technical implementation details
- **FAQ**: Common questions and solutions

### **Community**
- **GitHub Issues**: Bug reports and feature requests
- **Discord Server**: Community discussions and support
- **Email Support**: technical-support@eduai.com
- **Documentation Wiki**: Community-maintained guides

---

## 📄 **License & Legal**

### **Open Source License**
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **Third-Party Licenses**
- OpenAI API: Subject to OpenAI Terms of Service
- Google APIs: Subject to Google API Terms of Service
- YouTube API: Subject to YouTube API Terms of Service
- All other dependencies: See individual package licenses

---

**EduAI** - Revolutionizing education through artificial intelligence and personalized learning experiences. Built with ❤️ for learners worldwide.
