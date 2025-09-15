import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch, authenticatedFetch } from '../api';
import { FaGraduationCap, FaBullseye, FaStar, FaClock, FaArrowLeft, FaArrowRight } from 'react-icons/fa';

const OnboardingFlow = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    grade: '',
    career_goals: [],
    current_skills: [],
    time_commitment: '2 hours'
  });
  const [newGoal, setNewGoal] = useState('');
  const [newSkill, setNewSkill] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [setIsGoogleAuthenticated] = useState(false);
  const [showGoogleAuthCard, setShowGoogleAuthCard] = useState(false);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const navigate = useNavigate();

  // Check Google authentication status and existing onboarding data on component mount
  useEffect(() => {
    const checkAuthAndOnboarding = async () => {
      try {
        // First check if user has already completed onboarding
        try {
          await authenticatedFetch('/onboarding');
          // If we get onboarding data, user has already completed it
          setHasCompletedOnboarding(true);
          console.log('User has already completed onboarding, redirecting to dashboard');
          navigate('/dashboard');
          return;
        } catch (onboardingErr) {
          // If 404, user hasn't completed onboarding yet - this is expected
          if (onboardingErr.message.includes('404') || onboardingErr.message.includes('not found')) {
            console.log('User has not completed onboarding yet');
            setHasCompletedOnboarding(false);
          } else {
            console.log('Error checking onboarding:', onboardingErr.message);
            setHasCompletedOnboarding(false);
          }
        }

        // Then check Google authentication status
        const response = await authenticatedFetch('/auth/google/verify');
        setShowGoogleAuthCard(!response.is_google_authenticated);
      } catch (err) {
        console.log('Auth check failed:', err.message);
        setShowGoogleAuthCard(true);
      } finally {
        setCheckingAuth(false);
      }
    };

    checkAuthAndOnboarding();
  }, [navigate]);

  const handleGoogleAuth = async () => {
    try {
      const response = await apiFetch('/auth/google/url');
      localStorage.removeItem('token');
      localStorage.removeItem('google_user');
      window.location.href = response.auth_url;
    } catch (err) {
      setError(`Google authentication failed: ${err.message}`);
    }
  };

  const handleSkipGoogleAuth = () => {
    setShowGoogleAuthCard(false);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayChange = (field, value, action) => {
    setFormData(prev => ({
      ...prev,
      [field]: action === 'add' 
        ? [...prev[field], value]
        : prev[field].filter(item => item !== value)
    }));
  };

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, 5));
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleCompletion = async () => {
    setLoading(true);
    setError('');

    try {
      await authenticatedFetch('/onboarding', {
        method: 'POST',
        body: JSON.stringify(formData)
      });

      navigate('/dashboard');
    } catch (err) {
      setError(`Onboarding error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // If user has already completed onboarding, don't render anything (will redirect)
  if (hasCompletedOnboarding) {
    return null;
  }

  if (checkingAuth) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{
          background: 'white',
          padding: '40px',
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #4f8cff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p>Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show Google authentication card if user is not Google authenticated
  if (showGoogleAuthCard) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '20px'
      }}>
        <div style={{
          background: 'white',
          padding: '40px',
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
          width: '100%',
          maxWidth: '500px',
          textAlign: 'center'
        }}>
          <h2 style={{ color: '#333', marginBottom: '20px' }}>
            Connect Google Account
          </h2>
          
          <p style={{ color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
            To access advanced features like Gmail integration, Calendar sync, and YouTube learning, 
            you need to connect your Google account. This allows us to provide you with a personalized 
            learning experience.
          </p>

          {error && (
            <div style={{
              background: '#fee',
              color: '#c33',
              padding: '15px',
              borderRadius: '6px',
              marginBottom: '20px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <button
              onClick={handleGoogleAuth}
              style={{
                padding: '15px 30px',
                background: '#db4437',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px'
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Connect Google Account
            </button>

            <button
              onClick={handleSkipGoogleAuth}
              style={{
                padding: '12px 24px',
                background: 'transparent',
                color: '#666',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Skip for now (Limited features)
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main onboarding flow
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          background: '#f8f9fa',
          padding: '30px 40px 20px 40px',
          borderBottom: '1px solid #eee'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '15px'
          }}>
            <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#222', margin: 0 }}>
              Welcome to EduAI
            </h1>
            <span style={{ fontSize: '16px', color: '#666', fontWeight: '500' }}>
              Step {currentStep} of 5
            </span>
          </div>
          
          {/* Progress Bar */}
          <div style={{
            width: '100%',
            height: '8px',
            background: '#e9ecef',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${(currentStep / 5) * 100}%`,
              height: '100%',
              background: 'linear-gradient(90deg, #667eea, #764ba2)',
              transition: 'width 0.3s ease'
            }}></div>
          </div>
        </div>

        {/* Content */}
        <div style={{ padding: '40px' }}>
          {error && (
            <div style={{
              background: '#fee',
              color: '#c33',
              padding: '15px',
              borderRadius: '6px',
              marginBottom: '20px',
              fontSize: '14px'
            }}>
              {error}
            </div>
          )}

          {/* Step 1: Name */}
          {currentStep === 1 && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', color: '#8b5cf6', marginBottom: '20px' }}>
                <FaGraduationCap />
              </div>
              <h2 style={{ fontSize: '32px', fontWeight: '700', color: '#222', marginBottom: '15px' }}>
                Hi there! What's your name?
              </h2>
              <p style={{ fontSize: '16px', color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
                We'll create a personalized learning journey just for you. Let's start with your name so we can make this experience more personal.
              </p>
              
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                style={{
                  width: '100%',
                  maxWidth: '400px',
                  padding: '16px 20px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  fontSize: '18px',
                  textAlign: 'center',
                  boxSizing: 'border-box',
                  transition: 'border-color 0.3s ease'
                }}
                placeholder="Enter your name"
                onFocus={(e) => e.target.style.borderColor = '#4f8cff'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              />
              
              {formData.name && (
                <p style={{ fontSize: '16px', color: '#4f8cff', marginTop: '15px', fontWeight: '500' }}>
                  Nice to meet you, {formData.name}! 👋
                </p>
              )}
            </div>
          )}

          {/* Step 2: Grade/Level */}
          {currentStep === 2 && (
            <div style={{ textAlign: 'center' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#222', marginBottom: '15px' }}>
                Tell us about your studies
              </h2>
              <p style={{ fontSize: '16px', color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
                Select your current educational level so we can tailor content to your needs.
              </p>
              
              <select
                value={formData.grade}
                onChange={(e) => handleInputChange('grade', e.target.value)}
                style={{
                  width: '100%',
                  maxWidth: '400px',
                  padding: '16px 20px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  fontSize: '18px',
                  textAlign: 'center',
                  boxSizing: 'border-box',
                  transition: 'border-color 0.3s ease',
                  background: 'white'
                }}
                onFocus={(e) => e.target.style.borderColor = '#4f8cff'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              >
                <option value="">Select your grade/level</option>
                <option value="High School (9th-12th)">High School (9th-12th)</option>
                <option value="B.Tech 1st Year">B.Tech 1st Year</option>
                <option value="B.Tech 2nd Year">B.Tech 2nd Year</option>
                <option value="B.Tech 3rd Year">B.Tech 3rd Year</option>
                <option value="B.Tech 4th Year">B.Tech 4th Year</option>
                <option value="M.Tech 1st Year">M.Tech 1st Year</option>
                <option value="M.Tech 2nd Year">M.Tech 2nd Year</option>
                <option value="PhD">PhD</option>
                <option value="Working Professional">Working Professional</option>
                <option value="Other">Other</option>
              </select>
            </div>
          )}

          {/* Step 3: Career Goals */}
          {currentStep === 3 && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', color: '#8b5cf6', marginBottom: '20px' }}>
                <FaBullseye />
              </div>
              <h2 style={{ fontSize: '32px', fontWeight: '700', color: '#222', marginBottom: '15px' }}>
                What are your career goals?
              </h2>
              <p style={{ fontSize: '16px', color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
                Select one or more career paths you're interested in. We'll customize your learning plan accordingly.
              </p>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '15px',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                {[
                  { id: 'Data Scientist', icon: '📊', desc: 'Master ML, statistics, and data analysis' },
                  { id: 'GATE Cracker', icon: '🎯', desc: 'Ace the GATE examination' },
                  { id: 'Software Developer', icon: '💻', desc: 'Build amazing applications' },
                  { id: 'AI Engineer', icon: '🤖', desc: 'Create intelligent systems' },
                  { id: 'Product Manager', icon: '🚀', desc: 'Lead product development' },
                  { id: 'Researcher', icon: '🔬', desc: 'Advance scientific knowledge' }
                ].map(goal => (
                  <div
                    key={goal.id}
                    onClick={() => handleArrayChange('career_goals', goal.id, 
                      formData.career_goals.includes(goal.id) ? 'remove' : 'add')}
                    style={{
                      padding: '20px',
                      border: formData.career_goals.includes(goal.id) ? '2px solid #4f8cff' : '2px solid #e5e7eb',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      background: formData.career_goals.includes(goal.id) ? '#f0f7ff' : 'white',
                      textAlign: 'left'
                    }}
                  >
                    <div style={{ fontSize: '24px', marginBottom: '10px' }}>{goal.icon}</div>
                    <div style={{ fontWeight: '600', fontSize: '16px', color: '#222', marginBottom: '5px' }}>
                      {goal.id}
                    </div>
                    <div style={{ fontSize: '14px', color: '#666' }}>{goal.desc}</div>
                  </div>
                ))}
              </div>

              {/* Add custom career goal */}
              <div style={{
                marginTop: '20px',
                display: 'flex',
                gap: '10px',
                justifyContent: 'center'
              }}>
                <input
                  type="text"
                  value={newGoal}
                  onChange={(e) => setNewGoal(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      const value = newGoal.trim();
                      if (!value) return;
                      if (!formData.career_goals.includes(value)) {
                        handleArrayChange('career_goals', value, 'add');
                      }
                      setNewGoal('');
                    }
                  }}
                  placeholder="Add your own career goal"
                  style={{
                    width: '100%',
                    maxWidth: '420px',
                    padding: '12px 16px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '10px',
                    fontSize: '14px'
                  }}
                />
                <button
                  onClick={() => {
                    const value = newGoal.trim();
                    if (!value) return;
                    if (!formData.career_goals.includes(value)) {
                      handleArrayChange('career_goals', value, 'add');
                    }
                    setNewGoal('');
                  }}
                  style={{
                    padding: '12px 16px',
                    background: '#4f8cff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Add
                </button>
              </div>

              {formData.career_goals.length > 0 && (
                <div style={{ marginTop: '14px', color: '#666', fontSize: '14px' }}>
                  Selected: {formData.career_goals.join(', ')}
                </div>
              )}
            </div>
          )}

          {/* Step 4: Current Skills */}
          {currentStep === 4 && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', color: '#fbbf24', marginBottom: '20px' }}>
                <FaStar />
              </div>
              <h2 style={{ fontSize: '32px', fontWeight: '700', color: '#222', marginBottom: '15px' }}>
                What skills do you already have?
              </h2>
              <p style={{ fontSize: '16px', color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
                Add skills you're familiar with and rate your confidence level. This helps us avoid repetition.
              </p>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: '10px',
                maxWidth: '600px',
                margin: '0 auto'
              }}>
                {[
                  'Python', 'JavaScript', 'Java', 'C++', 'Data Structures', 'Algorithms',
                  'Machine Learning', 'Web Development', 'Database Management', 'Statistics',
                  'Linear Algebra', 'Calculus', 'Physics', 'Chemistry', 'English', 'Mathematics'
                ].map(skill => (
                  <button
                    key={skill}
                    onClick={() => handleArrayChange('current_skills', skill, 
                      formData.current_skills.includes(skill) ? 'remove' : 'add')}
                    style={{
                      padding: '12px 16px',
                      border: formData.current_skills.includes(skill) ? '2px solid #4f8cff' : '2px solid #e5e7eb',
                      borderRadius: '8px',
                      background: formData.current_skills.includes(skill) ? '#4f8cff' : 'white',
                      color: formData.current_skills.includes(skill) ? 'white' : '#666',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      fontSize: '14px',
                      fontWeight: '500'
                    }}
                  >
                    {skill}
                  </button>
                ))}
              </div>

              {/* Add custom skill */}
              <div style={{
                marginTop: '20px',
                display: 'flex',
                gap: '10px',
                justifyContent: 'center'
              }}>
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      const value = newSkill.trim();
                      if (!value) return;
                      if (!formData.current_skills.includes(value)) {
                        handleArrayChange('current_skills', value, 'add');
                      }
                      setNewSkill('');
                    }
                  }}
                  placeholder="Add your own skill"
                  style={{
                    width: '100%',
                    maxWidth: '420px',
                    padding: '12px 16px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '10px',
                    fontSize: '14px'
                  }}
                />
                <button
                  onClick={() => {
                    const value = newSkill.trim();
                    if (!value) return;
                    if (!formData.current_skills.includes(value)) {
                      handleArrayChange('current_skills', value, 'add');
                    }
                    setNewSkill('');
                  }}
                  style={{
                    padding: '12px 16px',
                    background: '#4f8cff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Add
                </button>
              </div>

              {formData.current_skills.length > 0 && (
                <div style={{ marginTop: '14px', color: '#666', fontSize: '14px' }}>
                  Selected: {formData.current_skills.join(', ')}
                </div>
              )}
            </div>
          )}

          {/* Step 5: Time Commitment */}
          {currentStep === 5 && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', color: '#10b981', marginBottom: '20px' }}>
                <FaClock />
              </div>
              <h2 style={{ fontSize: '32px', fontWeight: '700', color: '#222', marginBottom: '15px' }}>
                How much time can you dedicate daily?
              </h2>
              <p style={{ fontSize: '16px', color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
                We'll create a realistic learning schedule that fits your lifestyle.
              </p>
              
              <div style={{
                background: '#f0f7ff',
                padding: '30px',
                borderRadius: '16px',
                marginBottom: '30px',
                maxWidth: '400px',
                margin: '0 auto'
              }}>
                <div style={{ fontSize: '36px', fontWeight: '700', color: '#4f8cff', marginBottom: '5px' }}>
                  {formData.time_commitment}
                </div>
                <div style={{ fontSize: '16px', color: '#666' }}>per day</div>
              </div>
              
              <input
                type="range"
                min="0.5"
                max="8"
                step="0.5"
                value={formData.time_commitment.split(' ')[0]}
                onChange={(e) => handleInputChange('time_commitment', `${e.target.value} hours`)}
                style={{
                  width: '100%',
                  maxWidth: '400px',
                  marginBottom: '20px'
                }}
              />
              
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                maxWidth: '400px',
                margin: '0 auto',
                fontSize: '14px',
                color: '#666'
              }}>
                <span>30 min</span>
                <span>8 hours</span>
              </div>
              
              <div style={{
                background: '#f0f7ff',
                padding: '20px',
                borderRadius: '12px',
                marginTop: '30px',
                maxWidth: '400px',
                margin: '0 auto',
                textAlign: 'left'
              }}>
                <div style={{ fontWeight: '600', fontSize: '16px', color: '#222', marginBottom: '10px' }}>
                  Your Learning Preview
                </div>
                <div style={{ fontSize: '14px', color: '#666', lineHeight: '1.6' }}>
                  <div>• {parseFloat(formData.time_commitment.split(' ')[0]) * 7} hours per week</div>
                  <div>• ~{Math.ceil(parseFloat(formData.time_commitment.split(' ')[0]) * 2)} topics per week</div>
                  <div>• Estimated completion: 3-6 months</div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '40px'
          }}>
            {currentStep > 1 && (
              <button
                onClick={prevStep}
                style={{
                  padding: '12px 24px',
                  background: 'white',
                  color: '#666',
                  border: '2px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  e.target.style.borderColor = '#4f8cff';
                  e.target.style.color = '#4f8cff';
                }}
                onMouseLeave={(e) => {
                  e.target.style.borderColor = '#e5e7eb';
                  e.target.style.color = '#666';
                }}
              >
                <FaArrowLeft /> Previous
              </button>
            )}
            
            {currentStep < 5 ? (
              <button
                onClick={nextStep}
                style={{
                  padding: '12px 24px',
                  background: '#4f8cff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: 'pointer',
                  marginLeft: 'auto',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => e.target.style.background = '#3b7de9'}
                onMouseLeave={(e) => e.target.style.background = '#4f8cff'}
              >
                Next <FaArrowRight />
              </button>
            ) : (
              <button
                onClick={handleCompletion}
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  background: loading ? '#ccc' : '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  marginLeft: 'auto',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  if (!loading) e.target.style.background = '#059669';
                }}
                onMouseLeave={(e) => {
                  if (!loading) e.target.style.background = '#10b981';
                }}
              >
                {loading ? 'Creating your plan...' : 'Get Started'} <FaArrowRight />
              </button>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default OnboardingFlow; 