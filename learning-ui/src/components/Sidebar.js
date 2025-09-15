import React, { useState } from 'react';
import { FaHome, FaBullseye, FaBookOpen, FaBrain, FaRegStickyNote, FaCalendarAlt, FaUserGraduate, FaFileAlt, FaUsers, FaTrophy, FaCog, FaSignOutAlt, FaYoutube, FaBars, FaTimes,FaCalendar,FaUser, FaMicrophone, FaChartLine } from 'react-icons/fa';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import QuizDashboard from './QuizDashboard';

const navLinks = [
  { path: "/dashboard", icon: <FaHome />, text: "Dashboard" },
  { path: "/learning-plans", icon: <FaBookOpen />, text: "Learning Plans" },
  { path: "/subplans", icon: <FaBullseye />, text: "Sub Plans" },
  { path: "/quizzes", icon: <FaBrain />, text: "Quizzes" },
  { path: "/notes", icon: <FaRegStickyNote />, text: "Notes" },
  { path: "/calendar", icon: <FaCalendar />, text: "Calendar" },
  { path: "/voice-tutor", icon: <FaMicrophone />, text: "Voice Tutor" },
  { path: "/resume", icon: <FaFileAlt />, text: "Resume" },
  { path: "/community", icon: <FaUsers />, text: "Community" },
  { path: "/progress", icon: <FaChartLine />, text: "Progress" },
  { path: "/youtube-learning", icon: <FaYoutube />, text: "YouTube Learning" },
  { path: "/profile", icon: <FaUser />, text: "Profile" },
  { path: "/settings", icon: <FaCog />, text: "Settings" }
];

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showQuizDashboard, setShowQuizDashboard] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Check if we're on the quizzes page
  const isQuizzesPage = location.pathname === '/quizzes';
  // Auto-open quiz dashboard when on /quizzes
  React.useEffect(() => {
    if (isQuizzesPage) {
      setShowQuizDashboard(true);
    }
  }, [isQuizzesPage]);

  const handleLogout = () => {
    // Clear all stored data
    localStorage.removeItem('token');
    localStorage.removeItem('google_user');
    
    // Redirect to login page
    navigate('/login');
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const toggleQuizDashboard = () => {
    setShowQuizDashboard(!showQuizDashboard);
  };

  return (
    <>
      {/* Mobile overlay when sidebar is open */}
      {!isCollapsed && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 5,
            display: window.innerWidth <= 768 ? 'block' : 'none'
          }}
          onClick={toggleSidebar}
        />
      )}

      {/* Toggle button - positioned to avoid text intersection */}
      <button
        onClick={toggleSidebar}
        style={{
          position: 'fixed',
          top: '20px',
          left: isCollapsed ? '20px' : '280px', // Moved slightly left to avoid text
          zIndex: 20,
          background: '#4f8cff',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '50px',
          height: '50px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(79, 140, 255, 0.3)',
          transition: 'all 0.3s ease',
          fontSize: '18px'
        }}
      >
        {isCollapsed ? <FaBars /> : <FaTimes />}
      </button>

      <div style={{
        width: isCollapsed ? '80px' : '270px',
        background: '#fff',
        minHeight: '100vh',
        borderRight: '1.5px solid #f0f1f7',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'fixed',
        left: isCollapsed ? '-80px' : '0',
        top: 0,
        bottom: 0,
        zIndex: 10,
        transition: 'all 0.3s ease',
        transform: isCollapsed ? 'translateX(-100%)' : 'translateX(0)'
      }}>
        {/* Top: Logo and nav */}
        <div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 12, 
            padding: '2.2rem 2rem 1.5rem 2rem',
            opacity: isCollapsed ? 0 : 1,
            transition: 'opacity 0.3s ease'
          }}>
            <div style={{ 
              background: '#4f8cff', 
              color: '#fff', 
              borderRadius: '50%', 
              width: 44, 
              height: 44, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              fontWeight: 700, 
              fontSize: 22 
            }}>
              EA
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 20, color: '#222' }}>EduAI</div>
              <div style={{ fontSize: 13, color: '#6b7280', marginTop: 2 }}>Learning Platform</div>
            </div>
          </div>
          
          <nav style={{ marginTop: 10 }}>
            {navLinks.map((link, index) => (
              <NavLink
                key={index}
                to={link.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 16px',
                  color: '#666',
                  textDecoration: 'none',
                  borderRadius: '8px',
                  marginBottom: '4px',
                  transition: 'all 0.3s ease',
                  fontSize: isCollapsed ? '0' : '14px'
                }}
                onClick={() => {
                  if (link.path === '/quizzes') {
                    toggleQuizDashboard();
                  }
                }}
              >
                <span style={{ marginRight: isCollapsed ? '0' : '12px', fontSize: '16px' }}>
                  {link.icon}
                </span>
                {!isCollapsed && <span>{link.text}</span>}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* Quiz Dashboard Section - Only show when on quizzes page and not collapsed */}
        {isQuizzesPage && !isCollapsed && showQuizDashboard && (
          <div style={{
            borderTop: '1px solid #e5e7eb',
            padding: '16px 0',
            maxHeight: '50vh',
            overflow: 'hidden'
          }}>
            <QuizDashboard />
          </div>
        )}

        {/* Bottom: User profile and settings */}
        <div style={{ 
          padding: '2rem',
          opacity: isCollapsed ? 0 : 1,
          transition: 'opacity 0.3s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{ 
              background: '#e0e7ff', 
              color: '#4f8cff', 
              borderRadius: '50%', 
              width: 38, 
              height: 38, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              fontWeight: 600, 
              fontSize: 18 
            }}>
              Z
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 16, color: '#222' }}>zs</div>
              <div style={{ fontSize: 13, color: '#6b7280', marginTop: 2 }}>
                <span style={{ 
                  background: '#f3f4fd', 
                  color: '#4f8cff', 
                  borderRadius: 8, 
                  padding: '2px 8px', 
                  fontWeight: 500, 
                  fontSize: 12, 
                  marginRight: 6 
                }}>
                  Level 1
                </span>
                <span style={{ fontSize: 12 }}>0 XP</span>
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <NavLink 
              to="/settings" 
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '8px 12px',
                color: '#666',
                textDecoration: 'none',
                borderRadius: '6px',
                transition: 'all 0.3s ease',
                fontSize: isCollapsed ? '0' : '13px'
              }}
            >
              <span style={{ marginRight: isCollapsed ? '0' : '8px', fontSize: '14px' }}>
                <FaCog />
              </span>
              {!isCollapsed && <span>Settings</span>}
            </NavLink>
            
            <button
              onClick={handleLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '8px 12px',
                color: '#ef4444',
                textDecoration: 'none',
                borderRadius: '6px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                fontSize: isCollapsed ? '0' : '13px'
              }}
            >
              <span style={{ marginRight: isCollapsed ? '0' : '8px', fontSize: '14px' }}>
                <FaSignOutAlt />
              </span>
              {!isCollapsed && <span>Logout</span>}
            </button>
          </div>
        </div>
      </div>

      {/* CSS for active nav links */}
      <style>{`
        .nav-link:hover {
          background: #f8fafc;
          color: #4f8cff;
        }
        
        .nav-link.active {
          background: #eff6ff;
          color: #4f8cff;
          font-weight: 600;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};

export default Sidebar; 