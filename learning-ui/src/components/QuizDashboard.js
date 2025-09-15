import React, { useEffect, useState } from 'react';
import { authenticatedFetch } from '../api';
import { useNavigate } from 'react-router-dom';

const QuizCard = ({ quiz, onClick }) => (
  <div 
    onClick={onClick}
    style={{
      background: 'white',
      borderRadius: 8,
      padding: 12,
      border: '1px solid #e5e7eb',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      marginBottom: 8
    }}
    onMouseEnter={(e) => {
      e.target.style.transform = 'translateY(-1px)';
      e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
    }}
    onMouseLeave={(e) => {
      e.target.style.transform = 'translateY(0)';
      e.target.style.boxShadow = 'none';
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
      <div style={{ flex: 1 }}>
        <div style={{ 
          fontSize: 12, 
          color: '#6b7280', 
          marginBottom: 4,
          textTransform: 'uppercase',
          fontWeight: 600
        }}>
          {quiz.plan_title}
        </div>
        <div style={{ 
          fontSize: 14, 
          fontWeight: 600, 
          color: '#374151',
          marginBottom: 4
        }}>
          {quiz.month_title} • Day {quiz.day}
        </div>
        <div style={{ 
          fontSize: 12, 
          color: '#6b7280',
          lineHeight: 1.4
        }}>
          {quiz.day_concept}
        </div>
      </div>
      
      <div style={{ 
        padding: '4px 8px', 
        borderRadius: 12, 
        fontSize: 11, 
        fontWeight: 600,
        background: quiz.completed ? '#dcfce7' : '#fef3c7',
        color: quiz.completed ? '#166534' : '#92400e'
      }}>
        {quiz.completed ? '✅ Done' : '📝 Quiz'}
      </div>
    </div>
    
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      fontSize: 12,
      color: '#6b7280'
    }}>
      <span>{quiz.total_questions} questions</span>
      <span>Pass ≥ {quiz.required_score}%</span>
    </div>
    
    {quiz.completed && quiz.best_score && (
      <div style={{ 
        marginTop: 8,
        padding: '4px 8px',
        background: '#f0f9ff',
        borderRadius: 6,
        fontSize: 11,
        color: '#1e40af',
        textAlign: 'center'
      }}>
        Best Score: {quiz.best_score}%
      </div>
    )}
  </div>
);

const QuizDashboard = () => {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({});
  const navigate = useNavigate();

  const loadQuizzes = async () => {
    try {
      setLoading(true);
      const data = await authenticatedFetch('/available-quizzes');
      setQuizzes(data.quizzes || []);
      setStats({
        total: data.total_quizzes || 0,
        completed: data.completed_quizzes || 0,
        pending: data.pending_quizzes || 0
      });
    } catch (e) {
      console.error('Error loading quizzes:', e);
      setError('Failed to load quizzes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuizzes();
  }, []);

  const handleQuizClick = (quiz) => {
    navigate(quiz.url);
  };

  const refreshQuizzes = () => {
    loadQuizzes();
  };

  if (loading) {
    return (
      <div style={{ padding: 16 }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 8, 
          marginBottom: 16,
          color: '#6b7280'
        }}>
          <div style={{ 
            width: 16, 
            height: 16, 
            border: '2px solid #e5e7eb', 
            borderTop: '2px solid #4f8cff', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite' 
          }}></div>
          Loading quizzes...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 16 }}>
        <div style={{ 
          color: '#ef4444', 
          marginBottom: 12, 
          fontSize: 14 
        }}>
          ❌ {error}
        </div>
        <button 
          onClick={refreshQuizzes}
          style={{ 
            padding: '6px 12px', 
            borderRadius: 6, 
            border: '1px solid #ef4444', 
            background: 'transparent', 
            color: '#ef4444',
            fontSize: 12,
            cursor: 'pointer'
          }}
        >
          🔄 Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: 16 }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 8, 
          marginBottom: 8 
        }}>
          <span style={{ fontSize: 20 }}>📝</span>
          <h3 style={{ 
            margin: 0, 
            fontSize: 16, 
            fontWeight: 700, 
            color: '#111827' 
          }}>
            Quiz Dashboard
          </h3>
        </div>
        
        {/* Stats */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(3, 1fr)', 
          gap: 8, 
          marginBottom: 16 
        }}>
          <div style={{ 
            textAlign: 'center', 
            padding: '8px', 
            background: '#f0f9ff', 
            borderRadius: 6,
            border: '1px solid #dbeafe'
          }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#1e40af' }}>
              {stats.total}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Total</div>
          </div>
          <div style={{ 
            textAlign: 'center', 
            padding: '8px', 
            background: '#f0fdf4', 
            borderRadius: 6,
            border: '1px solid #a7f3d0'
          }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#166534' }}>
              {stats.completed}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Done</div>
          </div>
          <div style={{ 
            textAlign: 'center', 
            padding: '8px', 
            background: '#fff7ed', 
            borderRadius: 6,
            border: '1px solid #fed7aa'
          }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#92400e' }}>
              {stats.pending}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280' }}>Pending</div>
          </div>
        </div>
        
        {/* Refresh button */}
        <button 
          onClick={refreshQuizzes}
          style={{ 
            width: '100%',
            padding: '8px 12px', 
            borderRadius: 6, 
            border: '1px solid #d1d5db', 
            background: '#fff',
            color: '#374151',
            fontSize: 12,
            cursor: 'pointer'
          }}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Quiz List */}
      {quizzes.length === 0 ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '20px', 
          color: '#6b7280',
          fontSize: 14
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>📝</div>
          <div>No quizzes available</div>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            Start learning to generate quizzes
          </div>
        </div>
      ) : (
        <div>
          <div style={{ 
            fontSize: 12, 
            color: '#6b7280', 
            marginBottom: 12,
            fontWeight: 600,
            textTransform: 'uppercase'
          }}>
            Available Quizzes ({quizzes.length})
          </div>
          
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {quizzes.map((quiz) => (
              <QuizCard 
                key={quiz.id} 
                quiz={quiz} 
                onClick={() => handleQuizClick(quiz)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizDashboard;
