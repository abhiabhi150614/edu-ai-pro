import React, { useEffect, useState } from 'react';
import Layout from './Layout';
import { authenticatedFetch } from '../api';
import { useLocation, useNavigate } from 'react-router-dom';

const QuizCard = ({ children, style }) => (
  <div style={{
    background: 'white',
    borderRadius: 12,
    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    padding: 20,
    border: '1px solid #e5e7eb',
    ...style
  }}>
    {children}
  </div>
);

const Quizzes = ({ planId: propPlanId, monthIndex: propMonthIndex, day: propDay, embedded = false, onSubmitted }) => {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [quizStatus, setQuizStatus] = useState(null);
  const [showResults, setShowResults] = useState(false);
  
  const location = useLocation();
  const navigate = useNavigate();

  // Allow reading planId, month, day from query string when used as a full page
  const searchParams = new URLSearchParams(location.search);
  const qsPlanId = searchParams.get('planId');
  const qsMonth = searchParams.get('month');
  const qsDay = searchParams.get('day');
  const planId = propPlanId || (qsPlanId ? parseInt(qsPlanId, 10) : null);
  const monthIndex = propMonthIndex || (qsMonth ? parseInt(qsMonth, 10) : null);
  const day = propDay || (qsDay ? parseInt(qsDay, 10) : null);

  const loadQuiz = async () => {
    setError('');
    setLoading(true);
    try {
      const data = await authenticatedFetch(`/quiz/${planId}/${monthIndex}/${day}`);
      
      if (!data.questions || data.questions.length === 0) {
        setError('Quiz has no questions. Please click "Generate Quiz" to create a new quiz.');
        setQuiz(null);
      } else {
        setQuiz(data);
        setAnswers(new Array(data.questions.length).fill(null));
      }
    } catch (e) {
      console.error('Error loading quiz:', e);
      setError('Quiz not found. Click "Generate Quiz" to create one.');
    } finally {
      setLoading(false);
    }
  };

  const loadQuizStatus = async () => {
    if (!planId || !monthIndex || !day) return;
    
    try {
      const status = await authenticatedFetch(`/quiz/${planId}/${monthIndex}/${day}/status`);
      setQuizStatus(status);
    } catch (e) {
      console.error('Error loading quiz status:', e);
    }
  };

  const generateQuiz = async () => {
    setError('');
    setLoading(true);
    try {
      const endpoint = `/quiz/${planId}/${monthIndex}/${day}/generate`;
      const g = await authenticatedFetch(endpoint, { method: 'POST' });
      
      if (!g.questions || g.questions.length === 0) {
        setError('Failed to generate quiz questions. Please try again or contact support.');
        setQuiz(null);
      } else {
        setQuiz(g);
        setAnswers(new Array(g.questions.length).fill(null));
        setResult(null);
        setShowResults(false);
        
        // Show success message
        if (!embedded) {
          alert(`🎯 Quiz generated successfully with ${g.questions.length} questions!\n\nComplete the quiz with a score of at least ${g.required_score}% to mark this day as completed and unlock the next day.`);
        }
      }
    } catch (e) {
      console.error('Error generating quiz:', e);
      setError(e.message || 'Failed to generate quiz. Please ensure you\'ve completed the day\'s learning material before generating a quiz.');
    } finally {
      setLoading(false);
    }
  };
  
  const regenerateQuiz = async () => {
    setError('');
    setLoading(true);
    try {
      const endpoint = `/quiz/${planId}/${monthIndex}/${day}/regenerate`;
      const g = await authenticatedFetch(endpoint, { method: 'POST' });
      
      if (!g.questions || g.questions.length === 0) {
        setError('Failed to regenerate quiz questions. Please try again or contact support.');
        setQuiz(null);
      } else {
        setQuiz(g);
        setAnswers(new Array(g.questions.length).fill(null));
        setResult(null);
        setShowResults(false);
        
        if (!embedded) {
          alert(`🔄 Quiz regenerated with ${g.questions.length} new questions!\n\nComplete the quiz with a score of at least ${g.required_score}% to mark this day as completed.`);
        }
      }
    } catch (e) {
      console.error('Error regenerating quiz:', e);
      setError(e.message || 'Failed to regenerate quiz. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    // Check if all questions are answered
    const unansweredCount = answers.filter(a => a === null).length;
    if (unansweredCount > 0) {
      alert(`Please answer all ${unansweredCount} remaining questions before submitting.`);
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setShowResults(false);
    
    try {
      const res = await authenticatedFetch(`/quiz/${planId}/${monthIndex}/${day}/submit`, {
        method: 'POST',
        body: JSON.stringify(answers.map(a => (a == null ? -1 : a)))
      });
      
      setResult(res);
      setShowResults(true);
      
      // Call the onSubmitted callback with the result
      if (typeof onSubmitted === 'function') {
        try { 
          onSubmitted(res); 
        } catch (callbackError) {
          console.error('Error in onSubmitted callback:', callbackError);
        }
      }
      
      // Show appropriate message based on result
      if (res.passed) {
        console.log('Quiz passed with score:', res.score);
        if (res.day_completed && !embedded) {
          alert(`🎉 Congratulations! Day ${day} completed with ${res.score}% score!\n\nYou can now proceed to the next day in your learning plan.`);
        }
      } else {
        console.log('Quiz not passed. Score:', res.score, 'Required:', res.required_score);
      }
    } catch (e) {
      console.error('Error submitting quiz:', e);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const resetQuiz = () => {
    setAnswers(new Array(quiz.questions.length).fill(null));
    setResult(null);
    setShowResults(false);
  };

  const goToNextDay = () => {
    if (result?.next_day) {
      const next = result.next_day;
      navigate(`/learning-plans/${planId}/month/${next.month_index}/day/${next.day_number}`);
    }
  };

  useEffect(() => { 
    if (planId && monthIndex && day) {
      // Ensure sidebar quiz dashboard is visible when visiting quizzes directly
      // and handle query params to pre-select the target quiz
      loadQuiz();
      loadQuizStatus();
    }
  }, [planId, monthIndex, day]);

  const renderQuizStatus = () => {
    if (!quizStatus) return null;

    const statusConfig = {
      'not_generated': { color: '#f59e0b', icon: '📝', text: 'Quiz not yet generated' },
      'not_attempted': { color: '#3b82f6', icon: '🎯', text: 'Ready to take' },
      'failed': { color: '#ef4444', icon: '❌', text: 'Previous attempts failed' },
      'completed': { color: '#10b981', icon: '✅', text: 'Quiz completed' }
    };

    const config = statusConfig[quizStatus.status] || statusConfig.not_generated;

    return (
      <div style={{ 
        padding: '12px 16px', 
        background: `${config.color}15`, 
        border: `1px solid ${config.color}30`,
        borderRadius: 8,
        marginBottom: 16,
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }}>
        <span style={{ fontSize: 18 }}>{config.icon}</span>
        <div>
          <div style={{ fontWeight: 600, color: config.color }}>{config.text}</div>
          {quizStatus.message && (
            <div style={{ fontSize: 14, color: '#6b7280', marginTop: 2 }}>
              {quizStatus.message}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderQuizContent = () => {
    if (!quiz) return null;

    return (
      <div>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: 20,
          padding: '16px 20px',
          background: '#f8fafc',
          borderRadius: 8,
          border: '1px solid #e2e8f0'
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16, color: '#1f2937' }}>{quiz.title}</div>
            <div style={{ color: '#6b7280', fontSize: 14, marginTop: 4 }}>
              Pass ≥ {quiz.required_score}% • {quiz.questions.length} questions
            </div>
          </div>
          
          {!result && (
            <div style={{ display: 'flex', gap: 8 }}>
              <button 
                onClick={regenerateQuiz}
                disabled={loading}
                style={{ 
                  padding: '8px 16px', 
                  borderRadius: 6, 
                  border: '1px solid #d1d5db', 
                  background: '#fff',
                  color: '#374151',
                  cursor: 'pointer',
                  fontSize: 14
                }}
              >
                🔄 Regenerate
              </button>
            </div>
          )}
        </div>

        {quiz.questions.map((q, qi) => (
          <QuizCard key={qi} style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 8, 
                marginBottom: 8 
              }}>
                <span style={{ 
                  background: '#4f8cff', 
                  color: '#fff', 
                  padding: '4px 8px', 
                  borderRadius: '50%', 
                  fontSize: 12, 
                  fontWeight: 600,
                  minWidth: 24,
                  textAlign: 'center'
                }}>
                  {qi + 1}
                </span>
                <span style={{ fontWeight: 600, fontSize: 16, color: '#1f2937' }}>
                  {q.question}
                </span>
              </div>
              
              <div style={{ display: 'grid', gap: 8, marginLeft: 32 }}>
                {q.options.map((opt, oi) => (
                  <label key={oi} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 12,
                    padding: '12px 16px',
                    border: '2px solid #e5e7eb',
                    borderRadius: 8,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    background: answers[qi] === oi ? '#f0f9ff' : '#fff',
                    borderColor: answers[qi] === oi ? '#4f8cff' : '#e5e7eb'
                  }}>
                    <input 
                      type="radio" 
                      name={`q-${qi}`} 
                      checked={answers[qi] === oi} 
                      onChange={() => {
                        const next = [...answers]; 
                        next[qi] = oi; 
                        setAnswers(next);
                      }}
                      style={{ margin: 0 }}
                    />
                    <span style={{ 
                      color: answers[qi] === oi ? '#1e40af' : '#374151',
                      fontWeight: answers[qi] === oi ? 600 : 400
                    }}>
                      {opt}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </QuizCard>
        ))}

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24 }}>
          {!result && (
            <>
              <button 
                onClick={resetQuiz}
                style={{ 
                  padding: '12px 24px', 
                  borderRadius: 8, 
                  border: '1px solid #d1d5db', 
                  background: '#fff',
                  color: '#374151',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                🔄 Reset Quiz
              </button>
              <button 
                onClick={submit} 
                disabled={loading || answers.some(a => a === null)}
                style={{ 
                  padding: '12px 24px', 
                  borderRadius: 8, 
                  border: 'none', 
                  background: answers.some(a => a === null) ? '#9ca3af' : '#4f8cff', 
                  color: '#fff',
                  fontWeight: 600,
                  cursor: answers.some(a => a === null) ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Submitting...' : '📝 Submit Quiz'}
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderResults = () => {
    if (!result || !showResults) return null;

    return (
      <QuizCard style={{ 
        background: result.passed ? '#f0fdf4' : '#fff7ed',
        border: result.passed ? '2px solid #a7f3d0' : '2px solid #fed7aa'
      }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>
            {result.passed ? '🎉' : '📚'}
          </div>
          <h2 style={{ 
            fontSize: 24, 
            fontWeight: 700, 
            color: result.passed ? '#166534' : '#9a3412',
            marginBottom: 8
          }}>
            {result.passed ? 'Quiz Passed!' : 'Quiz Not Passed'}
          </h2>
          <div style={{ 
            fontSize: 18, 
            color: result.passed ? '#047857' : '#b45309',
            marginBottom: 16
          }}>
            Score: {result.score}% • Required: {result.required_score}%
          </div>
          
          {result.passed && (
            <div style={{ 
              padding: '12px 20px', 
              background: '#dcfce7', 
              borderRadius: 8,
              border: '1px solid #a7f3d0',
              marginBottom: 20
            }}>
              <div style={{ fontWeight: 600, color: '#166534' }}>
                🎯 Day {day} completed successfully!
              </div>
              <div style={{ color: '#047857', marginTop: 4 }}>
                You can now proceed to the next day in your learning plan.
              </div>
            </div>
          )}
        </div>

        {result.question_results && (
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>Question Results</h3>
            <div style={{ display: 'grid', gap: 12 }}>
              {result.question_results.map((qr, idx) => (
                <div key={idx} style={{ 
                  padding: '12px 16px',
                  background: qr.is_correct ? '#f0fdf4' : '#fef2f2',
                  border: `1px solid ${qr.is_correct ? '#a7f3d0' : '#fecaca'}`,
                  borderRadius: 8
                }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 8, 
                    marginBottom: 8 
                  }}>
                    <span style={{ fontSize: 18 }}>
                      {qr.is_correct ? '✅' : '❌'}
                    </span>
                    <span style={{ fontWeight: 600, color: '#374151' }}>
                      Question {idx + 1}
                    </span>
                  </div>
                  <div style={{ fontSize: 14, color: '#6b7280' }}>
                    {qr.explanation || 'No explanation available'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          {result.passed && result.next_day && (
            <button 
              onClick={goToNextDay}
              style={{ 
                padding: '12px 24px', 
                borderRadius: 8, 
                border: 'none', 
                background: '#10b981', 
                color: '#fff',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              🚀 Continue to Next Day
            </button>
          )}
          
          {!result.passed && (
            <button 
              onClick={regenerateQuiz}
              style={{ 
                padding: '12px 24px', 
                borderRadius: 8, 
                border: 'none', 
                background: '#4f8cff', 
                color: '#fff',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              🔄 Try New Quiz
            </button>
          )}
          
          <button 
            onClick={() => setShowResults(false)}
            style={{ 
              padding: '12px 24px', 
              borderRadius: 8, 
              border: '1px solid #d1d5db', 
              background: '#fff',
              color: '#374151',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {result.passed ? '📊 View Quiz' : '📝 Retake Quiz'}
          </button>
        </div>
      </QuizCard>
    );
  };

  const content = (
    <div style={{ maxWidth: embedded ? '100%' : 900, margin: embedded ? '0' : '0 auto', padding: embedded ? 0 : 24 }}>
      {!embedded && (
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ marginBottom: 8, fontSize: 28, fontWeight: 800 }}>📝 Quiz</h1>
          <p style={{ color: '#6b7280', fontSize: 16 }}>
            Test your knowledge and track your progress
          </p>
        </div>
      )}

      {error && (
        <QuizCard style={{ 
          background: '#fee2e2', 
          border: '1px solid #fecaca',
          marginBottom: 16
        }}>
          <div style={{ color: '#7f1d1d', marginBottom: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>❌ Error</div>
            <div>{error}</div>
          </div>
          {error.includes('not found') && (
            <button 
              onClick={generateQuiz} 
              style={{ 
                padding: '8px 16px', 
                borderRadius: 6, 
                border: 'none', 
                background: '#4f8cff', 
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              🚀 Generate Quiz
            </button>
          )}
        </QuizCard>
      )}

      {loading && (
        <QuizCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center', padding: '40px' }}>
            <div style={{ 
              width: 24, 
              height: 24, 
              border: '3px solid #e5e7eb', 
              borderTop: '3px solid #4f8cff', 
              borderRadius: '50%', 
              animation: 'spin 1s linear infinite' 
            }}></div>
            <span>Loading quiz...</span>
          </div>
        </QuizCard>
      )}

      {renderQuizStatus()}
      {renderQuizContent()}
      {renderResults()}

      {!quiz && !loading && !error && (
        <QuizCard style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📝</div>
          <div style={{ marginBottom: 8, fontSize: 18, fontWeight: 600 }}>No quiz available</div>
          <div style={{ color: '#6b7280', marginBottom: 20 }}>
            Generate a quiz to test your knowledge for this day
          </div>
          <button 
            onClick={generateQuiz}
            style={{ 
              padding: '12px 24px', 
              borderRadius: 8, 
              border: 'none', 
              background: '#4f8cff', 
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            🚀 Generate Quiz
          </button>
        </QuizCard>
      )}
    </div>
  );
  
  if (!planId || !monthIndex || !day) {
    return embedded ? (
      <div style={{ padding: 16, textAlign: 'center', color: '#6b7280' }}>
        Select a day from Learning Plans to take the quiz.
      </div>
    ) : (
      <Layout>
        <div style={{ padding: 24, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📝</div>
          <h2>Quiz Section</h2>
          <p style={{ color: '#6b7280' }}>
            Select a day from Learning Plans to take the quiz.
          </p>
        </div>
      </Layout>
    );
  }

  return embedded ? content : <Layout>{content}</Layout>;
};

export default Quizzes;