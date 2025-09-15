import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { authenticatedFetch } from '../api';

const YouTubeLearning = () => {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [playlistData, setPlaylistData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [schedules, setSchedules] = useState([]);
  const [dailyMinutes, setDailyMinutes] = useState(30);
  const [syncingToGoogle, setSyncingToGoogle] = useState(false);
  const [showTimeOptions, setShowTimeOptions] = useState(false);
  const [startTime, setStartTime] = useState('21:00'); // 9:00 PM default
  const [durationMinutes, setDurationMinutes] = useState(60); // 60 min default

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      const response = await authenticatedFetch('/youtube-schedules', {
        method: 'GET'
      });
      setSchedules(response);
    } catch (error) {
      console.error('Failed to load schedules:', error);
    }
  };

  const extractPlaylistId = (url) => {
    const match = url.match(/[?&]list=([^&]+)/);
    return match ? match[1] : null;
  };

  const fetchPlaylistData = async () => {
    if (!playlistUrl) {
      setError('Please enter a YouTube playlist URL');
      return;
    }

    const playlistId = extractPlaylistId(playlistUrl);
    if (!playlistId) {
      setError('Invalid YouTube playlist URL');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // First, get playlist items
      const playlistResponse = await fetch(`https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&maxResults=50&playlistId=${playlistId}&key=AIzaSyCMNrYa-BKiDwczZh99fMZEu9C4Hbxm9D4`);
      const playlistData = await playlistResponse.json();

      if (playlistData.error) {
        throw new Error(playlistData.error.message);
      }

      // Extract video IDs
      const videoIds = playlistData.items.map(item => item.contentDetails.videoId);

      // Get video details including duration
      const videoIdsString = videoIds.join(',');
      const videoResponse = await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=${videoIdsString}&key=AIzaSyCMNrYa-BKiDwczZh99fMZEu9C4Hbxm9D4`);
      const videoData = await videoResponse.json();

      if (videoData.error) {
        throw new Error(videoData.error.message);
      }

      // Create a map of video details
      const videoDetailsMap = {};
      videoData.items.forEach(video => {
        videoDetailsMap[video.id] = {
          duration: parseDuration(video.contentDetails.duration),
          title: video.snippet.title,
          thumbnail: video.snippet.thumbnails?.default?.url || ''
        };
      });

      // Combine playlist items with video details
      const videos = playlistData.items.map(item => {
        const videoId = item.contentDetails.videoId;
        const details = videoDetailsMap[videoId] || {};
        
        return {
          videoId: videoId,
          title: details.title || item.snippet.title,
          thumbnail: details.thumbnail || item.snippet.thumbnails?.default?.url || '',
          duration: details.duration || 600, // Fallback to 10 minutes if duration not found
          url: `https://www.youtube.com/watch?v=${videoId}`
        };
      });

      // Calculate total duration using actual video durations
      const totalSeconds = videos.reduce((sum, video) => sum + video.duration, 0);
      const totalMinutes = Math.ceil(totalSeconds / 60);
      const totalHours = Math.floor(totalMinutes / 60);
      const remainingMinutes = totalMinutes % 60;

      setPlaylistData({
        playlistId: playlistId,
        title: playlistData.items[0]?.snippet?.channelTitle || 'Playlist',
        videoCount: videos.length,
        totalDuration: `${totalHours}h ${remainingMinutes}m`,
        videos: videos
      });

    } catch (err) {
      setError(`Failed to fetch playlist: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to parse YouTube duration format (PT4M13S -> 253 seconds)
  const parseDuration = (duration) => {
    const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!match) return 600; // Default 10 minutes
    
    const hours = parseInt(match[1]) || 0;
    const minutes = parseInt(match[2]) || 0;
    const seconds = parseInt(match[3]) || 0;
    
    return hours * 3600 + minutes * 60 + seconds;
  };

  const generateSchedule = (videos, dailyMinutes) => {
    const schedule = [];
    let currentDay = 1;
    let currentDayVideos = [];
    let currentDayMinutes = 0;

    videos.forEach((video, index) => {
      const videoMinutes = Math.ceil(video.duration / 60);
      
      if (currentDayMinutes + videoMinutes <= dailyMinutes) {
        currentDayVideos.push(video);
        currentDayMinutes += videoMinutes;
      } else {
        // Save current day and start new day
        if (currentDayVideos.length > 0) {
          schedule.push({
            day: currentDay,
            videos: currentDayVideos,
            totalMinutes: currentDayMinutes
          });
        }
        currentDay++;
        currentDayVideos = [video];
        currentDayMinutes = videoMinutes;
      }
    });

    // Add the last day if it has videos
    if (currentDayVideos.length > 0) {
      schedule.push({
        day: currentDay,
        videos: currentDayVideos,
        totalMinutes: currentDayMinutes
      });
    }

    return schedule;
  };

  const saveToBackend = async () => {
    if (!playlistData) return;

    try {
      const schedule = generateSchedule(playlistData.videos, dailyMinutes);
      
      const scheduleData = {
        playlist_id: playlistData.playlistId,
        playlist_url: playlistUrl,
        playlist_title: playlistData.title,
        daily_minutes: dailyMinutes,
        schedule: schedule,
        start_time: startTime,
        duration_minutes: durationMinutes
      };

      await authenticatedFetch('/youtube-schedules', {
        method: 'POST',
        body: JSON.stringify(scheduleData)
      });

      // Reload schedules from backend
      await loadSchedules();
      
      // Clear current playlist
      setPlaylistData(null);
      setPlaylistUrl('');
      
      // Show success message
      alert('✅ Playlist saved successfully! You can now view it in your calendar.');
      
    } catch (error) {
      setError(`Failed to save schedule: ${error.message}`);
    }
  };

  const syncToGoogleCalendar = async (schedule) => {
    setSyncingToGoogle(true);
    try {
      // Call backend to sync all schedules to Google Calendar
      const response = await authenticatedFetch('/youtube-schedules/sync-all-to-google-calendar', {
        method: 'POST'
      });
      
      alert(`✅ Successfully synced ${response.events_created} events to your Google Calendar!`);
    } catch (error) {
      if (error.message.includes('must be authenticated with Google')) {
        alert('❌ Please connect your Google account first to sync to Google Calendar. Go to Settings to connect.');
      } else {
        setError(`Failed to sync to Google Calendar: ${error.message}`);
      }
    } finally {
      setSyncingToGoogle(false);
    }
  };

  const syncIndividualSchedule = async (scheduleId) => {
    try {
      const response = await authenticatedFetch(`/youtube-schedules/${scheduleId}/sync-to-google-calendar`, {
        method: 'POST'
      });
      
      alert(`✅ Successfully synced ${response.events_created} events from "${response.schedule_title}" to your Google Calendar!`);
    } catch (error) {
      if (error.message.includes('must be authenticated with Google')) {
        alert('❌ Please connect your Google account first to sync to Google Calendar. Go to Settings to connect.');
      } else {
        setError(`Failed to sync to Google Calendar: ${error.message}`);
      }
    }
  };

  const deleteSchedule = async (id) => {
    try {
      await authenticatedFetch(`/youtube-schedules/${id}`, {
        method: 'DELETE'
      });
      await loadSchedules();
    } catch (error) {
      setError(`Failed to delete schedule: ${error.message}`);
    }
  };

  const getTodaysVideos = () => {
    const today = new Date();
    const dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
    
    const todaysVideos = [];
    schedules.forEach(schedule => {
      schedule.schedule.forEach(daySchedule => {
        if (daySchedule.day === dayOfYear) {
          todaysVideos.push({
            ...daySchedule,
            playlistTitle: schedule.playlist_title
          });
        }
      });
    });
    
    return todaysVideos;
  };

  return (
    <Layout>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '700', color: '#1a1a1a', marginBottom: '2rem' }}>
          YouTube Learning
        </h1>

        {/* Input Section */}
        <div style={{ 
          background: '#fff', 
          padding: '2rem', 
          borderRadius: '16px', 
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          marginBottom: '2rem'
        }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '600', marginBottom: '1.5rem', color: '#333' }}>
            Add New Playlist
          </h2>
          
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#555' }}>
                YouTube Playlist URL
              </label>
              <input
                type="text"
                value={playlistUrl}
                onChange={(e) => setPlaylistUrl(e.target.value)}
                placeholder="https://www.youtube.com/playlist?list=..."
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '2px solid #e1e5e9',
                  borderRadius: '8px',
                  fontSize: '16px',
                  transition: 'border-color 0.2s ease'
                }}
              />
            </div>
            
            <div style={{ minWidth: '150px' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#555' }}>
                Daily Minutes
              </label>
              <input
                type="number"
                value={dailyMinutes}
                onChange={(e) => setDailyMinutes(parseInt(e.target.value))}
                min="10"
                max="180"
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
              onClick={fetchPlaylistData}
              disabled={loading}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#ff0000',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1
              }}
            >
              {loading ? 'Loading...' : 'Analyze Playlist'}
            </button>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <button
              onClick={() => setShowTimeOptions(!showTimeOptions)}
              style={{
                background: '#f3f4fd',
                color: '#4f8cff',
                border: 'none',
                borderRadius: '8px',
                padding: '0.5rem 1.2rem',
                fontWeight: 600,
                cursor: 'pointer',
                marginBottom: '0.5rem'
              }}
            >
              {showTimeOptions ? 'Hide' : 'Show'} Time Window Options
            </button>
            {showTimeOptions && (
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginTop: '0.5rem' }}>
                <div style={{ minWidth: '140px' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#555' }}>
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={startTime}
                    onChange={e => setStartTime(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '2px solid #e1e5e9',
                      borderRadius: '8px',
                      fontSize: '16px'
                    }}
                  />
                </div>
                <div style={{ minWidth: '120px' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#555' }}>
                    Duration (min)
                  </label>
                  <input
                    type="number"
                    value={durationMinutes}
                    onChange={e => setDurationMinutes(parseInt(e.target.value))}
                    min="10"
                    max="180"
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '2px solid #e1e5e9',
                      borderRadius: '8px',
                      fontSize: '16px'
                    }}
                  />
                </div>
                <div style={{ minWidth: '160px', alignSelf: 'center', color: '#4f8cff', fontWeight: 600 }}>
                  End Time: {(() => {
                    const [hours, minutes] = startTime.split(':').map(Number);
                    const start = new Date();
                    start.setHours(hours, minutes, 0, 0);
                    const end = new Date(start.getTime() + durationMinutes * 60000);
                    return end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  })()}
                </div>
              </div>
            )}
          </div>

          {error && (
            <div style={{ 
              background: '#fee', 
              color: '#c33', 
              padding: '0.75rem', 
              borderRadius: '8px', 
              marginTop: '1rem' 
            }}>
              {error}
            </div>
          )}
        </div>

        {/* Playlist Analysis */}
        {playlistData && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '16px', 
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            marginBottom: '2rem'
          }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1rem', color: '#333' }}>
              Playlist Analysis
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '2rem', fontWeight: '700', color: '#ff0000' }}>{playlistData.videoCount}</div>
                <div style={{ color: '#666' }}>Videos</div>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '2rem', fontWeight: '700', color: '#ff0000' }}>{playlistData.totalDuration}</div>
                <div style={{ color: '#666' }}>Total Duration</div>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <div style={{ fontSize: '2rem', fontWeight: '700', color: '#ff0000' }}>{Math.ceil(playlistData.videoCount * 10 / dailyMinutes)}</div>
                <div style={{ color: '#666' }}>Days to Complete</div>
              </div>
            </div>

            {/* Schedule Preview */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '1rem', color: '#333' }}>
                Your Learning Schedule
              </h4>
              <div style={{ display: 'grid', gap: '0.75rem' }}>
                {generateSchedule(playlistData.videos, dailyMinutes).map((daySchedule, index) => (
                  <div key={index} style={{ 
                    padding: '1rem', 
                    background: '#f8f9fa', 
                    borderRadius: '8px',
                    border: '1px solid #e1e5e9'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center', 
                      marginBottom: '0.5rem' 
                    }}>
                      <strong style={{ color: '#333' }}>Day {daySchedule.day}</strong>
                      <span style={{ 
                        background: '#ff0000', 
                        color: 'white', 
                        padding: '0.25rem 0.5rem', 
                        borderRadius: '4px', 
                        fontSize: '12px' 
                      }}>
                        {daySchedule.videos.length} videos • {daySchedule.totalMinutes} min
                      </span>
                    </div>
                    <div style={{ fontSize: '14px', color: '#666' }}>
                      {daySchedule.videos.map((video, videoIndex) => (
                        <div key={videoIndex} style={{ marginBottom: '0.25rem' }}>
                          • {video.title}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                onClick={saveToBackend}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Save to Learning Schedule
              </button>
              
              <button
                onClick={() => syncToGoogleCalendar()}
                disabled={syncingToGoogle}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: '#4285f4',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: syncingToGoogle ? 'not-allowed' : 'pointer',
                  opacity: syncingToGoogle ? 0.7 : 1
                }}
              >
                {syncingToGoogle ? 'Syncing...' : 'Sync to Google Calendar'}
              </button>
            </div>
          </div>
        )}

        {/* Today's Videos */}
        {getTodaysVideos().length > 0 && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '16px', 
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            marginBottom: '2rem'
          }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1rem', color: '#333' }}>
              Today's Videos
            </h3>
            
            {getTodaysVideos().map((daySchedule, index) => (
              <div key={index} style={{ marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '1.1rem', fontWeight: '600', color: '#555', marginBottom: '0.5rem' }}>
                  {daySchedule.playlistTitle}
                </h4>
                {daySchedule.videos.map((video, videoIndex) => (
                  <div key={videoIndex} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '1rem', 
                    padding: '0.75rem', 
                    background: '#f8f9fa', 
                    borderRadius: '8px', 
                    marginBottom: '0.5rem' 
                  }}>
                    <img 
                      src={video.thumbnail} 
                      alt={video.title}
                      style={{ width: '60px', height: '45px', borderRadius: '4px' }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '500', fontSize: '14px' }}>{video.title}</div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        {Math.ceil(video.duration / 60)} minutes
                      </div>
                    </div>
                    <a 
                      href={video.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#ff0000',
                        color: 'white',
                        textDecoration: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      Watch
                    </a>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Saved Playlists */}
        {schedules.length > 0 && (
          <div style={{ 
            background: '#fff', 
            padding: '2rem', 
            borderRadius: '16px', 
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)' 
          }}>
            <h3 style={{ fontSize: '1.3rem', fontWeight: '600', marginBottom: '1.5rem', color: '#333' }}>
              Your Learning Playlists
            </h3>
            
            <div style={{ display: 'grid', gap: '1rem' }}>
              {schedules.map((schedule) => (
                <div key={schedule.id} style={{ 
                  padding: '1.5rem', 
                  border: '2px solid #e1e5e9', 
                  borderRadius: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>
                      {schedule.playlist_title}
                    </h4>
                    <div style={{ color: '#666', fontSize: '14px' }}>
                      {schedule.schedule.length} days • {schedule.daily_minutes} minutes/day
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <a 
                      href={schedule.playlist_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#ff0000',
                        color: 'white',
                        textDecoration: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      View Playlist
                    </a>
                    
                    <button
                      onClick={() => syncIndividualSchedule(schedule.id)}
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#4285f4',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer'
                      }}
                    >
                      Sync to Calendar
                    </button>

                    <button
                      onClick={() => deleteSchedule(schedule.id)}
                      style={{
                        padding: '0.5rem 1rem',
                        background: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer'
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default YouTubeLearning; 