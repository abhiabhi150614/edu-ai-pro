const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function apiFetch(path, options = {}) {
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });
    
    if (!response.ok) {
      let errMsg = 'Unknown error';
      try {
        const errData = await response.json();
        
        // Handle validation errors (422 status)
        if (response.status === 422 && errData.detail) {
          if (Array.isArray(errData.detail)) {
            // Format validation errors
            const validationErrors = errData.detail.map(error => 
              `${error.loc?.join('.') || 'field'}: ${error.msg}`
            ).join(', ');
            errMsg = `Validation error: ${validationErrors}`;
          } else {
            errMsg = errData.detail;
          }
        } else {
          errMsg = errData.detail || errData.message || errMsg;
        }
      } catch (parseError) {
        // If JSON parsing fails, use status text
        errMsg = response.statusText || errMsg;
      }
      throw new Error(errMsg);
    }
    
    return response.json();
  } catch (error) {
    console.error(`API Error (${path}):`, error);
    throw error;
  }
}

// Helper function for authenticated requests
export async function authenticatedFetch(path, options = {}) {
  const token = localStorage.getItem('token');
  
  if (!token) {
    throw new Error('No authentication token found');
  }
  
  return apiFetch(path, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    },
  });
} 