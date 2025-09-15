import React, { useState, useEffect } from 'react';
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import Layout from './Layout';
import { authenticatedFetch } from '../api';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const locales = {
  'en-US': require('date-fns/locale/en-US')
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

const Calendar = () => {
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedEvents, setSelectedEvents] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [schedules, setSchedules] = useState([]);

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      const response = await authenticatedFetch('/youtube-schedules', {
        method: 'GET'
      });
      setSchedules(response);
      generateEvents(response);
    } catch (error) {
      console.error('Failed to load schedules:', error);
    }
  };

  const generateEvents = (schedules) => {
    const calendarEvents = [];
    const today = new Date();
    schedules.forEach(schedule => {
      const startTime = schedule.start_time || '21:00';
      const duration = schedule.duration_minutes || 60;
      const [hour, minute] = startTime.split(':').map(Number);
      schedule.schedule.forEach(daySchedule => {
        // Calculate the actual date for this day (starting from today)
        const eventDate = new Date(today);
        eventDate.setDate(today.getDate() + daySchedule.day - 1);
        const perVideo = Math.max(1, Math.floor(duration / Math.max(1, daySchedule.videos.length)));
        let currentTime = new Date(eventDate.setHours(hour, minute, 0, 0));
        daySchedule.videos.forEach((video, index) => {
          const eventStart = new Date(currentTime);
          const eventEnd = new Date(currentTime.getTime() + perVideo * 60 * 1000);
          calendarEvents.push({
            id: `${schedule.id}-${daySchedule.day}-${index}`,
            title: `${video.title} (${schedule.playlist_title})`,
            start: eventStart,
            end: eventEnd,
            video: video,
            playlistTitle: schedule.playlist_title,
            resource: {
              videoUrl: video.url,
              thumbnail: video.thumbnail,
              duration: video.duration
            }
          });
          currentTime = new Date(currentTime.getTime() + perVideo * 60 * 1000);
        });
      });
    });
    setEvents(calendarEvents);
  };

  const handleSelectEvent = (event) => {
    setSelectedDate(event.start);
    setSelectedEvents([event]);
    setShowModal(true);
  };

  const handleSelectSlot = (slotInfo) => {
    setSelectedDate(slotInfo.start);
    const dayEvents = events.filter(event => 
      format(event.start, 'yyyy-MM-dd') === format(slotInfo.start, 'yyyy-MM-dd')
    );
    setSelectedEvents(dayEvents);
    setShowModal(true);
  };

  const markAsWatched = (eventId) => {
    // This would update the backend to mark a video as watched
    // For now, we'll just remove it from the local events
    setEvents(events.filter(event => event.id !== eventId));
    setSelectedEvents(selectedEvents.filter(event => event.id !== eventId));
  };

  const eventStyleGetter = (event) => {
    return {
      style: {
        backgroundColor: '#ff0000',
        color: 'white',
        borderRadius: '8px',
        border: 'none',
        padding: '4px 8px',
        fontSize: '12px',
        fontWeight: '500',
        boxShadow: '0 2px 4px rgba(255, 0, 0, 0.3)'
      }
    };
  };

  const dayStyleGetter = (date) => {
    const dayEvents = events.filter(event => 
      format(event.start, 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd')
    );
    
    if (dayEvents.length > 0) {
      return {
        style: {
          backgroundColor: '#fff3f3',
          borderRadius: '8px'
        }
      };
    }
    return {};
  };

  return (
    <Layout>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '700', color: '#1a1a1a', marginBottom: '2rem' }}>
          Learning Calendar
        </h1>

        {/* Calendar Stats */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '1rem', 
          marginBottom: '2rem' 
        }}>
          <div style={{ 
            background: '#fff', 
            padding: '1.5rem', 
            borderRadius: '12px', 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700', color: '#ff0000' }}>
              {events.length}
            </div>
            <div style={{ color: '#666', fontSize: '14px' }}>Total Videos</div>
          </div>
          
          <div style={{ 
            background: '#fff', 
            padding: '1.5rem', 
            borderRadius: '12px', 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700', color: '#ff0000' }}>
              {schedules.length}
            </div>
            <div style={{ color: '#666', fontSize: '14px' }}>Active Playlists</div>
          </div>
          
          <div style={{ 
            background: '#fff', 
            padding: '1.5rem', 
            borderRadius: '12px', 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700', color: '#ff0000' }}>
              {new Set(events.map(e => format(e.start, 'yyyy-MM-dd'))).size}
            </div>
            <div style={{ color: '#666', fontSize: '14px' }}>Days with Videos</div>
          </div>
        </div>

        {/* Calendar */}
        <div style={{ 
          background: '#fff', 
          padding: '2rem', 
          borderRadius: '16px', 
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          height: '600px'
        }}>
          <BigCalendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            style={{ height: '100%' }}
            onSelectEvent={handleSelectEvent}
            onSelectSlot={handleSelectSlot}
            selectable
            eventPropGetter={eventStyleGetter}
            dayPropGetter={dayStyleGetter}
            views={['month', 'week', 'day']}
            defaultView="month"
            popup
            tooltipAccessor={(event) => `${event.title}\nDuration: ${Math.ceil(event.resource.duration / 60)} minutes`}
          />
        </div>

        {/* Event Details Modal */}
        {showModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}>
            <div style={{
              background: '#fff',
              borderRadius: '16px',
              padding: '2rem',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#333' }}>
                  {format(selectedDate, 'EEEE, MMMM d, yyyy')}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '1.5rem',
                    cursor: 'pointer',
                    color: '#666'
                  }}
                >
                  ×
                </button>
              </div>

              {selectedEvents.length === 0 ? (
                <p style={{ color: '#666', textAlign: 'center' }}>No videos scheduled for this day.</p>
              ) : (
                <div style={{ display: 'grid', gap: '1rem' }}>
                  {selectedEvents.map((event, index) => (
                    <div key={event.id} style={{
                      padding: '1rem',
                      border: '2px solid #e1e5e9',
                      borderRadius: '12px',
                      background: '#f8f9fa'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                        <img 
                          src={event.resource.thumbnail} 
                          alt={event.title}
                          style={{ width: '80px', height: '60px', borderRadius: '8px' }}
                        />
                        <div style={{ flex: 1 }}>
                          <h4 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#333' }}>
                            {event.title}
                          </h4>
                          <div style={{ fontSize: '14px', color: '#666', marginBottom: '0.5rem' }}>
                            Duration: {Math.ceil(event.resource.duration / 60)} minutes
                          </div>
                          <div style={{ fontSize: '12px', color: '#888' }}>
                            {format(event.start, 'h:mm a')} - {format(event.end, 'h:mm a')}
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          <a 
                            href={event.resource.videoUrl} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{
                              padding: '0.5rem 1rem',
                              background: '#ff0000',
                              color: 'white',
                              textDecoration: 'none',
                              borderRadius: '6px',
                              fontSize: '14px',
                              fontWeight: '500',
                              textAlign: 'center'
                            }}
                          >
                            Watch
                          </a>
                          <button
                            onClick={() => markAsWatched(event.id)}
                            style={{
                              padding: '0.5rem 1rem',
                              background: '#28a745',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              fontSize: '14px',
                              fontWeight: '500',
                              cursor: 'pointer'
                            }}
                          >
                            Mark Watched
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Calendar; 