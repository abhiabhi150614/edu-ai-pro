import openai
from app.core.config import settings
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import asyncio
from dataclasses import dataclass

# OpenAI client will be initialized per request

@dataclass
class AgentState:
    messages: List[Dict]
    user_id: int
    context: str
    tool_calls: List[Dict]
    memory_context: Dict
    next_action: str

class AgenticOpenAIChatbot:
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.chat_sessions: Dict[str, List[Dict]] = {}
        self.workflow = self._create_workflow()
    
    def get_or_create_session(self, user_id: int) -> List[Dict]:
        """Get existing chat session or create new one for user"""
        session_key = f"user_{user_id}"
        
        if session_key not in self.chat_sessions:
            # Create new chat session with system message
            self.chat_sessions[session_key] = [{
                "role": "system",
                "content": """
You are EduAI, an autonomous, memory-augmented learning companion and tool-using agent. 

CRITICAL FORMATTING RULES - FOLLOW THESE EXACTLY:

**TEXT FORMATTING:**
- Use **bold** for important concepts, headings, and key terms
- Use *italic* for emphasis and definitions
- Use `inline code` for code snippets, variables, and technical terms
- Use bullet points (•) for lists and key points
- Use numbered lists (1., 2., 3.) for step-by-step instructions
- Break up long responses into clear paragraphs

**CODE BLOCKS:**
- Always use proper code blocks with language specification
- Format: ```language\ncode\n```
- Examples: ```python\nprint("Hello")\n``` or ```javascript\nconsole.log("Hello")\n```
- Include comments in code to explain what it does
- Keep code examples simple and educational

**STRUCTURE:**
- Start with a clear introduction
- Use headings with **bold** formatting
- Provide practical examples with code blocks
- End with a summary or next steps
- Keep responses comprehensive but well-organized (3-5 paragraphs max)

**YOUR AGENTIC CAPABILITIES:**
You are an autonomous agent that can:
• Answer programming questions with deep explanations + runnable code
• Manage Google Drive notes: fetch, add content, return clickable links
• Manage YouTube: search videos, create playlists, add videos, summarize content
• Track user progress: current day, % completion, quiz results, adaptive recommendations
• Maintain multi-layer memory: conversation, episodic, semantic, graph memory
• Handle multi-intent queries by decomposing into subtasks
• Handle invalid requests gracefully with corrections and alternatives
• Always enrich responses with context, progress, and smart suggestions

**AGENTIC RULES:**
✅ Always provide real, clickable YouTube links (never placeholders)
✅ Store every YouTube link, playlist, and Drive link in memory
✅ When asked to "add video to playlist" without a link → resolve using memory
❌ Never allow invalid ops (e.g., adding notes to playlists) → correct gently + suggest alternatives
✅ Use tool orchestration for multi-intent queries
✅ Always enrich responses with: progress state, memory context, smart recommendations

**MEMORY SYSTEM:**
• Conversation Memory → recent chat history
• Episodic Memory → past actions, links, playlists created
• Semantic Memory → concept dependencies, learning relationships
• Always recall relevant context from memory before responding

**AGENTIC BEHAVIOR:**
- Act like a proactive tutor + assistant
- Always be context-aware (use memory + history)
- Be polite, encouraging, and motivating
- Handle multi-intent queries by decomposing into subtasks
- Always confirm tool actions (e.g., "Added X to Y playlist")
- Use emojis: 📘 Notes → 🎥 Videos → 🎯 Playlists → ✅ Progress → 🚀 Encouragement
- Format responses with markdown, code blocks, clickable links
- When explaining programming, always include runnable code examples
- Store all links and actions in memory for future reference
- Provide smart recommendations based on progress and memory
- Gracefully handle invalid requests with corrections and alternatives

Remember: Your responses should be well-formatted, educational, and include practical examples!
"""
            }]
        
        return self.chat_sessions[session_key]
    
    def _format_response(self, response_text: str) -> str:
        """Format the response for better readability"""
        # Clean up any extra whitespace
        response_text = response_text.strip()
        
        # Ensure proper paragraph spacing
        paragraphs = response_text.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Ensure bullet points are properly formatted
                if paragraph.startswith('•') or paragraph.startswith('-'):
                    # Keep bullet points as is
                    formatted_paragraphs.append(paragraph)
                elif paragraph.startswith(('1.', '2.', '3.', '4.', '5.')):
                    # Keep numbered lists as is
                    formatted_paragraphs.append(paragraph)
                else:
                    # Add proper spacing for regular paragraphs
                    formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _create_workflow(self):
        """Create simple workflow orchestration"""
        return self  # Simplified - no LangGraph for now
    
    async def _get_memory_context(self, user_id: int, message: str) -> Dict:
        """Get memory context for user"""
        try:
            from app.core.agent_memory import memory_manager
            
            conversation_memory = memory_manager.recall_conversation(user_id, 5)
            episodic_memory = memory_manager.recall_episodic(user_id)
            
            return {
                "conversation": conversation_memory,
                "episodic": episodic_memory[:5],
                "semantic": [],
                "graph": {}
            }
        except Exception as e:
            print(f"Memory error: {e}")
            return {"conversation": [], "episodic": [], "semantic": [], "graph": {}}
    
    def _parse_intent(self, message: str) -> List[Dict]:
        """Fast intent parsing with auto-suggestions"""
        tools = []
        msg_lower = message.lower()
        
        # Auto-suggest videos for learning topics
        learning_keywords = ['learn', 'understand', 'explain', 'help', 'tutorial', 'how to']
        if any(kw in msg_lower for kw in learning_keywords):
            tools.append({"tool": "youtube", "function": "search_videos", "params": {"message": message}})
        
        # Notes intent (simplified)
        if 'notes' in msg_lower or 'day' in msg_lower:
            tools.append({"tool": "notes", "function": "get_notes", "params": {"message": message}})
        
        return tools
    
    async def _execute_tools(self, tool_calls: List[Dict], user_id: int, context: str) -> List[Dict]:
        """Execute tools directly"""
        results = []
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get("tool")
                function_name = tool_call.get("function")
                params = tool_call.get("params", {})
                
                # Simple tool execution
                if tool_name == "notes" and function_name == "get_notes":
                    from app.core.agentic_tools import get_notes_tool
                    result = get_notes_tool(params.get("message", ""), user_id)
                elif tool_name == "youtube" and function_name == "search_videos":
                    from app.core.agentic_tools import search_youtube_tool
                    result = search_youtube_tool(params.get("message", ""), user_id)
                elif tool_name == "progress" and function_name == "get_progress":
                    from app.core.agentic_tools import get_progress_tool
                    result = get_progress_tool(user_id)
                else:
                    result = {"error": f"Unknown tool: {tool_name}_{function_name}"}
                
                results.append(result)
                
            except Exception as e:
                results.append({"error": str(e)})
        
        return results
    
    async def _generate_response(self, message: str, user_id: int, memory_context: Dict, tool_results: List[Dict]) -> str:
        """Generate response using OpenAI with comprehensive learning context"""
        try:
            # Build enhanced response prompt with learning analytics
            response_prompt = f"""
User message: {message}

Context: {memory_context}
Tool results: {tool_results}

RESPONSE REQUIREMENTS:
1. Write 3-5 paragraphs with detailed explanations
2. ALWAYS suggest relevant YouTube videos with search terms
3. Include code examples when explaining programming concepts
4. Use emojis, bullet points, and markdown formatting
5. Be encouraging and interactive
6. Ask follow-up questions to engage the user
7. Provide step-by-step guidance
8. Reference their current learning progress when relevant

Make responses comprehensive, interactive, and educational!
"""
            
            chat_session = self.get_or_create_session(user_id)
            chat_session.append({"role": "user", "content": response_prompt})
            
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=self.model,
                messages=chat_session,
                max_tokens=1500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            # Add assistant response to session
            chat_session.append({"role": "assistant", "content": response_text})
            
            return self._format_response(response_text)
            
        except Exception as e:
            print(f"Response error: {e}")
            return "I'm having trouble generating a response. Please try again."
    
    async def get_response(self, message: str, user_id: int, context: str = "") -> Dict:
        """Main entry point with comprehensive learning context"""
        try:
            if not settings.OPENAI_API_KEY:
                return {
                    "response": "AI assistant not configured.",
                    "timestamp": datetime.now().isoformat(),
                    "message_id": str(uuid.uuid4())
                }
            
            # Get enhanced memory context with learning analytics
            memory_context = await self._get_memory_context(user_id, message)
            
            # Combine memory context with learning context from chatbot route
            enhanced_context = f"{context}\n\nMemoryContext: {memory_context}"
            
            # Parse intents and execute tools
            tool_calls = self._parse_intent(message)
            tool_results = []
            
            if tool_calls:
                tool_results = await self._execute_tools(tool_calls, user_id, enhanced_context)
            
            # Generate contextually aware response
            response_text = await self._generate_response(message, user_id, enhanced_context, tool_results)
            
            # Store conversation with learning context
            try:
                from app.core.agent_memory import memory_manager
                memory_manager.store_conversation(
                    user_id, message, response_text, 
                    [tc.get("tool", "") for tc in tool_calls]
                )
                
                # Store learning interaction if it involves help with failed concepts
                if any(keyword in message.lower() for keyword in ['help', 'explain', 'understand', 'confused']):
                    memory_manager.store_episodic(user_id, "learning_help", {
                        "message": message,
                        "response_length": len(response_text),
                        "tools_used": [tc.get("tool", "") for tc in tool_calls]
                    })
                    
            except Exception as e:
                print(f"Memory storage error: {e}")
            
            return {
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4()),
                "tools_executed": [tc.get("tool", "") for tc in tool_calls],
                "memory_updated": True,
                "context_aware": True
            }
            
        except Exception as e:
            print(f"Workflow error: {str(e)}")
            return {
                "response": "I'm having trouble processing your request. Please try again.",
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4())
            }
    
    def clear_session(self, user_id: int) -> bool:
        """Clear chat session for user"""
        session_key = f"user_{user_id}"
        if session_key in self.chat_sessions:
            del self.chat_sessions[session_key]
            return True
        return False

# Global agentic chatbot instance
chatbot = AgenticOpenAIChatbot()