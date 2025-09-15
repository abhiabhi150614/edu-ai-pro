import React from 'react';
import Sidebar from './Sidebar';
import Chatbot from './Chatbot';

const Layout = ({ children }) => {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      
      <div style={{ 
        flex: 1, 
        padding: '20px', 
        background: '#f8f9fa',
        marginLeft: '270px', // Account for sidebar width
        transition: 'margin-left 0.3s ease'
      }}>
        {children}
      </div>
      
      {/* Floating Chat Widget */}
      <Chatbot />
    </div>
  );
};

export default Layout; 