import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaExclamationTriangle, FaPhone, FaCheckCircle } from 'react-icons/fa';
import Layout from './Layout';
import { authenticatedFetch } from '../api';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [onboardingData, setOnboardingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [userData, onboardingResponse] = await Promise.all([
        authenticatedFetch('/me'),
        authenticatedFetch('/onboarding').catch(() => null)
      ]);
      
      setUser(userData);
      if (onboardingResponse) {
        setOnboardingData(onboardingResponse);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <div>Loading dashboard...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem' }}>
        <h1 style={{ marginBottom: '2rem', color: '#333' }}>Welcome to Your Learning Dashboard</h1>

        {/* Phone Verification Alert */}
        {user && !user.phone_verified && (
          <div style={{
            background: '#fff3cd',
            border: '1px solid #ffeaa7',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <FaExclamationTriangle color="#856404" />
            <div style={{ flex: 1 }}>
              <strong>Phone verification required!</strong>
              <div style={{ fontSize: '0.9rem', color: '#856404', marginTop: '0.25rem' }}>
                Please verify your phone number to access all features. 
                <button
                  onClick={() => navigate('/profile')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#856404',
                    textDecoration: 'underline',
                    cursor: 'pointer',
                    marginLeft: '0.5rem'
                  }}
                >
                  Go to Profile
                </button>
              </div>
            </div>
          </div>
        )}

        {/* User Information */}
        <div style={{ background: 'white', borderRadius: '12px', padding: '2rem', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>Account Information</h2>
          
          <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
            <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
              <strong>Email:</strong> {user?.email}
            </div>
            
            <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <strong>Google Account:</strong>
              {user?.is_google_authenticated ? (
                <span style={{ color: '#28a745', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <FaCheckCircle /> Connected
                </span>
              ) : (
                <span style={{ color: '#dc3545' }}>Not connected</span>
              )}
            </div>
            
            <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <strong>Phone:</strong>
              {user?.phone_verified ? (
                <span style={{ color: '#28a745', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <FaCheckCircle /> {user.phone_number}
                </span>
              ) : (
                <span style={{ color: '#dc3545', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <FaPhone /> {user?.phone_number || 'Not verified'}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Onboarding Information */}
        {onboardingData && (
          <div style={{ background: 'white', borderRadius: '12px', padding: '2rem', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', marginBottom: '2rem' }}>
            <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>Learning Profile</h2>

            <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
              <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <strong>Name:</strong> {onboardingData.name}
              </div>

              <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <strong>Grade:</strong> {onboardingData.grade}
              </div>

              <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <strong>Time Commitment:</strong> {onboardingData.time_commitment}
              </div>

              {Array.isArray(onboardingData.career_goals) && onboardingData.career_goals.length > 0 && (
                <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px', gridColumn: '1 / -1' }}>
                  <strong>Career Goals:</strong> {onboardingData.career_goals.join(', ')}
                </div>
              )}

              {Array.isArray(onboardingData.current_skills) && onboardingData.current_skills.length > 0 && (
                <div style={{ padding: '1rem', background: '#f8f9fa', borderRadius: '8px', gridColumn: '1 / -1' }}>
                  <strong>Current Skills:</strong> {onboardingData.current_skills.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div style={{ background: 'white', borderRadius: '12px', padding: '2rem', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>Quick Actions</h2>
          
          <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            <button
              onClick={() => navigate('/youtube-learning')}
              style={{
                background: '#4f8cff',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '1rem',
                fontSize: '16px',
                cursor: 'pointer',
                transition: 'background 0.3s ease'
              }}
            >
              Add YouTube Playlist
            </button>
            
            <button
              onClick={() => navigate('/calendar')}
              style={{
                background: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '1rem',
                fontSize: '16px',
                cursor: 'pointer',
                transition: 'background 0.3s ease'
              }}
            >
              View Calendar
            </button>
            
            <button
              onClick={() => navigate('/profile')}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                padding: '1rem',
                fontSize: '16px',
                cursor: 'pointer',
                transition: 'background 0.3s ease'
              }}
            >
              Manage Profile
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard; 