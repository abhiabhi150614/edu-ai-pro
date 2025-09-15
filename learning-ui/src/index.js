import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { ThemeProvider, createGlobalStyle } from 'styled-components';
import '@fontsource/inter/400.css';
import '@fontsource/inter/700.css';
import '@fontsource/poppins/400.css';
import '@fontsource/poppins/700.css';

const theme = {
  colors: {
    primary: '#4F8CFF', // Calming blue
    secondary: '#A259FF', // Calming purple
    background: '#F7F9FB',
    card: '#FFFFFF',
    text: '#22223B',
    accent: '#E0E7FF',
    border: '#E3E8F0',
    success: '#4ADE80',
    warning: '#FBBF24',
    error: '#F87171',
  },
  fonts: {
    heading: 'Poppins, Inter, sans-serif',
    body: 'Inter, Poppins, sans-serif',
  },
  radii: {
    card: '18px',
    button: '12px',
    input: '10px',
  },
  shadows: {
    card: '0 4px 24px rgba(80, 112, 255, 0.08)',
    modal: '0 8px 32px rgba(80, 112, 255, 0.12)',
  },
};

const GlobalStyle = createGlobalStyle`
  body {
    background: ${props => props.theme.colors.background};
    color: ${props => props.theme.colors.text};
    font-family: ${props => props.theme.fonts.body};
    margin: 0;
    padding: 0;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  *, *::before, *::after {
    box-sizing: border-box;
  }
`;

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);

reportWebVitals();
