import React, { useEffect, useState, useCallback } from 'react';
import Layout from './Layout';
import Quizzes from './Quizzes';
import { authenticatedFetch } from '../api';
import { useNavigate, useParams, useLocation } from 'react-router-dom';

const Card = ({ children, style, onClick }) => (
  <div onClick={onClick} style={{
    background: 'white',
    borderRadius: 16,
    boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
    padding: 24,
    ...style
  }}>
    {children}
  </div>
);

const ProgressBar = ({ completed, total, label, color = '#10b981' }) => (
  <div style={{ marginBottom: 12 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
      <span style={{ fontSize: 14, color: '#6b7280' }}>{label}</span>
      <span style={{ fontSize: 14, color: '#6b7280' }}>{completed}/{total}</span>
    </div>
    <div style={{ 
      width: '100%', 
      height: 8, 
      backgroundColor: '#e5e7eb', 
      borderRadius: 4,
      overflow: 'hidden'
    }}>
      <div style={{
        width: `${(completed / total) * 100}%`,
        height: '100%',
        backgroundColor: color,
        transition: 'width 0.3s ease'
      }} />
    </div>
  </div>
);

const NavigationBreadcrumb = ({ plan, monthIndex, day, onNavigate }) => (
  <div style={{ 
    display: 'flex', 
    alignItems: 'center', 
    gap: 8, 
    marginBottom: 20,
    padding: '12px 16px',
    background: '#f9fafb',
    borderRadius: 8,
    border: '1px solid #e5e7eb'
  }}>
    <button 
      onClick={() => onNavigate('plans')}
      style={{ 
        padding: '6px 12px', 
        borderRadius: 6, 
        border: '1px solid #d1d5db', 
        background: '#fff',
        color: '#374151',
        fontSize: 14,
        cursor: 'pointer'
      }}
    >
      📚 Learning Plans
    </button>
    
    {plan && (
      <>
        <span style={{ color: '#9ca3af' }}>→</span>
        <button 
          onClick={() => onNavigate('months', plan.id)}
          style={{ 
            padding: '6px 12px', 
            borderRadius: 6, 
            border: '1px solid #d1d5db', 
            background: '#fff',
            color: '#374151',
            fontSize: 14,
            cursor: 'pointer'
          }}
        >
          {plan.title}
        </button>
      </>
    )}
    
    {monthIndex && (
      <>
        <span style={{ color: '#9ca3af' }}>→</span>
        <button 
          onClick={() => onNavigate('month', plan.id, monthIndex)}
          style={{ 
            padding: '6px 12px', 
            borderRadius: 6, 
            border: '1px solid #d1d5db', 
            background: '#fff',
            color: '#374151',
            fontSize: 14,
            cursor: 'pointer'
          }}
        >
          Month {monthIndex}
        </button>
      </>
    )}
    
    {day && (
      <>
        <span style={{ color: '#9ca3af' }}>→</span>
        <span style={{ 
          padding: '6px 12px', 
          borderRadius: 6, 
          background: '#4f8cff', 
          color: '#fff',
          fontSize: 14
        }}>
          Day {day}
        </span>
      </>
    )}
  </div>
);

const LearningPlans = () => {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [starting, setStarting] = useState(false);
  const [currentPosition, setCurrentPosition] = useState(null);
  const [viewMode, setViewMode] = useState('plans'); // 'plans', 'months', 'month', 'day'
  const [selectedMonthIndex, setSelectedMonthIndex] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  
  const navigate = useNavigate();
  const params = useParams();
  const location = useLocation();

  // Initialize from URL params
  useEffect(() => {
    if (params.planId && params.monthIndex && params.day) {
      setViewMode('day');
      setSelectedMonthIndex(parseInt(params.monthIndex));
      setSelectedDay(parseInt(params.day));
    } else if (params.planId && params.monthIndex) {
      setViewMode('month');
      setSelectedMonthIndex(parseInt(params.monthIndex));
    } else if (params.planId) {
      setViewMode('months');
    } else {
      setViewMode('plans');
    }
  }, [params]);

  // Fetch user's current learning position
  const fetchCurrentPosition = async () => {
    try {
      const position = await authenticatedFetch('/user/current-position');
      setCurrentPosition(position);
      return position;
    } catch (e) {
      console.error('Error fetching current position:', e);
      // If no position exists, that's okay - return empty position
      const emptyPosition = {
        current_plan_id: null,
        current_month_index: null,
        current_day: null
      };
      setCurrentPosition(emptyPosition);
      return emptyPosition;
    }
  };

  const loadPlan = useCallback(async (planId = null) => {
    try {
      const targetPlanId = planId || params.planId;
      let data = null;
      if (targetPlanId) {
        data = await authenticatedFetch(`/learning-plan/${targetPlanId}`);
      } else {
        // Try to fetch the current user's plan when no ID in URL
        try {
          data = await authenticatedFetch(`/learning-plan`);
        } catch (err) {
          const msg = String(err?.message || '').toLowerCase();
          if (msg.includes('404') || msg.includes('not found')) {
            return null;
          }
          throw err;
        }
      }
      setPlan(data);
      return data;
    } catch (e) {
      console.error('Error loading plan:', e);
      const msg = String(e?.message || '').toLowerCase();
      if (msg.includes('404') || msg.includes('not found')) {
        // Plan not found - return null instead of throwing
      return null;
    }
      throw e; // Re-throw other errors
    }
  }, [params.planId]);

  const refreshPlan = async () => {
    if (plan) {
      await loadPlan(plan.id);
    }
  };

  const generatePlan = async () => {
    setError('');
    setLoading(true);
    try {
      const data = await authenticatedFetch('/learning-plan/generate', { method: 'POST' });
      setPlan(data);
      setViewMode('months');
      
      // Show success message
      alert(`🎉 Learning plan generated successfully!\n\nPlan: ${data.title}\nDuration: ${data.total_years} year(s)\nMonths: ${data.plan?.months?.length || 0}\n\nYour first month is now active and ready to start!`);
      
      // Navigate to the months view
      navigate(`/learning-plans/${data.id}`);
    } catch (e) {
      setError(e.message);
      alert(`❌ Error generating learning plan: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startMonth = async (monthIndex) => {
    setStarting(true);
    try {
        const data = await authenticatedFetch(`/learning-plan/${plan.id}/start-month/${monthIndex}`, { method: 'POST' });
        
      // Show success message
      alert(`🚀 Month ${monthIndex} started successfully!\n\n30 days have been generated for this month.\nYou can now start learning day by day!`);
      
      await refreshPlan();
      setSelectedMonthIndex(monthIndex);
      setViewMode('month');
      
      // Navigate to the month view
      navigate(`/learning-plans/${plan.id}/month/${monthIndex}`);
    } catch (e) {
      setError(e.message);
      alert(`❌ Error starting month: ${e.message}`);
    } finally {
      setStarting(false);
    }
  };

  const startDay = async (monthIndex, dayNum) => {
    try {
      const response = await authenticatedFetch(`/learning-plan/${plan.id}/month/${monthIndex}/day/${dayNum}/start`, { method: 'POST' });
      
      // Show success message
      alert(`📚 Day ${dayNum} started successfully!\n\nStudy content has been generated for this day.\nComplete the learning material and then take the quiz to mark this day as complete!`);
      
      await refreshPlan();
      setSelectedMonthIndex(monthIndex);
      setSelectedDay(dayNum);
      setViewMode('day');
      
      // Navigate to the day view
      navigate(`/learning-plans/${plan.id}/month/${monthIndex}/day/${dayNum}`);
    } catch (e) {
      console.error('Error starting day:', e);
      alert(`❌ Error starting day: ${e.message}`);
    }
  };

  const handleNavigation = (mode, planId = null, monthIndex = null) => {
    setViewMode(mode);
    if (mode === 'plans') {
      setSelectedMonthIndex(null);
          setSelectedDay(null);
      navigate('/learning-plans');
    } else if (mode === 'months') {
      setSelectedMonthIndex(null);
      setSelectedDay(null);
      navigate(`/learning-plans/${planId}`);
    } else if (mode === 'month') {
      setSelectedDay(null);
      navigate(`/learning-plans/${planId}/month/${monthIndex}`);
    }
  };

  const renderPlansView = () => {
    return (
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, color: '#111827', marginBottom: 16 }}>
            🎓 Your Learning Journey
          </h1>
          <p style={{ fontSize: 18, color: '#6b7280', maxWidth: 600, margin: '0 auto' }}>
            Start your personalized learning adventure with AI-generated content tailored to your goals
          </p>
        </div>

        {plan ? (
          // Show existing plan
      <Card>
            <div style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <span style={{ fontSize: 24 }}>📚</span>
                <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600, color: '#111827' }}>
                  {plan.title}
                </h2>
        </div>

            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: 16, 
                marginBottom: 24 
              }}>
                <div style={{ textAlign: 'center', padding: '16px', background: '#f0f9ff', borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: '#1e40af' }}>
                    {plan.total_years || 1}
            </div>
                  <div style={{ color: '#6b7280' }}>Years</div>
          </div>
                <div style={{ textAlign: 'center', padding: '16px', background: '#f0fdf4', borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: '#166534' }}>
                    {plan.plan?.months?.length || 0}
            </div>
                  <div style={{ color: '#6b7280' }}>Months</div>
                    </div>
                <div style={{ textAlign: 'center', padding: '16px', background: '#fff7ed', borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: '#92400e' }}>
                    {plan.plan?.months?.length * 30 || 0}
                </div>
                  <div style={{ color: '#6b7280' }}>Days</div>
                </div>
            </div>
              
                <button 
                onClick={() => setViewMode('months')}
                  style={{ 
                  width: '100%',
                  padding: '12px 24px', 
                    borderRadius: 8, 
                    border: 'none', 
                  background: '#10b981', 
                    color: '#fff',
                  fontSize: 16,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                🚀 Continue Learning
                </button>
              </div>
          </Card>
        ) : (
          // Show generate plan option
          <Card>
            <div style={{ padding: 40, textAlign: 'center' }}>
              <div style={{ fontSize: 64, marginBottom: 24 }}>🎯</div>
              <h2 style={{ fontSize: 28, fontWeight: 600, color: '#111827', marginBottom: 16 }}>
                No Learning Plan Yet
              </h2>
              <p style={{ fontSize: 16, color: '#6b7280', marginBottom: 32, maxWidth: 500, margin: '0 auto 32px' }}>
                Ready to start your learning journey? Generate a personalized plan based on your goals, skills, and time commitment.
              </p>
              
              <button 
                onClick={generatePlan}
                disabled={loading}
                  style={{ 
                  padding: '16px 32px', 
                  borderRadius: 12, 
                  border: 'none', 
                  background: '#4f8cff', 
                  color: '#fff',
                  fontSize: 18,
                    fontWeight: 600,
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.7 : 1,
                  transition: 'all 0.2s ease'
                }}
              >
                {loading ? '🔄 Generating...' : '🚀 Generate My Learning Plan'}
              </button>
              
              <div style={{ marginTop: 24, fontSize: 14, color: '#9ca3af' }}>
                ✨ AI-powered • Personalized • Adaptive
              </div>
            </div>
          </Card>
          )}
        </div>
    );
  };

  const renderMonthsView = () => {
    if (!plan) return null;
    
    const months = plan.plan?.months || [];
    const progress = {
      totalMonths: months.length,
      completedMonths: months.filter(m => m.status === 'completed').length,
      totalDays: months.reduce((sum, m) => sum + (m.days?.length || 0), 0),
      completedDays: months.reduce((sum, m) => sum + (m.days?.filter(d => d.completed).length || 0), 0)
    };

    return (
      <div style={{ display: 'grid', gap: 16 }}>
        <NavigationBreadcrumb 
          plan={plan} 
          onNavigate={handleNavigation} 
        />
        
        {/* Header and Progress */}
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
              <div style={{ color: '#6b7280', fontSize: 14 }}>{plan.total_years} year plan</div>
              <h2 style={{ margin: '4px 0', fontSize: 28, fontWeight: 800 }}>{plan.title}</h2>
              <div style={{ marginTop: 16 }}>
                <ProgressBar 
                  completed={progress.completedMonths} 
                  total={progress.totalMonths} 
                  label="Months Completed" 
                  color="#4f8cff"
                />
                <ProgressBar 
                  completed={progress.completedDays} 
                  total={progress.totalDays} 
                  label="Days Completed" 
                  color="#10b981"
                />
          </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
                  <button
                onClick={refreshPlan}
                style={{ 
                  padding: '8px 16px', 
                  borderRadius: 8, 
                  border: '1px solid #d1d5db', 
                  background: '#fff',
                  color: '#374151',
                  cursor: 'pointer'
                }}
              >
                🔄 Refresh
                  </button>
              </div>
          </div>
        </Card>

        {/* Months Grid */}
        <div style={{ display: 'grid', gap: 16 }}>
          {months.map((month, idx) => {
            const monthIndex = idx + 1;
            const days = month.days || [];
            const completedDays = days.filter(d => d.completed).length;
            const isActive = month.status === 'active';
            const isCompleted = month.status === 'completed';
            const isLocked = month.status === 'locked';
            
            return (
              <Card key={monthIndex} style={{ 
                border: isActive ? '2px solid #4f8cff' : '1px solid #e5e7eb',
                background: isActive ? '#f0f9ff' : 'white'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: 12, 
                        fontSize: 12, 
                        fontWeight: 600,
                        background: isCompleted ? '#dcfce7' : isActive ? '#dbeafe' : '#f3f4f6',
                        color: isCompleted ? '#166534' : isActive ? '#1e40af' : '#6b7280'
                      }}>
                        {isCompleted ? '✅ Completed' : isActive ? '🔄 Active' : '🔒 Locked'}
                      </span>
                      <span style={{ color: '#6b7280', fontSize: 14 }}>Month {monthIndex}</span>
                  </div>
                  
                    <h3 style={{ margin: '4px 0', fontSize: 20, fontWeight: 700 }}>{month.title}</h3>
                    <p style={{ color: '#4b5563', marginBottom: 12, lineHeight: 1.5 }}>
                      {month.description || 'No description available'}
                    </p>
                    
                    {isActive && (
                      <div style={{ marginBottom: 16 }}>
                        <ProgressBar 
                          completed={completedDays} 
                          total={days.length} 
                          label="Days Completed" 
                          color="#10b981"
                        />
                    </div>
                  )}
                  
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {isLocked && monthIndex === 1 && (
                      <button 
                          onClick={() => startMonth(monthIndex)}
                          disabled={starting}
                        style={{ 
                            padding: '10px 16px', 
                          borderRadius: 8, 
                            border: 'none', 
                            background: '#10b981', 
                            color: '#fff',
                          fontWeight: 600,
                            cursor: 'pointer'
                        }}
                      >
                          {starting ? 'Starting...' : '🚀 Start Month'}
                      </button>
                      )}
                      
                      {isLocked && monthIndex > 1 && (
                        <div style={{ 
                          padding: '8px 12px', 
                          background: '#f3f4f6', 
                            borderRadius: 6,
                          color: '#6b7280',
                            fontSize: 12
                        }}>
                          Complete previous months first
                        </div>
                      )}
                      
                      {isActive && (
                        <button 
                          onClick={() => handleNavigation('month', plan.id, monthIndex)}
                          style={{ 
                            padding: '10px 16px', 
                            borderRadius: 8, 
                            border: '1px solid #4f8cff', 
                            background: '#fff',
                            color: '#4f8cff',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          📅 View Days
                        </button>
                      )}
                      
                      {isCompleted && (
              <button 
                          onClick={() => handleNavigation('month', plan.id, monthIndex)}
                style={{ 
                            padding: '10px 16px', 
                            borderRadius: 8, 
                            border: '1px solid #10b981', 
                            background: '#fff',
                            color: '#10b981',
                            fontWeight: 600,
                            cursor: 'pointer'
                          }}
                        >
                          📊 Review Progress
              </button>
                      )}
            </div>
          </div>
            </div>
          </Card>
            );
          })}
                  </div>
                </div>
    );
  };

  const renderMonthView = () => {
    if (!plan || !selectedMonthIndex) return null;
    
    const month = plan.plan?.months?.[selectedMonthIndex - 1];
    if (!month) return null;
    
    const days = month.days || [];
                  const completedDays = days.filter(d => d.completed).length;
    const isActive = month.status === 'active';
    
                  return (
      <div style={{ display: 'grid', gap: 16 }}>
        <NavigationBreadcrumb 
          plan={plan} 
          monthIndex={selectedMonthIndex}
          onNavigate={handleNavigation} 
        />
        
        {/* Month Header */}
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ color: '#6b7280', fontSize: 14 }}>Month {selectedMonthIndex}</div>
              <h2 style={{ margin: '4px 0', fontSize: 24, fontWeight: 700 }}>{month.title}</h2>
              <p style={{ color: '#4b5563', marginBottom: 16, lineHeight: 1.5 }}>
                {month.description || 'No description available'}
              </p>
              
              {isActive && (
                            <ProgressBar 
                              completed={completedDays} 
                              total={days.length} 
                              label="Days Completed" 
                  color="#10b981"
                            />
              )}
                      </div>

            <div style={{ display: 'flex', gap: 8 }}>
                              <button 
                onClick={() => handleNavigation('months', plan.id)}
                                style={{ 
                                  padding: '8px 16px', 
                                  borderRadius: 8, 
                  border: '1px solid #d1d5db', 
                  background: '#fff',
                  color: '#374151',
                                  cursor: 'pointer'
                                }}
                              >
                ← Back to Months
                              </button>
                            </div>
                                    </div>
        </Card>

        {/* Days Grid */}
        {isActive ? (
          <div style={{ display: 'grid', gap: 12 }}>
            {days.map((day, idx) => {
              const dayNum = idx + 1;
              const isCompleted = day.completed;
              const isStarted = day.started_at;
              
              return (
                <Card key={dayNum} style={{ 
                  border: isCompleted ? '2px solid #10b981' : '1px solid #e5e7eb',
                  background: isCompleted ? '#f0fdf4' : 'white'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                      <span style={{ 
                                        padding: '4px 8px', 
                          borderRadius: 12, 
                                        fontSize: 12, 
                          fontWeight: 600,
                          background: isCompleted ? '#dcfce7' : isStarted ? '#dbeafe' : '#f3f4f6',
                          color: isCompleted ? '#166534' : isStarted ? '#1e40af' : '#6b7280'
                                      }}>
                          {isCompleted ? '✅ Completed' : isStarted ? '🔄 Started' : '📚 Ready'}
                                      </span>
                        <span style={{ color: '#6b7280', fontSize: 14 }}>Day {dayNum}</span>
                                  </div>
                                  
                      <h4 style={{ margin: '4px 0', fontSize: 16, fontWeight: 600 }}>{day.concept}</h4>
                      <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 8 }}>
                        ⏱️ {day.time_estimate || 60} minutes
                      </p>
                      
                      {day.quiz_score && (
                                  <div style={{ 
                          padding: '8px 12px', 
                          background: '#f0f9ff', 
                          borderRadius: 6, 
                          border: '1px solid #dbeafe',
                          marginBottom: 12
                        }}>
                          <span style={{ color: '#1e40af', fontSize: 14 }}>
                            🎯 Quiz Score: {day.quiz_score}%
                          </span>
                                    </div>
                                  )}
                                  
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {!isStarted && (
                                      <button
                            onClick={() => startDay(selectedMonthIndex, dayNum)}
                            style={{ 
                              padding: '8px 16px', 
                              borderRadius: 8, 
                              border: 'none', 
                              background: '#4f8cff', 
                              color: '#fff',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            🚀 Start Day
                          </button>
                        )}
                        
                        {isStarted && !isCompleted && (
                          <button 
                            onClick={() => startDay(selectedMonthIndex, dayNum)}
                                        style={{ 
                              padding: '8px 16px', 
                                          borderRadius: 8, 
                              border: '1px solid #4f8cff', 
                                          background: '#fff',
                              color: '#4f8cff',
                                          fontWeight: 600,
                              cursor: 'pointer'
                                        }}
                                      >
                            📖 Continue Learning
                                      </button>
                        )}
                        
                        {isCompleted && (
                                      <button
                            onClick={() => startDay(selectedMonthIndex, dayNum)}
                                        style={{ 
                              padding: '8px 16px', 
                                          borderRadius: 8, 
                              border: '1px solid #10b981', 
                              background: '#fff',
                              color: '#10b981',
                                          fontWeight: 600,
                              cursor: 'pointer'
                                        }}
                                      >
                            📊 Review Day
                                      </button>
                                  )}
                                </div>
                    </div>
                  </div>
                </Card>
                              );
                            })}
                          </div>
        ) : (
          <Card style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{ color: '#6b7280', marginBottom: 16 }}>
              This month is currently locked. Complete previous months to unlock it.
            </div>
          </Card>
        )}
                        </div>
                          );
  };

  const renderDayView = () => {
    if (!plan || !selectedMonthIndex || !selectedDay) return null;
    
    const month = plan.plan?.months?.[selectedMonthIndex - 1];
    if (!month) return null;
    
    const day = month.days?.[selectedDay - 1];
    if (!day) return null;
    
                          return (
      <div style={{ display: 'grid', gap: 16 }}>
        <NavigationBreadcrumb 
          plan={plan} 
          monthIndex={selectedMonthIndex}
          day={selectedDay}
          onNavigate={handleNavigation} 
        />
        
        {/* Day Header */}
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ color: '#6b7280', fontSize: 14 }}>
                Month {selectedMonthIndex} • Day {selectedDay}
                            </div>
              <h2 style={{ margin: '4px 0', fontSize: 24, fontWeight: 700 }}>{day.concept}</h2>
              <p style={{ color: '#6b7280', fontSize: 16, marginBottom: 16 }}>
                ⏱️ Estimated time: {day.time_estimate || 60} minutes
              </p>
              
              {day.completed && (
                <div style={{ 
                  padding: '12px 16px', 
                  background: '#f0fdf4', 
                  borderRadius: 8, 
                  border: '1px solid #a7f3d0',
                  marginBottom: 16
                }}>
                  <span style={{ color: '#166534', fontSize: 14, fontWeight: 600 }}>
                    ✅ Day completed! Quiz score: {day.quiz_score}%
                  </span>
                </div>
                                        )}
                                      </div>
            
            <div style={{ display: 'flex', gap: 8 }}>
              <button 
                onClick={() => handleNavigation('month', plan.id, selectedMonthIndex)}
                style={{ 
                  padding: '8px 16px', 
                  borderRadius: 8, 
                  border: '1px solid #d1d5db', 
                  background: '#fff',
                  color: '#374151',
                  cursor: 'pointer'
                }}
              >
                ← Back to Month
              </button>
            </div>
          </div>
        </Card>

        {/* Day Content */}
        <Card>
          <h3 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>Learning Content</h3>
          
          {day.detail ? (
            <div style={{ lineHeight: 1.6 }}>
              {day.detail.overview && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ marginBottom: 8, color: '#374151' }}>📖 Overview</h4>
                  <div style={{ 
                    color: '#4b5563', 
                    padding: '12px 16px',
                    background: '#f8fafc',
                    borderRadius: 8,
                    border: '1px solid #e2e8f0'
                  }}>
                    {day.detail.overview}
                  </div>
                                  </div>
                                )}
              
              {day.detail.learning_objectives && day.detail.learning_objectives.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ marginBottom: 8, color: '#374151' }}>🎯 Learning Objectives</h4>
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {day.detail.learning_objectives.map((obj, idx) => (
                      <li key={idx} style={{ marginBottom: 4, color: '#4b5563' }}>{obj}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
              
              {day.detail.sections && day.detail.sections.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ marginBottom: 8, color: '#374151' }}>📚 Study Plan</h4>
                  <div style={{ display: 'grid', gap: 12 }}>
                    {day.detail.sections.map((section, idx) => (
                      <div key={idx} style={{ 
                        padding: '16px',
                        background: '#f8fafc',
                        borderRadius: 8,
                        border: '1px solid #e2e8f0'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          marginBottom: 8
                        }}>
                          <h5 style={{ margin: 0, color: '#374151', fontWeight: 600 }}>{section.title}</h5>
                          <span style={{ 
                            padding: '4px 8px', 
                            background: '#dbeafe', 
                            color: '#1e40af',
                            borderRadius: 6,
                            fontSize: 12,
                            fontWeight: 600
                          }}>
                            ⏱️ {section.minutes} min
                          </span>
                              </div>
                        
                        {section.steps && section.steps.length > 0 && (
                          <ol style={{ margin: '8px 0 0 0', paddingLeft: 20, color: '#4b5563' }}>
                            {section.steps.map((step, stepIdx) => (
                              <li key={stepIdx} style={{ marginBottom: 4 }}>{step}</li>
                            ))}
                          </ol>
                        )}
                        
                        {section.focus_areas && section.focus_areas.length > 0 && (
                              <div style={{ marginTop: 12 }}>
                            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>Focus Areas:</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                              {section.focus_areas.map((area, areaIdx) => (
                                <span key={areaIdx} style={{ 
                                  padding: '2px 8px', 
                                  background: '#f0f9ff', 
                                  color: '#1e40af',
                                  borderRadius: 12,
                                  fontSize: 11
                                }}>
                                  {area}
                                </span>
                              ))}
                            </div>
                                  </div>
                                )}
                      </div>
                    ))}
                  </div>
                              </div>
                            )}
              
              {day.detail.resources && day.detail.resources.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ marginBottom: 8, color: '#374151' }}>🔗 Resources</h4>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {day.detail.resources.map((resource, idx) => (
                      <div key={idx} style={{ 
                        padding: '12px',
                        background: '#f0f9ff',
                        borderRadius: 6,
                        border: '1px solid #dbeafe'
                      }}>
                        <div style={{ fontWeight: 600, color: '#1e40af', marginBottom: 4 }}>
                          {resource.type}: {resource.title}
                        </div>
                        {resource.description && (
                          <div style={{ color: '#4b5563', fontSize: 14, marginBottom: 4 }}>
                            {resource.description}
                          </div>
                        )}
                        {resource.url && (
                          <a 
                            href={resource.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ 
                              color: '#4f8cff', 
                              textDecoration: 'none',
                              fontWeight: 600,
                              fontSize: 14
                            }}
                          >
                            🔗 Open Resource
                          </a>
                        )}
                            </div>
                    ))}
                          </div>
                        </div>
                      )}
              
              {day.detail.checklist && day.detail.checklist.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ marginBottom: 8, color: '#374151' }}>✅ Checklist</h4>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {day.detail.checklist.map((item, idx) => (
                      <div key={idx} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 8,
                        padding: '8px 12px',
                        background: '#f0fdf4',
                        borderRadius: 6,
                        border: '1px solid #a7f3d0'
                      }}>
                        <span style={{ color: '#10b981' }}>☐</span>
                        <span style={{ color: '#047857' }}>{item}</span>
                    </div>
                    ))}
                  </div>
                </div>
            )}
          </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: '#6b7280' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>📚</div>
              <div style={{ marginBottom: 8 }}>Day content not yet generated</div>
              <div style={{ marginBottom: 16, fontSize: 14 }}>
                Click "Start Day" to generate detailed learning content for this day
              </div>
              <button 
                onClick={() => startDay(selectedMonthIndex, selectedDay)}
                style={{ 
                  padding: '10px 20px', 
                  borderRadius: 8, 
                  border: 'none', 
                  background: '#4f8cff', 
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                🚀 Start Day
              </button>
          </div>
        )}
        </Card>

        {/* Quiz Section - Redirect to Quizzes page */}
        <Card>
          <h3 style={{ marginBottom: 16, fontSize: 18, fontWeight: 600 }}>📝 Quiz</h3>
          <div style={{ color: '#6b7280', marginBottom: 12 }}>
            Take the quiz for this day to mark it complete and unlock the next day.
      </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => navigate(`/quizzes?planId=${plan.id}&month=${selectedMonthIndex}&day=${selectedDay}`)}
              style={{
                padding: '12px 16px',
                borderRadius: 8,
                border: 'none',
                background: '#4f8cff',
                color: '#fff',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              🚀 Take Quiz
            </button>
            <button
              onClick={() => navigate('/quizzes')}
              style={{
                padding: '12px 16px',
                borderRadius: 8,
                border: '1px solid #d1d5db',
                background: '#fff',
                color: '#374151',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              📋 Open Quizzes
            </button>
          </div>
        </Card>
      </div>
    );
  };

  // Load plan and current position
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // First, try to get current position
        const position = await fetchCurrentPosition();
        setCurrentPosition(position);
        
        // Then try to load existing plan
        try {
          const planData = await loadPlan();
          if (planData) {
            setPlan(planData);
            // Set view mode based on URL params or default to months
            if (params.planId && params.monthIndex && params.day) {
              setViewMode('day');
              setSelectedMonthIndex(parseInt(params.monthIndex));
              setSelectedDay(parseInt(params.day));
            } else if (params.planId && params.monthIndex) {
              setViewMode('month');
              setSelectedMonthIndex(parseInt(params.monthIndex));
            } else if (params.planId) {
              setViewMode('months');
            } else {
              setViewMode('months');
            }
          } else {
            // No plan exists - show plans view
            setViewMode('plans');
          }
        } catch (planError) {
          // Plan not found - show plans view
          console.log('No existing plan found, showing plans view');
          setViewMode('plans');
        }
      } catch (e) {
        console.error('Error loading data:', e);
        setError(e.message);
        // On error, show plans view
        setViewMode('plans');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div style={{ padding: 20, textAlign: 'center' }}>
          <div style={{ 
            width: 40, 
            height: 40, 
            border: '4px solid #e5e7eb', 
            borderTop: '4px solid #4f8cff', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <div style={{ fontSize: 18, color: '#6b7280' }}>Loading your learning journey...</div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div style={{ padding: 20, textAlign: 'center' }}>
          <div style={{ color: '#ef4444', marginBottom: 16, fontSize: 18 }}>❌ Error</div>
          <div style={{ color: '#6b7280', marginBottom: 20 }}>{error}</div>
          <button 
            onClick={() => window.location.reload()}
            style={{ 
              padding: '10px 20px', 
              borderRadius: 8, 
              border: 'none', 
              background: '#4f8cff', 
              color: '#fff',
              cursor: 'pointer'
            }}
          >
            🔄 Retry
          </button>
        </div>
      </Layout>
    );
  }

  // Render based on view mode
  if (viewMode === 'plans') {
    return (
      <Layout>
        <div style={{ padding: 20 }}>
          {renderPlansView()}
        </div>
      </Layout>
    );
  }

  if (viewMode === 'months') {
    return (
      <Layout>
        <div style={{ padding: 20 }}>
          {renderMonthsView()}
        </div>
      </Layout>
    );
  }

  if (viewMode === 'month') {
    return (
      <Layout>
        <div style={{ padding: 20 }}>
          {renderMonthView()}
        </div>
      </Layout>
    );
  }

  if (viewMode === 'day') {
    return (
      <Layout>
        <div style={{ padding: 20 }}>
          {renderDayView()}
        </div>
      </Layout>
    );
  }

  // Fallback - should never reach here
  return (
    <Layout>
      <div style={{ padding: 20, textAlign: 'center' }}>
        <div style={{ color: '#6b7280', fontSize: 18 }}>Something went wrong</div>
        <button 
          onClick={() => setViewMode('plans')}
          style={{ 
            padding: '10px 20px', 
            borderRadius: 8, 
            border: 'none', 
            background: '#4f8cff', 
            color: '#fff',
            cursor: 'pointer',
            marginTop: 16
          }}
        >
          🏠 Go Home
        </button>
      </div>
    </Layout>
  );
};

export default LearningPlans;