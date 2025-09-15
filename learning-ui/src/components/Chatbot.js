import React, { useState, useRef, useEffect } from 'react';
import { FaComments, FaTimes, FaPaperPlane, FaRobot, FaUser, FaTrash } from 'react-icons/fa';
import { authenticatedFetch } from '../api';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [memoryContext, setMemoryContext] = useState(null);
  const [showMemory, setShowMemory] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage.trim(),
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Check if message is asking for notes or progress
    const isNotesRequest = /notes|day\s*\d+|month\s*\d+/i.test(userMessage.text);
    const isProgressRequest = /progress|status|completed|current/i.test(userMessage.text);

    try {
      // Send message to chatbot API
      const response = await authenticatedFetch('/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMessage.text })
      });

      const botMessage = {
        id: response.message_id,
        text: response.response,
        sender: 'bot',
        timestamp: response.timestamp,
        toolsExecuted: response.tools_executed || [],
        memoryUpdated: response.memory_updated || false
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Update memory context if available
      if (response.memory_context) {
        setMemoryContext(response.memory_context);
      }

      // If user is asking about progress, suggest the progress page
      if (isProgressRequest) {
        const suggestionMessage = {
          id: Date.now() + 1,
          text: "💡 You can view your detailed learning progress and track your journey in the Progress page. Would you like to go there now?",
          sender: 'bot',
          timestamp: new Date().toISOString(),
          isActionable: true,
          action: () => window.location.href = '/progress'
        };
        setMessages(prev => [...prev, suggestionMessage]);
      }
      
      // If user is asking about notes, suggest the notes feature
      if (isNotesRequest) {
        const suggestionMessage = {
          id: Date.now() + 2,
          text: "💡 You can access and download your learning notes for any day in the Progress page. Would you like to go there now?",
          sender: 'bot',
          timestamp: new Date().toISOString(),
          isActionable: true,
          action: () => window.location.href = '/progress'
        };
        setMessages(prev => [...prev, suggestionMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now(),
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = async () => {
    try {
      await authenticatedFetch('/chat/clear', {
        method: 'POST'
      });
      setMessages([]);
    } catch (error) {
      console.error('Clear chat error:', error);
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatMessageText = (text) => {
    // Split text into paragraphs
    const paragraphs = text.split('\n\n');
    
    return paragraphs.map((paragraph, index) => {
      // Check if it's a code block
      if (paragraph.includes('```')) {
        const codeMatch = paragraph.match(/```(\w+)?\n([\s\S]*?)```/);
        if (codeMatch) {
          const language = codeMatch[1] || '';
          const code = codeMatch[2];
          return (
            <div key={index} style={{
              background: '#f6f8fa',
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              padding: '12px',
              margin: '8px 0',
              fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
              fontSize: '13px',
              lineHeight: '1.4',
              overflowX: 'auto'
            }}>
              {language && (
                <div style={{
                  fontSize: '11px',
                  color: '#586069',
                  marginBottom: '8px',
                  textTransform: 'uppercase',
                  fontWeight: '600'
                }}>
                  {language}
                </div>
              )}
              <pre style={{
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                {code}
              </pre>
            </div>
          );
        }
      }
      
      // Check if it's a bullet point list
      if (paragraph.includes('•') || paragraph.includes('-')) {
        const lines = paragraph.split('\n');
        const listItems = lines.map((line, lineIndex) => {
          if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
            return (
              <li key={lineIndex} style={{ 
                marginBottom: '6px', 
                lineHeight: '1.5',
                paddingLeft: '4px'
              }}>
                {formatInlineText(line.trim().substring(1).trim())}
              </li>
            );
          }
          return null;
        }).filter(Boolean);
        
        return (
          <ul key={index} style={{ 
            margin: '12px 0', 
            paddingLeft: '20px',
            listStyleType: 'none'
          }}>
            {listItems}
          </ul>
        );
      }
      
      // Check if it's a numbered list
      if (paragraph.match(/^\d+\./)) {
        const lines = paragraph.split('\n');
        const listItems = lines.map((line, lineIndex) => {
          const match = line.match(/^(\d+)\.\s*(.*)/);
          if (match) {
            return (
              <li key={lineIndex} style={{ 
                marginBottom: '6px', 
                lineHeight: '1.5',
                paddingLeft: '4px'
              }}>
                {formatInlineText(match[2])}
              </li>
            );
          }
          return null;
        }).filter(Boolean);
        
        return (
          <ol key={index} style={{ 
            margin: '12px 0', 
            paddingLeft: '20px',
            lineHeight: '1.5'
          }}>
            {listItems}
          </ol>
        );
      }
      
      // Regular paragraph with inline formatting
      return (
        <p key={index} style={{ 
          margin: '12px 0', 
          lineHeight: '1.6',
          whiteSpace: 'pre-wrap'
        }}>
          {formatInlineText(paragraph)}
        </p>
      );
    });
  };

  const formatInlineText = (text) => {
    // Handle bold text (**text**)
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text (*text*)
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Handle inline code (`code`)
    text = text.replace(/`(.*?)`/g, '<code style="background: #f1f3f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; font-size: 12px;">$1</code>');
    
    // Handle markdown links [text](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #4f8cff; text-decoration: underline;">$1</a>');
    
    // Handle plain URLs (http/https)
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: #4f8cff; text-decoration: underline;">$1</a>');
    
    // Split by line breaks and create elements
    const parts = text.split('\n');
    return parts.map((part, index) => (
      <span key={index} dangerouslySetInnerHTML={{ __html: part }} />
    ));
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: isOpen ? '#dc3545' : '#4f8cff',
          color: 'white',
          border: 'none',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '20px',
          transition: 'all 0.3s ease'
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = 'scale(1.1)';
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'scale(1)';
        }}
      >
        {isOpen ? <FaTimes /> : <FaComments />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: '90px',
            right: '20px',
            width: '420px',
            height: '600px',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
            zIndex: 999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: '1px solid #e1e5e9'
          }}
        >
          {/* Chat Header */}
          <div
            style={{
              background: 'linear-gradient(135deg, #4f8cff, #6d9eff)',
              color: 'white',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderTopLeftRadius: '12px',
              borderTopRightRadius: '12px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FaRobot style={{ fontSize: '18px' }} />
              <span style={{ fontWeight: '600', fontSize: '16px' }}>EduAI Assistant</span>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setShowMemory(!showMemory)}
                style={{
                  background: showMemory ? 'rgba(255,255,255,0.2)' : 'none',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                title="Toggle memory"
              >
                🧠
              </button>
              <button
                onClick={clearChat}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                title="Clear chat"
              >
                <FaTrash style={{ fontSize: '14px' }} />
              </button>
            </div>
          </div>

          {/* Main Content Area */}
          <div style={{ flex: 1, display: 'flex' }}>
            {/* Memory Sidebar */}
            {showMemory && memoryContext && (
              <div style={{
                width: '200px',
                background: '#f0f7ff',
                borderRight: '1px solid #e1e5e9',
                padding: '12px',
                fontSize: '12px',
                overflowY: 'auto'
              }}>
                <div style={{ fontWeight: '600', marginBottom: '8px', color: '#1976d2' }}>
                  🧠 Memory Context
                </div>
                
                {memoryContext.current_progress && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontWeight: '500', color: '#666' }}>Progress</div>
                    <div>Day {memoryContext.current_progress.day}</div>
                    <div>{memoryContext.current_progress.percentage}% complete</div>
                  </div>
                )}
                
                {memoryContext.last_video && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontWeight: '500', color: '#666' }}>Last Video</div>
                    <div style={{ fontSize: '11px' }}>{memoryContext.last_video}</div>
                  </div>
                )}
                
                {memoryContext.recent_notes && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontWeight: '500', color: '#666' }}>Recent Notes</div>
                    <div style={{ fontSize: '11px' }}>{memoryContext.recent_notes}</div>
                  </div>
                )}
                
                {memoryContext.playlists && memoryContext.playlists.length > 0 && (
                  <div>
                    <div style={{ fontWeight: '500', color: '#666' }}>Playlists</div>
                    {memoryContext.playlists.slice(0, 3).map((playlist, i) => (
                      <div key={i} style={{ fontSize: '11px' }}>• {playlist}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Messages Container */}
            <div
              style={{
                flex: 1,
                padding: '16px',
                overflowY: 'auto',
                overflowX: 'hidden',
                background: '#f8f9fa',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                maxHeight: '400px',
                minHeight: '300px'
              }}
            >
            {messages.length === 0 ? (
              <div style={{ 
                textAlign: 'center', 
                color: '#666', 
                fontSize: '14px',
                marginTop: '20px'
              }}>
                <FaRobot style={{ fontSize: '32px', marginBottom: '10px', color: '#4f8cff' }} />
                <p>Hello! I'm your EduAI learning assistant.</p>
                <p>Ask me anything about studying, learning strategies, or academic advice!</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    display: 'flex',
                    justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: '8px'
                  }}
                >
                  <div
                    style={{
                      maxWidth: '85%',
                      padding: '12px 16px',
                      borderRadius: '18px',
                      background: message.sender === 'user' 
                        ? '#4f8cff' 
                        : message.isActionable ? '#f0f7ff' : 'white',
                      color: message.sender === 'user' ? 'white' : '#333',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      position: 'relative',
                      cursor: message.isActionable ? 'pointer' : 'default',
                      border: message.isActionable ? '1px solid #4f8cff' : 'none',
                      transition: 'all 0.2s ease',
                      wordWrap: 'break-word',
                      overflowWrap: 'break-word'
                    }}
                    onClick={() => message.isActionable && message.action && message.action()}
                    onMouseEnter={(e) => {
                      if (message.isActionable) {
                        e.currentTarget.style.background = '#e6f0ff';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (message.isActionable) {
                        e.currentTarget.style.background = '#f0f7ff';
                      }
                    }}
                  >
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      marginBottom: '4px'
                    }}>
                      {message.sender === 'bot' && <FaRobot style={{ fontSize: '12px', color: '#4f8cff' }} />}
                      {message.sender === 'user' && <FaUser style={{ fontSize: '12px' }} />}
                      <span style={{ 
                        fontSize: '11px', 
                        opacity: 0.7,
                        color: message.sender === 'user' ? 'rgba(255,255,255,0.8)' : '#666'
                      }}>
                        {formatTime(message.timestamp)}
                      </span>
                      {message.toolsExecuted && message.toolsExecuted.length > 0 && (
                        <span style={{
                          fontSize: '10px',
                          background: '#e8f4fd',
                          color: '#1976d2',
                          padding: '2px 6px',
                          borderRadius: '10px',
                          marginLeft: '4px'
                        }}>
                          🔧 {message.toolsExecuted.length} tools
                        </span>
                      )}
                      {message.memoryUpdated && (
                        <span style={{
                          fontSize: '10px',
                          background: '#f3e5f5',
                          color: '#7b1fa2',
                          padding: '2px 6px',
                          borderRadius: '10px',
                          marginLeft: '4px'
                        }}>
                          🧠 memory
                        </span>
                      )}
                    </div>
                    <div style={{ 
                      fontSize: '14px', 
                      lineHeight: '1.4'
                    }}>
                      {message.sender === 'bot' ? formatMessageText(message.text) : message.text}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  maxWidth: '80%',
                  padding: '12px 16px',
                  borderRadius: '18px',
                  background: 'white',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <div style={{
                    width: '16px',
                    height: '16px',
                    border: '2px solid #4f8cff',
                    borderTop: '2px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <span style={{ fontSize: '14px', color: '#666' }}>Thinking...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div style={{
            padding: '16px',
            borderTop: '1px solid #e1e5e9',
            background: 'white'
          }}>
            <div style={{
              display: 'flex',
              gap: '8px',
              alignItems: 'flex-end'
            }}>
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  border: '1px solid #e1e5e9',
                  borderRadius: '20px',
                  fontSize: '14px',
                  resize: 'none',
                  minHeight: '40px',
                  maxHeight: '100px',
                  outline: 'none',
                  fontFamily: 'inherit'
                }}
                rows={1}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: inputMessage.trim() && !isLoading ? '#4f8cff' : '#e1e5e9',
                  color: inputMessage.trim() && !isLoading ? 'white' : '#999',
                  border: 'none',
                  cursor: inputMessage.trim() && !isLoading ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s ease'
                }}
              >
                <FaPaperPlane style={{ fontSize: '14px' }} />
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};

export default Chatbot;
