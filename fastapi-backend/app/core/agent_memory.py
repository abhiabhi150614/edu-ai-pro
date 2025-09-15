"""
Enhanced Memory Management for Agentic EduAI
Handles multi-layer memory: conversation, episodic, semantic, graph
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from sentence_transformers import SentenceTransformer
import networkx as nx

@dataclass
class MemoryEntry:
    user_id: int
    content: str
    memory_type: str  # conversation, episodic, semantic
    metadata: Dict[str, Any]
    timestamp: datetime
    embedding: Optional[List[float]] = None

class AgentMemoryManager:
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_graph = nx.DiGraph()
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                memory_type TEXT,
                metadata TEXT,
                timestamp TEXT,
                embedding BLOB
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                source_node TEXT,
                target_node TEXT,
                relationship TEXT,
                weight REAL,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_conversation(self, user_id: int, user_message: str, ai_response: str, tools_used: List[str] = None):
        """Store conversation in memory"""
        conversation_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "tools_used": tools_used or []
        }
        
        entry = MemoryEntry(
            user_id=user_id,
            content=f"User: {user_message}\nAI: {ai_response}",
            memory_type="conversation",
            metadata=conversation_data,
            timestamp=datetime.now()
        )
        
        self._store_entry(entry)
    
    def store_episodic(self, user_id: int, action: str, result: Dict[str, Any]):
        """Store episodic memory (actions, results, links)"""
        entry = MemoryEntry(
            user_id=user_id,
            content=f"Action: {action}",
            memory_type="episodic",
            metadata=result,
            timestamp=datetime.now()
        )
        
        self._store_entry(entry)
        
        # Update knowledge graph
        if "youtube_link" in result:
            self._add_to_graph(user_id, action, result["youtube_link"], "created_link")
        if "playlist_name" in result:
            self._add_to_graph(user_id, action, result["playlist_name"], "created_playlist")
    
    def store_semantic(self, user_id: int, concept: str, related_concepts: List[str]):
        """Store semantic relationships between concepts"""
        entry = MemoryEntry(
            user_id=user_id,
            content=concept,
            memory_type="semantic",
            metadata={"related_concepts": related_concepts},
            timestamp=datetime.now()
        )
        
        self._store_entry(entry)
        
        # Add to knowledge graph
        for related in related_concepts:
            self._add_to_graph(user_id, concept, related, "related_to")
    
    def _store_entry(self, entry: MemoryEntry):
        """Store memory entry in database"""
        # Generate embedding
        embedding = self.embedding_model.encode(entry.content).tolist()
        entry.embedding = embedding
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memory_entries (user_id, content, memory_type, metadata, timestamp, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            entry.user_id,
            entry.content,
            entry.memory_type,
            json.dumps(entry.metadata, default=str),
            entry.timestamp.isoformat(),
            json.dumps(embedding)
        ))
        
        conn.commit()
        conn.close()
    
    def _add_to_graph(self, user_id: int, source: str, target: str, relationship: str, weight: float = 1.0):
        """Add relationship to knowledge graph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge_graph (user_id, source_node, target_node, relationship, weight, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, source, target, relationship, weight, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Update in-memory graph
        self.knowledge_graph.add_edge(f"{user_id}:{source}", f"{user_id}:{target}", 
                                    relationship=relationship, weight=weight)
    
    def recall_conversation(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Recall recent conversations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content, metadata, timestamp FROM memory_entries
            WHERE user_id = ? AND memory_type = 'conversation'
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "content": row[0],
                "metadata": json.loads(row[1]),
                "timestamp": row[2]
            })
        
        conn.close()
        return results
    
    def recall_episodic(self, user_id: int, action_type: str = None) -> List[Dict]:
        """Recall episodic memories (past actions)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT content, metadata, timestamp FROM memory_entries
            WHERE user_id = ? AND memory_type = 'episodic'
        '''
        params = [user_id]
        
        if action_type:
            query += ' AND content LIKE ?'
            params.append(f'%{action_type}%')
        
        query += ' ORDER BY timestamp DESC LIMIT 20'
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "content": row[0],
                "metadata": json.loads(row[1]),
                "timestamp": row[2]
            })
        
        conn.close()
        return results
    
    def semantic_search(self, user_id: int, query: str, limit: int = 5) -> List[Dict]:
        """Perform semantic search across all memories"""
        query_embedding = self.embedding_model.encode(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content, metadata, timestamp, embedding FROM memory_entries
            WHERE user_id = ?
        ''', (user_id,))
        
        results = []
        for row in cursor.fetchall():
            stored_embedding = np.array(json.loads(row[3]))
            similarity = np.dot(query_embedding, stored_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
            )
            
            if similarity > 0.5:  # Threshold for relevance
                results.append({
                    "content": row[0],
                    "metadata": json.loads(row[1]),
                    "timestamp": row[2],
                    "similarity": float(similarity)
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        conn.close()
        return results[:limit]
    
    def get_related_concepts(self, user_id: int, concept: str) -> List[str]:
        """Get related concepts from knowledge graph"""
        user_concept = f"{user_id}:{concept}"
        
        if user_concept in self.knowledge_graph:
            related = []
            for neighbor in self.knowledge_graph.neighbors(user_concept):
                clean_concept = neighbor.split(":", 1)[1] if ":" in neighbor else neighbor
                related.append(clean_concept)
            return related
        
        return []
    
    def get_graph_context(self, user_id: int, query: str) -> Dict[str, Any]:
        """Get GraphRAG context for query"""
        # Extract key concepts from query
        query_concepts = self._extract_concepts(query)
        
        graph_context = {
            "related_notes": [],
            "related_videos": [],
            "concept_dependencies": {},
            "learning_path": []
        }
        
        for concept in query_concepts:
            user_concept = f"{user_id}:{concept}"
            
            if user_concept in self.knowledge_graph:
                # Get all connected nodes
                neighbors = list(self.knowledge_graph.neighbors(user_concept))
                
                for neighbor in neighbors:
                    edge_data = self.knowledge_graph.get_edge_data(user_concept, neighbor)
                    relationship = edge_data.get('relationship', 'related')
                    
                    clean_neighbor = neighbor.split(":", 1)[1] if ":" in neighbor else neighbor
                    
                    if 'note' in relationship or 'day' in clean_neighbor.lower():
                        graph_context["related_notes"].append(clean_neighbor)
                    elif 'video' in relationship or 'youtube' in clean_neighbor.lower():
                        graph_context["related_videos"].append(clean_neighbor)
                    elif 'depends' in relationship:
                        if concept not in graph_context["concept_dependencies"]:
                            graph_context["concept_dependencies"][concept] = []
                        graph_context["concept_dependencies"][concept].append(clean_neighbor)
        
        return graph_context
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        programming_concepts = [
            'python', 'javascript', 'recursion', 'loops', 'functions', 'variables',
            'classes', 'objects', 'arrays', 'strings', 'algorithms', 'data structures'
        ]
        
        text_lower = text.lower()
        found_concepts = []
        
        for concept in programming_concepts:
            if concept in text_lower:
                found_concepts.append(concept)
        
        # Also extract day references
        import re
        day_matches = re.findall(r'day\s*(\d+)', text_lower)
        for day in day_matches:
            found_concepts.append(f"day_{day}")
        
        return found_concepts
    
    def link_concepts(self, user_id: int, source_concept: str, target_concept: str, relationship: str = "related"):
        """Create bidirectional concept links"""
        self._add_to_graph(user_id, source_concept, target_concept, relationship)
        # Add reverse relationship
        reverse_rel = f"reverse_{relationship}"
        self._add_to_graph(user_id, target_concept, source_concept, reverse_rel)
    
    def create_learning_path_graph(self, user_id: int, day: int, concept: str, resources: List[str]):
        """Create graph connections for learning day"""
        day_node = f"day_{day}"
        
        # Link day to concept
        self.link_concepts(user_id, day_node, concept, "teaches")
        
        # Link concept to resources
        for resource in resources:
            if 'youtube' in resource or 'video' in resource:
                self.link_concepts(user_id, concept, resource, "video_resource")
            elif 'notes' in resource or 'drive' in resource:
                self.link_concepts(user_id, concept, resource, "note_resource")
    
    def get_last_youtube_link(self, user_id: int) -> Optional[str]:
        """Get the last YouTube link from episodic memory"""
        episodic_memories = self.recall_episodic(user_id, "youtube")
        
        for memory in episodic_memories:
            metadata = memory["metadata"]
            if "youtube_link" in metadata:
                return metadata["youtube_link"]
        
        return None
    
    def get_user_playlists(self, user_id: int) -> List[str]:
        """Get all playlists created by user"""
        episodic_memories = self.recall_episodic(user_id, "playlist")
        
        playlists = []
        for memory in episodic_memories:
            metadata = memory["metadata"]
            if "playlist_name" in metadata:
                playlists.append(metadata["playlist_name"])
        
        return list(set(playlists))  # Remove duplicates
    
    def get_contextual_memory(self, user_id: int, query: str) -> Dict[str, Any]:
        """Get comprehensive contextual memory using GraphRAG"""
        # Combine vector search with graph traversal
        semantic_results = self.semantic_search(user_id, query, 5)
        graph_context = self.get_graph_context(user_id, query)
        
        # Get recent episodic memories
        recent_actions = self.recall_episodic(user_id)[:5]
        
        return {
            "semantic_matches": semantic_results,
            "graph_context": graph_context,
            "recent_actions": recent_actions,
            "summary": f"Found {len(semantic_results)} semantic matches, {len(graph_context.get('related_notes', []))} related notes"
        }
    
    def cleanup_old_memories(self, user_id: int, days: int = 30):
        """Clean up memories older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM memory_entries
            WHERE user_id = ? AND timestamp < ? AND memory_type = 'conversation'
        ''', (user_id, cutoff_date.isoformat()))
        
        conn.commit()
        conn.close()

# Global memory manager instance
memory_manager = AgentMemoryManager()