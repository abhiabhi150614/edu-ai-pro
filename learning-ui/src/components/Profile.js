import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaUser, FaPhone, FaCheckCircle, FaExclamationTriangle, FaGoogle, FaEnvelope, FaCalendarAlt, FaEdit } from 'react-icons/fa';
import Layout from './Layout';
import { authenticatedFetch } from '../api';


const Profile = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [showPhoneForm, setShowPhoneForm] = useState(false);
  const [showVerificationForm, setShowVerificationForm] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const userData = await authenticatedFetch('/me');
      setUser(userData);
      if (userData.phone_number) {
        setPhoneNumber(userData.phone_number);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const sendVerificationCode = async () => {
    if (!phoneNumber) {
      setError('Please enter a phone number');
      return;
    }
    
    setSendingCode(true);
    setError('');
    try {
      const response = await authenticatedFetch('/phone/send-verification', {
        method: 'POST',
        body: JSON.stringify({ phone_number: phoneNumber })
      });
      setMessage(`Verification code sent! Demo code: ${response.demo_code}`);
      setShowVerificationForm(true);
    } catch (error) {
      setError(`Failed to send verification code: ${error.message}`);
    } finally {
      setSendingCode(false);
    }
  };

  const verifyPhoneCode = async () => {
    if (!verificationCode) {
      setError('Please enter the verification code');
      return;
    }
    
    setVerifying(true);
    setError('');
    try {
      await authenticatedFetch('/phone/verify', {
        method: 'POST',
        body: JSON.stringify({ 
          phone_number: phoneNumber, 
          verification_code: verificationCode 
        })
      });
      setMessage('Phone number verified successfully!');
      setShowVerificationForm(false);
      setShowPhoneForm(false);
      await loadUserProfile(); // Reload user data
    } catch (error) {
      setError(`Verification failed: ${error.message}`);
    } finally {
      setVerifying(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <div>Loading profile...</div>
        </div>
      </Layout>
    );
  }

  if (!user) {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div>Failed to load profile</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
        <h1 style={{ marginBottom: '2rem', color: '#333', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FaUser /> Profile
        </h1>

        {/* Phone Verification Alert */}
        {!user.phone_verified && (
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
            <div>
              <strong>Phone verification required!</strong>
              <div style={{ fontSize: '0.9rem', color: '#856404', marginTop: '0.25rem' }}>
                Please verify your phone number to access all features.
              </div>
            </div>
          </div>
        )}

        {/* Profile Information */}
        <div style={{ background: 'white', borderRadius: '12px', padding: '2rem', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '1.5rem', color: '#333', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FaUser /> Personal Information
          </h2>
          
          <div style={{ display: 'grid', gap: '1.5rem' }}>
            {/* Email */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
              <FaEnvelope color="#4f8cff" />
              <div>
                <div style={{ fontWeight: '600', color: '#333' }}>Email</div>
                <div style={{ color: '#666' }}>{user.email}</div>
              </div>
            </div>

            {/* Google Authentication */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
              <FaGoogle color={user.is_google_authenticated ? "#34a853" : "#666"} />
              <div>
                <div style={{ fontWeight: '600', color: '#333' }}>Google Account</div>
                <div style={{ color: '#666' }}>
                  {user.is_google_authenticated ? (
                    <span style={{ color: '#34a853', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FaCheckCircle /> Connected
                      {user.google_name && ` (${user.google_name})`}
                    </span>
                  ) : (
                    <span style={{ color: '#dc3545' }}>Not connected</span>
                  )}
                </div>
              </div>
            </div>

            {/* Phone Number */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
              <FaPhone color={user.phone_verified ? "#34a853" : "#666"} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '600', color: '#333' }}>Phone Number</div>
                <div style={{ color: '#666' }}>
                  {user.phone_number ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {user.phone_number}
                      {user.phone_verified ? (
                        <FaCheckCircle color="#34a853" />
                      ) : (
                        <FaExclamationTriangle color="#dc3545" />
                      )}
                    </span>
                  ) : (
                    <span style={{ color: '#dc3545' }}>Not provided</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowPhoneForm(!showPhoneForm)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#4f8cff',
                  cursor: 'pointer',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                <FaEdit /> {user.phone_number ? 'Edit' : 'Add'}
              </button>
            </div>

            {/* Account Created */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
              <FaCalendarAlt color="#4f8cff" />
              <div>
                <div style={{ fontWeight: '600', color: '#333' }}>Account Created</div>
                <div style={{ color: '#666' }}>
                  {new Date(user.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Phone Verification Form */}
        {showPhoneForm && (
          <div style={{ background: 'white', borderRadius: '12px', padding: '2rem', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', marginBottom: '2rem' }}>
            <h3 style={{ marginBottom: '1rem', color: '#333' }}>Phone Verification</h3>
            
            {!showVerificationForm ? (
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#555' }}>
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="+1234567890"
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '2px solid #e1e5e9',
                      borderRadius: '8px',
                      fontSize: '16px'
                    }}
                  />
                </div>
                <button
                  onClick={sendVerificationCode}
                  disabled={sendingCode}
                  style={{
                    background: '#4f8cff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0.75rem 1.5rem',
                    fontSize: '16px',
                    cursor: sendingCode ? 'not-allowed' : 'pointer',
                    opacity: sendingCode ? 0.7 : 1
                  }}
                >
                  {sendingCode ? 'Sending...' : 'Send Code'}
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#555' }}>
                    Verification Code
                  </label>
                  <input
                    type="text"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    placeholder="123456"
                    maxLength="6"
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '2px solid #e1e5e9',
                      borderRadius: '8px',
                      fontSize: '16px'
                    }}
                  />
                </div>
                <button
                  onClick={verifyPhoneCode}
                  disabled={verifying}
                  style={{
                    background: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0.75rem 1.5rem',
                    fontSize: '16px',
                    cursor: verifying ? 'not-allowed' : 'pointer',
                    opacity: verifying ? 0.7 : 1
                  }}
                >
                  {verifying ? 'Verifying...' : 'Verify'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Messages */}
        {message && (
          <div style={{
            background: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem',
            color: '#155724'
          }}>
            {message}
          </div>
        )}

        {error && (
          <div style={{
            background: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem',
            color: '#721c24'
          }}>
            {error}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Profile; 