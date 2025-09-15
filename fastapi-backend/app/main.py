from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, onboarding, youtube_schedule, chatbot
from app.routes import learning_plan
from app.routes import quiz

from app.database.db import create_tables, engine, Base
from sqlalchemy import text

app = FastAPI(title="EduAI Learning Platform", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Auth"])
app.include_router(onboarding.router, tags=["Onboarding"])
app.include_router(youtube_schedule.router, tags=["YouTubeSchedule"])
app.include_router(chatbot.router, tags=["Chatbot"])
app.include_router(learning_plan.router, tags=["LearningPlan"])
app.include_router(quiz.router, tags=["Quiz"])


@app.on_event("startup")
async def startup_event():
    """Force recreate all tables on startup to ensure a clean schema each run."""
    try:
        print("🔄 Initializing EduAI Agentic System...")
        
        # Initialize agent memory system
        from app.core.agent_memory import memory_manager
        print("✅ Agent memory system initialized")
        
        # Initialize OpenAI chatbot
        from app.core.openai_ai import chatbot
        print("✅ OpenAI chatbot initialized")
        
        print("🔄 Resetting database schema (public) with CASCADE...")
        # Hard reset the schema to handle any tables not present in SQLAlchemy metadata
        with engine.connect() as connection:
            connection = connection.execution_options(isolation_level="AUTOCOMMIT")
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
            connection.execute(text("CREATE SCHEMA public;"))
            # Optional grants for local dev environments
            connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        print("✅ Schema reset complete")

        # Create all tables with current models
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created with current schema")

        # Verify the onboarding table has the updated columns
        with engine.connect() as conn:
            result = conn.execute(text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'onboarding'
                ORDER BY ordinal_position
                """
            ))
            columns = [row[0] for row in result.fetchall()]

            required_columns = [
                'id', 'user_id', 'name', 'grade', 'career_goals', 'current_skills', 'time_commitment'
            ]

            missing_columns = [col for col in required_columns if col not in columns]

            if missing_columns:
                print(f"❌ Onboarding table missing columns: {missing_columns}")
            else:
                print("✅ Onboarding table has all expected columns")

    except Exception as e:
        print(f"❌ Error during database initialization: {e}")

@app.get("/")
def read_root():
    return {"message": "EduAI Learning Platform API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

