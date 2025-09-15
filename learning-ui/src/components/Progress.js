import React, { useState, useEffect } from 'react';
import { authenticatedFetch } from '../api';
import { FaCalendarAlt, FaBook, FaCheckCircle, FaSpinner, FaDownload } from 'react-icons/fa';

const Progress = () => {
  const [progress, setProgress] = useState(null);
  const [notes, setNotes] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notesLoading, setNotesLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProgress();
  }, []);

  const fetchProgress = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await authenticatedFetch('/progress');
      setProgress(data);
      
      // Set default selected month to current month
      if (data.current_position) {
        setSelectedMonth(data.current_position.current_month_index);
        setSelectedDay(data.current_position.current_day);
      }
    } catch (err) {
      console.error('Error fetching progress:', err);
      setError('Failed to load progress data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotes = async (monthIndex, day) => {
    if (!monthIndex || !day) return;
    
    setNotesLoading(true);
    setNotes(null);
    try {
      const data = await authenticatedFetch(`/notes/${monthIndex}/${day}`);
      setNotes(data.notes);
    } catch (err) {
      console.error('Error fetching notes:', err);
      setError('Failed to load notes. Please try again later.');
    } finally {
      setNotesLoading(false);
    }
  };

  useEffect(() => {
    if (selectedMonth && selectedDay) {
      fetchNotes(selectedMonth, selectedDay);
    }
  }, [selectedMonth, selectedDay]);

  if (loading) {
    return (
      <div style={{ padding: 32, textAlign: 'center' }}>
        <FaSpinner style={{ fontSize: 32, color: '#4f8cff', animation: 'spin 1s linear infinite' }} />
        <p>Loading your progress...</p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 32, textAlign: 'center', color: '#dc3545' }}>
        <h2>Error</h2>
        <p>{error}</p>
        <button 
          onClick={fetchProgress}
          style={{
            padding: '8px 16px',
            background: '#4f8cff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!progress) {
    return (
      <div style={{ padding: 32 }}>
        <h2>No Progress Data</h2>
        <p>You don't have any active learning plans yet.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 24, color: '#333' }}>Learning Progress</h1>
      
      {/* Current Position */}
      <div style={{ 
        background: 'linear-gradient(135deg, #4f8cff, #6d9eff)', 
        padding: 24, 
        borderRadius: 8,
        color: 'white',
        marginBottom: 32,
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ marginTop: 0 }}>{progress.current_position.plan_title}</h2>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div>
            <h3 style={{ fontSize: 16, opacity: 0.9, margin: '0 0 8px 0' }}>
              <FaCalendarAlt style={{ marginRight: 8 }} />
              Current Month
            </h3>
            <p style={{ fontSize: 20, fontWeight: 'bold', margin: 0 }}>
              Month {progress.current_position.current_month_index}
            </p>
          </div>
          <div>
            <h3 style={{ fontSize: 16, opacity: 0.9, margin: '0 0 8px 0' }}>
              <FaBook style={{ marginRight: 8 }} />
              Current Day
            </h3>
            <p style={{ fontSize: 20, fontWeight: 'bold', margin: 0 }}>
              Day {progress.current_position.current_day}
            </p>
          </div>
          {progress.summary && (
            <div>
              <h3 style={{ fontSize: 16, opacity: 0.9, margin: '0 0 8px 0' }}>
                <FaCheckCircle style={{ marginRight: 8 }} />
                Overall Progress
              </h3>
              <p style={{ fontSize: 20, fontWeight: 'bold', margin: 0 }}>
                {progress.summary.overall_progress || '0%'}
              </p>
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
        {/* Month Progress */}
        <div style={{ flex: 1, minWidth: 300 }}>
          <h2>Month Progress</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {progress.month_progress.map((month) => (
              <div 
                key={month.index}
                style={{ 
                  padding: 16, 
                  borderRadius: 8, 
                  border: `1px solid ${selectedMonth === month.index ? '#4f8cff' : '#e1e5e9'}`,
                  background: selectedMonth === month.index ? '#f0f7ff' : 'white',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onClick={() => setSelectedMonth(month.index)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0 }}>{month.title || `Month ${month.index}`}</h3>
                  <span style={{ 
                    padding: '4px 8px', 
                    borderRadius: 12, 
                    fontSize: 12,
                    background: month.status === 'completed' ? '#28a745' : 
                               month.status === 'in_progress' ? '#ffc107' : '#6c757d',
                    color: 'white'
                  }}>
                    {month.status === 'completed' ? 'Completed' : 
                     month.status === 'in_progress' ? 'In Progress' : 
                     month.status === 'not_started' ? 'Not Started' : month.status}
                  </span>
                </div>
                
                <div style={{ marginTop: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span>Progress</span>
                    <span>{month.days_completed}/{month.total_days} days</span>
                  </div>
                  <div style={{ 
                    height: 8, 
                    background: '#e9ecef', 
                    borderRadius: 4, 
                    overflow: 'hidden' 
                  }}>
                    <div style={{ 
                      height: '100%', 
                      width: `${(month.days_completed / Math.max(month.total_days, 1)) * 100}%`,
                      background: '#4f8cff',
                      borderRadius: 4
                    }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Day Selection and Notes */}
        <div style={{ flex: 1, minWidth: 300 }}>
          {selectedMonth && (
            <>
              <h2>Day Notes</h2>
              <div style={{ marginBottom: 16 }}>
                <label htmlFor="daySelect" style={{ display: 'block', marginBottom: 8 }}>
                  Select Day:
                </label>
                <select 
                  id="daySelect"
                  value={selectedDay || ''}
                  onChange={(e) => setSelectedDay(Number(e.target.value))}
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px', 
                    borderRadius: 4, 
                    border: '1px solid #ced4da',
                    fontSize: 16
                  }}
                >
                  <option value="">Select a day...</option>
                  {Array.from({ length: 30 }, (_, i) => i + 1).map(day => (
                    <option key={day} value={day}>Day {day}</option>
                  ))}
                </select>
              </div>

              {notesLoading ? (
                <div style={{ textAlign: 'center', padding: 32 }}>
                  <FaSpinner style={{ fontSize: 24, color: '#4f8cff', animation: 'spin 1s linear infinite' }} />
                  <p>Loading notes...</p>
                </div>
              ) : notes ? (
                <div style={{ 
                  padding: 16, 
                  borderRadius: 8, 
                  border: '1px solid #e1e5e9',
                  background: 'white',
                  whiteSpace: 'pre-wrap',
                  maxHeight: 400,
                  overflowY: 'auto'
                }}>
                  {notes}
                </div>
              ) : (
                <div style={{ 
                  padding: 16, 
                  borderRadius: 8, 
                  border: '1px solid #e1e5e9',
                  background: '#f8f9fa',
                  textAlign: 'center'
                }}>
                  {selectedDay ? (
                    <p>No notes found for Month {selectedMonth}, Day {selectedDay}</p>
                  ) : (
                    <p>Select a day to view notes</p>
                  )}
                </div>
              )}

              {notes && (
                <div style={{ marginTop: 16, textAlign: 'right' }}>
                  <button
                    onClick={() => {
                      // Create a blob and download link
                      const blob = new Blob([notes], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `Month_${selectedMonth}_Day_${selectedDay}_Notes.txt`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      URL.revokeObjectURL(url);
                    }}
                    style={{
                      padding: '8px 16px',
                      background: '#4f8cff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8
                    }}
                  >
                    <FaDownload /> Download Notes
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Progress;