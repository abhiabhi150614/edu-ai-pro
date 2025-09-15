import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiFetch } from '../api';

const GoogleCallback = () => {
  const [status, setStatus] = useState('Processing...');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleGoogleCallback = async () => {
      try {
        // Get the authorization code from URL parameters
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');
        
        console.log('Google callback params:', { code: !!code, error });
        
        if (error) {
          setError(`Google authentication error: ${error}`);
          setStatus('Authentication failed');
          return;
        }
        
        if (!code) {
          setError('No authorization code received from Google');
          setStatus('Authentication failed');
          return;
        }

        setStatus('Authenticating with Google...');

        // Send the code to our backend
        const response = await apiFetch('/auth/google/callback', {
          method: 'POST',
          body: JSON.stringify({
            code: code,
            redirect_uri: process.env.REACT_APP_GOOGLE_REDIRECT_URI || 'http://localhost:3000/auth/google/callback'
          })
        });

        console.log('Google auth response:', response);

        // Store the token
        localStorage.setItem('token', response.access_token);
        
        // Store Google user info if needed
        if (response.user) {
          localStorage.setItem('google_user', JSON.stringify(response.user));
        }

        setStatus('Authentication successful! Redirecting...');

        // Redirect based on whether user has completed onboarding
        try {
          await apiFetch('/onboarding');
          // If successful, user has onboarding data, go to dashboard
          setTimeout(() => navigate('/dashboard'), 1000);
        } catch (onboardingError) {
          console.log('User needs onboarding:', onboardingError.message);
          // If error, user needs to complete onboarding
          setTimeout(() => navigate('/onboarding'), 1000);
        }

      } catch (err) {
        console.error('Google callback error:', err);
        setError(err.message || 'Authentication failed');
        setStatus('Authentication failed');
      }
    };

    handleGoogleCallback();
  }, [navigate, location]);

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
        maxWidth: '400px',
        textAlign: 'center'
      }}>
        <div style={{ marginBottom: '20px' }}>
          <div style={{
            width: '60px',
            height: '60px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #4f8cff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
        </div>
        
        <h2 style={{ color: '#333', marginBottom: '10px' }}>Google Authentication</h2>
        
        {error ? (
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
        ) : (
          <p style={{ color: '#666', fontSize: '16px', marginBottom: '20px' }}>
            {status}
          </p>
        )}

        {error && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              onClick={() => navigate('/login')}
              style={{
                padding: '12px 24px',
                background: '#4f8cff',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Back to Login
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '8px 16px',
                background: '#f3f4f6',
                color: '#374151',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Try Again
            </button>
          </div>
        )}
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

export default GoogleCallback; 