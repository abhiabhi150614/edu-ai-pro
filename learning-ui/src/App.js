import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Profile from './components/Profile';
import Chatbot from './components/Chatbot';
import GoogleCallback from './components/GoogleCallback';

import OnboardingFlow from './components/OnboardingFlow';
import LearningPlans from './components/LearningPlans';
import QuizDashboard from './components/QuizDashboard';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/chat" element={<div style={{padding: '20px'}}><Chatbot /></div>} />
          <Route path="/onboarding" element={<OnboardingFlow />} />
          <Route path="/learning-plans" element={<LearningPlans />} />
          <Route path="/quiz" element={<QuizDashboard />} />
          <Route path="/auth/google/callback" element={<GoogleCallback />} />

        </Routes>
      </div>
    </Router>
  );
}

export default App;