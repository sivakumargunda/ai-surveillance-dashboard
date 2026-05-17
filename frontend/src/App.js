import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import Sidebar from './components/Sidebar';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState({ state: 'checking', lastSync: null, message: '' });
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [livePeople, setLivePeople] = useState(0);
  const [dateRange, setDateRange] = useState('24h');
  const [liveStats, setLiveStats] = useState({ people: 0, vehicles: 0, fps: 0, tracked: 0 });
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [soundAlerts, setSoundAlerts] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedCamera, setSelectedCamera] = useState('cam-mobile-1');
  const [cameraList, setCameraList] = useState([]);
  const [newCameraUrl, setNewCameraUrl] = useState('');
  const [newCameraName, setNewCameraName] = useState('');
  const [cameraMessage, setCameraMessage] = useState('');
  const [zones, setZones] = useState([]);
  const [zoneName, setZoneName] = useState('');
  const [zoneType, setZoneType] = useState('intrusion');
  const [draftPoints, setDraftPoints] = useState([]);
  const [zoneMessage, setZoneMessage] = useState('');
  const [frameSize, setFrameSize] = useState({ width: 640, height: 480 });
  const [eventSearch, setEventSearch] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [eventStateFilter, setEventStateFilter] = useState('all');
  const [eventCameraFilter, setEventCameraFilter] = useState('all');
  const zoneImageRef = useRef(null);

  const parseJsonValue = (value, defaultValue) => {
    if (value === undefined || value === null) return defaultValue;
    if (typeof value === 'string') {
      try {
        return JSON.parse(value);
      } catch {
        return defaultValue;
      }
    }
    return value;
  };

  const getSnapshotFilename = (path) => path ? path.replace(/\\/g, '/').split('/').pop() : '';
  const getClipFilename = (path) => path ? path.replace(/\\/g, '/').split('/').pop() : '';
  const getApiErrorMessage = (error, fallback) => {
    const detail = error.response?.data?.detail || error.response?.data?.message;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg || JSON.stringify(item)).join(', ');
    }
    return detail || error.message || fallback;
  };

  const getStateBadge = (state) => ({
    start: 'START',
    active: 'ACTIVE',
    end: 'END',
  }[state] || 'UNKNOWN');

  const getActivityColor = (activityType) => ({
    crowd: '#3b82f6',
    zone_intrusion: '#ef4444',
  }[activityType] || '#6b7280');

  const getSeverity = (alert) => {
    if (alert.state === 'active') return 'critical';
    if (alert.state === 'start') return 'warning';
    return 'resolved';
  };

  const getSeverityLabel = (alert) => ({
    critical: 'Critical',
    warning: 'Warning',
    resolved: 'Resolved',
  }[getSeverity(alert)]);

  const markBackendOnline = () => {
    setBackendStatus({ state: 'online', lastSync: new Date(), message: '' });
  };

  const markBackendOffline = (error) => {
    setBackendStatus({
      state: 'offline',
      lastSync: backendStatus.lastSync,
      message: getApiErrorMessage(error, 'Backend offline. Check the API server and try again.'),
    });
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/alerts?limit=100`);
      setAlerts(response.data);
      const active = response.data.filter((alert) => alert.state === 'active');
      const totalPeople = active.reduce((sum, alert) => {
        return sum + (parseJsonValue(alert.extra_data, {}).count || 0);
      }, 0);
      setLivePeople(totalPeople);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/alerts/stats`);
      setStats(response.data);
      markBackendOnline();
    } catch (error) {
      console.error('Error fetching stats:', error);
      markBackendOffline(error);
    }
    setLoading(false);
  };

  const fetchLiveStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/live-stats`);
      setLiveStats(response.data);
    } catch (error) {
      console.error('Error fetching live stats:', error);
    }
  };

  const fetchCameras = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/cameras`);
      const cameras = response.data || [];
      setCameraList(cameras);
      if (!cameras.length) {
        setSelectedCamera('');
      } else if (!cameras.some((cam) => cam.id === selectedCamera)) {
        setSelectedCamera(cameras[0].id);
      }
    } catch (error) {
      console.error('Error fetching cameras:', error);
    }
  };

  const fetchZones = async (cameraId = selectedCamera) => {
    if (!cameraId) {
      setZones([]);
      return;
    }
    try {
      const response = await axios.get(`${API_BASE_URL}/zones/${encodeURIComponent(cameraId)}`);
      setZones(response.data || []);
    } catch (error) {
      console.error('Error fetching zones:', error);
    }
  };

  const addCamera = async (event) => {
    event.preventDefault();
    const url = newCameraUrl.trim();
    if (!url) {
      setCameraMessage('Please enter a camera URL.');
      return;
    }

    try {
      new URL(url);
    } catch {
      setCameraMessage('Please enter a valid URL (e.g., http://192.168.0.102:8080).');
      return;
    }

    try {
      const payload = {
        url,
        name: newCameraName.trim() || `Camera ${cameraList.length + 1}`,
      };
      const response = await axios.post(`${API_BASE_URL}/cameras`, payload);
      setCameraMessage(`Added camera ${response.data.id}`);
      setNewCameraUrl('');
      setNewCameraName('');
      fetchCameras();
    } catch (error) {
      console.error('Error adding camera:', error);
      setCameraMessage(getApiErrorMessage(error, 'Unable to add camera. Check the URL and try again.'));
    }
  };

  const deleteCamera = async (cameraId, event) => {
    event.stopPropagation(); // Prevent triggering the card click
    if (!window.confirm(`Are you sure you want to delete camera "${cameraId}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/cameras/${encodeURIComponent(cameraId)}`);
      setCameraMessage(`Camera ${cameraId} deleted successfully`);
      setCameraList((prevList) => prevList.filter((cam) => cam.id !== cameraId));
      if (selectedCamera === cameraId) {
        setSelectedCamera('');
      }
      setZones((prevZones) => prevZones.filter((zone) => zone.camera_id !== cameraId));
      await fetchCameras();
    } catch (error) {
      console.error('Error deleting camera:', error);
      const msg = getApiErrorMessage(error, 'Failed to delete camera. Please try again.');
      setCameraMessage(msg);
    }
  };

  const handleZoneImageLoad = (event) => {
    const width = event.target.naturalWidth || 640;
    const height = event.target.naturalHeight || 480;
    if (width > 1 && height > 1) {
      setFrameSize({ width, height });
    }
  };

  const addDraftPoint = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * frameSize.width;
    const y = ((event.clientY - bounds.top) / bounds.height) * frameSize.height;
    const clampedX = Math.max(0, Math.min(frameSize.width, Math.round(x)));
    const clampedY = Math.max(0, Math.min(frameSize.height, Math.round(y)));
    setDraftPoints((points) => [...points, [clampedX, clampedY]]);
  };

  const undoDraftPoint = () => {
    setDraftPoints((points) => points.slice(0, -1));
  };

  const clearDraftZone = () => {
    setDraftPoints([]);
    setZoneMessage('');
  };

  const saveZone = async () => {
    if (!selectedCamera) {
      setZoneMessage('Select a camera before saving a zone.');
      return;
    }
    if (draftPoints.length < 3) {
      setZoneMessage('Add at least three points to create a polygon.');
      return;
    }

    const name = zoneName.trim() || `${zoneType.replace('_', ' ')} zone`;
    try {
      await axios.post(`${API_BASE_URL}/zones`, {
        camera_id: selectedCamera,
        zone_name: name,
        zone_type: zoneType,
        points: draftPoints,
      });
      setZoneName('');
      setDraftPoints([]);
      setZoneMessage(`Saved ${name}`);
      await fetchZones(selectedCamera);
    } catch (error) {
      console.error('Error saving zone:', error);
      setZoneMessage(getApiErrorMessage(error, 'Unable to save zone.'));
    }
  };

  const deleteZone = async (zoneId) => {
    try {
      await axios.delete(`${API_BASE_URL}/zones/${zoneId}`);
      setZones((prevZones) => prevZones.filter((zone) => zone.id !== zoneId));
      setZoneMessage('Zone deleted');
    } catch (error) {
      console.error('Error deleting zone:', error);
      setZoneMessage(getApiErrorMessage(error, 'Unable to delete zone.'));
    }
  };

  const clearCameraZones = async () => {
    if (!selectedCamera) return;
    if (!window.confirm(`Delete all zones for "${selectedCamera}"?`)) {
      return;
    }
    try {
      await axios.delete(`${API_BASE_URL}/zones/camera/${encodeURIComponent(selectedCamera)}`);
      setZones((prevZones) => prevZones.filter((zone) => zone.camera_id !== selectedCamera));
      setDraftPoints([]);
      setZoneMessage(`Cleared zones for ${selectedCamera}`);
    } catch (error) {
      console.error('Error clearing zones:', error);
      setZoneMessage(getApiErrorMessage(error, 'Unable to clear zones.'));
    }
  };

  useEffect(() => {
    fetchAlerts();
    fetchStats();
    fetchLiveStats();
    fetchCameras();
    fetchZones();

    const interval = setInterval(() => {
      if (!autoRefresh) return;
      fetchAlerts();
      fetchStats();
      fetchLiveStats();
      fetchCameras();
      fetchZones();
    }, 3000);

    return () => clearInterval(interval);
  // Refresh functions intentionally read the current dashboard state on each timer tick.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRefresh]);

  useEffect(() => {
    fetchZones(selectedCamera);
    setDraftPoints([]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCamera]);

  const formatTimestamp = (timestamp) => new Date(timestamp).toLocaleTimeString();

  const getDayKey = (timestamp) => new Date(timestamp).toISOString().split('T')[0];

  const groupByDay = (items) => {
    const groups = {};
    items.forEach(item => {
      const day = getDayKey(item.timestamp);
      if (!groups[day]) groups[day] = [];
      groups[day].push(item);
    });
    return Object.entries(groups).map(([day, events]) => ({
      day,
      formattedDate: new Date(day).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' }),
      events: events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    })).sort((a, b) => new Date(b.day) - new Date(a.day));
  };

  const todayKey = getDayKey(new Date());
  const activeEvents = alerts.filter((alert) => 
    ['start', 'active'].includes(alert.state) && getDayKey(alert.timestamp) === todayKey
  );
  const recentEvents = alerts.filter((alert) => alert.state === 'end').slice(0, 10);
  const cameraStats = stats.by_camera || {};
  const activeCameras = cameraList.length > 0
    ? cameraList.map((cam) => ({
        cameraId: cam.id,
        count: cameraStats[cam.id] || 0,
        status: cam.status || 'offline',
        url: cam.url,
      }))
    : Object.entries(cameraStats).map(([cameraId, count]) => ({
        cameraId,
        count,
        status: 'online',
      }));
  const registeredCameras = cameraList.map((cam) => ({
    cameraId: cam.id,
    count: cameraStats[cam.id] || 0,
    status: cam.status || 'offline',
    url: cam.url,
  }));
  const typeData = Object.entries(stats.by_type || {}).map(([type, count]) => ({ name: type, value: count }));
  const cameraChartData = activeCameras.map((camera) => ({ name: camera.cameraId, count: camera.count }));
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
  const eventTypes = Array.from(new Set(alerts.map((alert) => alert.activity_type).filter(Boolean))).sort();
  const eventCameras = Array.from(new Set(alerts.map((alert) => alert.camera_id).filter(Boolean))).sort();
  const filteredAlerts = alerts.filter((alert) => {
    const query = eventSearch.trim().toLowerCase();
    const matchesSearch = !query || [
      alert.activity_type,
      alert.state,
      alert.camera_id,
      alert.track_ids?.join(' '),
      getSeverityLabel(alert),
    ].filter(Boolean).join(' ').toLowerCase().includes(query);
    const matchesType = eventTypeFilter === 'all' || alert.activity_type === eventTypeFilter;
    const matchesState = eventStateFilter === 'all' || alert.state === eventStateFilter;
    const matchesCamera = eventCameraFilter === 'all' || alert.camera_id === eventCameraFilter;
    return matchesSearch && matchesType && matchesState && matchesCamera;
  });
  const criticalEvents = activeEvents.filter((alert) => getSeverity(alert) === 'critical');
  const warningEvents = activeEvents.filter((alert) => getSeverity(alert) === 'warning');
  const offlineCameras = registeredCameras.filter((camera) => camera.status !== 'online');
  const lastSyncText = backendStatus.lastSync ? backendStatus.lastSync.toLocaleTimeString() : 'Not synced';
  const pageTitle = currentPage === 'dashboard'
    ? 'Dashboard'
    : currentPage.split('-').map((word) => word[0].toUpperCase() + word.slice(1)).join(' ');

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-panel">
          <div className="loading-mark">S</div>
          <h1>Loading command center</h1>
          <p>Checking API status, cameras, and recent events.</p>
          <div className="loading-bar"><span /></div>
        </div>
      </div>
    );
  }

  const renderPageHeader = (title) => (
    <div className="page-title-row">
      <h2>{title}</h2>
      {currentPage !== 'dashboard' && (
        <button className="back-button" onClick={() => setCurrentPage('dashboard')}>Back to dashboard</button>
      )}
    </div>
  );

  const downloadReport = (format) => {
    const rows = alerts.map((alert) => ({
      id: alert.id,
      type: alert.activity_type,
      state: alert.state,
      camera: alert.camera_id,
      time: alert.timestamp,
      people: parseJsonValue(alert.extra_data, {}).count || 0,
    }));
    const content = format === 'json'
      ? JSON.stringify(rows, null, 2)
      : [
          'id,type,state,camera,time,people',
          ...rows.map((row) => [row.id, row.type, row.state, row.camera, row.time, row.people].join(','))
        ].join('\\n');
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `surveillance-report.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const renderEventList = (items, emptyText) => {
    const dayGroups = groupByDay(items);
    return (
      <div className="events-table">
        {dayGroups.length === 0 && <div className="empty-state">{emptyText}</div>}
        {dayGroups.map(({ day, formattedDate, events }) => (
          <div key={day} className="day-group">
            <div className="day-header">
              <h4>{formattedDate}</h4>
              <span className="event-count">{events.length} events</span>
            </div>
            {events.map((alert) => (
              <div key={alert.id} className="event-row" onClick={() => setSelectedAlert(alert)}>
                <div className="event-row-main">
                  <span className="activity-dot" style={{ backgroundColor: getActivityColor(alert.activity_type) }} />
                  <div>
                    <div className="activity-name">{alert.activity_type.toUpperCase()}</div>
                    <div className="recent-details">
                      Camera: {alert.camera_id} | Tracks: {alert.track_ids?.join(', ') || 'none'}
                      {parseJsonValue(alert.extra_data, {}).clip_path ? ' | Clip available' : ''}
                    </div>
                  </div>
                </div>
                <div className="event-row-meta">
                  <div className="state-badge">{getStateBadge(alert.state)}</div>
                  <div>{formatTimestamp(alert.timestamp)}</div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };

  const renderStatusNotice = () => {
    if (backendStatus.state !== 'offline') return null;
    return (
      <div className="status-notice status-notice-error">
        <div>
          <strong>Backend offline</strong>
          <span>{backendStatus.message}</span>
        </div>
        <button type="button" onClick={() => { fetchAlerts(); fetchStats(); fetchLiveStats(); fetchCameras(); }}>Retry</button>
      </div>
    );
  };

  const renderEventTable = (items, emptyText) => (
    <div className="event-table-shell">
      {items.length === 0 ? (
        <div className="empty-state">
          <strong>{emptyText}</strong>
          <span>Try changing the filters or refreshing the event feed.</span>
        </div>
      ) : (
        <table className="event-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Event</th>
              <th>Camera</th>
              <th>People</th>
              <th>Tracks</th>
              <th>Time</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((alert) => (
              <tr key={alert.id} onClick={() => setSelectedAlert(alert)}>
                <td><span className={`severity-pill severity-${getSeverity(alert)}`}>{getSeverityLabel(alert)}</span></td>
                <td>
                  <div className="event-name-cell">
                    <span className="activity-dot" style={{ backgroundColor: getActivityColor(alert.activity_type) }} />
                    <span>{alert.activity_type.replace('_', ' ').toUpperCase()}</span>
                  </div>
                </td>
                <td>{alert.camera_id}</td>
                <td>{parseJsonValue(alert.extra_data, {}).count || 0}</td>
                <td>{alert.track_ids?.join(', ') || 'none'}</td>
                <td>{formatTimestamp(alert.timestamp)}</td>
                <td><span className="state-badge">{getStateBadge(alert.state)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );

  const renderDashboard = () => (
    <div className="ops-overview">
      {renderStatusNotice()}
      <section className="ops-hero">
        <div>
          <div className="eyebrow">Operations overview</div>
          <h2>{criticalEvents.length ? `${criticalEvents.length} active critical event${criticalEvents.length > 1 ? 's' : ''}` : 'All monitored zones normal'}</h2>
          <p>Live camera health, alert triage, and detection trends for the current command cycle.</p>
        </div>
        <div className={`system-health health-${backendStatus.state}`}>
          <span className="status-dot" />
          <div>
            <strong>{backendStatus.state === 'online' ? 'API online' : backendStatus.state === 'offline' ? 'API offline' : 'Checking API'}</strong>
            <span>Last sync: {lastSyncText}</span>
          </div>
        </div>
      </section>

      <section className="ops-grid">
        <button className="metric-tile metric-danger" onClick={() => setCurrentPage('active-events')}>
          <span>Critical active</span>
          <strong>{criticalEvents.length}</strong>
          <small>{warningEvents.length} warnings queued</small>
        </button>
        <button className="metric-tile" onClick={() => setCurrentPage('active-cameras')}>
          <span>Cameras online</span>
          <strong>{Math.max(registeredCameras.length - offlineCameras.length, 0)}</strong>
          <small>{offlineCameras.length} offline</small>
        </button>
        <button className="metric-tile" onClick={() => setCurrentPage('total-events')}>
          <span>Events today</span>
          <strong>{activeEvents.length + recentEvents.length}</strong>
          <small>{stats.total || 0} total retained</small>
        </button>
        <div className="metric-tile">
          <span>Live people</span>
          <strong>{liveStats.people ?? livePeople}</strong>
          <small>{liveStats.tracked ?? 0} tracked objects</small>
        </div>
      </section>

      <section className="ops-main-grid">
        <div className="active-events panel">
          <div className="panel-header">
            <h2>Priority Queue</h2>
            <button type="button" className="link-button" onClick={() => setCurrentPage('events')}>Open all events</button>
          </div>
          <div className="active-events-row">
            {activeEvents.slice(0, 4).map((alert) => (
              <div
                key={alert.id}
                className="horizontal-card"
                onClick={() => setSelectedAlert(alert)}
                style={{ borderLeftColor: getActivityColor(alert.activity_type) }}
              >
                <div className={`card-icon severity-${getSeverity(alert)}`}>{getSeverityLabel(alert)}</div>
                <div className="card-info">
                  <div className="activity-name">{alert.activity_type.replace('_', ' ').toUpperCase()}</div>
                  <div className="people-count">Camera {alert.camera_id} | People {parseJsonValue(alert.extra_data, {}).count || 0}</div>
                </div>
                <div className="card-arrow">Review</div>
              </div>
            ))}
            {activeEvents.length === 0 && <div className="no-active"><strong>System normal</strong><span>No active events require attention.</span></div>}
          </div>
        </div>

        <div className="camera-health panel">
          <div className="panel-header">
            <h2>Camera Health</h2>
            <button type="button" className="link-button" onClick={() => setCurrentPage('live-view')}>Live grid</button>
          </div>
          {registeredCameras.length === 0 ? (
            <div className="empty-state"><strong>No cameras configured</strong><span>Add a camera to start monitoring.</span></div>
          ) : registeredCameras.slice(0, 5).map((camera) => (
            <div className="camera-health-row" key={camera.cameraId}>
              <div>
                <strong>{camera.cameraId}</strong>
                <span>{camera.url || 'No source URL'}</span>
              </div>
              <span className={`camera-status-pill ${camera.status === 'online' ? 'online' : 'offline'}`}>{camera.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="ops-main-grid">
        <div className="chart-card">
          <h3>Events by Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={typeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={78}>
                {typeData.map((entry, index) => <Cell fill={COLORS[index % COLORS.length]} key={entry.name} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-card">
          <h3>Recent Activity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={recentEvents.slice(0, 12).reverse().map((alert) => ({ time: formatTimestamp(alert.timestamp), count: 1 }))}>
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );

  const renderCurrentPage = () => {
    if (currentPage === 'live-view') {
      return (
        <div className="page-panel">
          {renderStatusNotice()}
          {renderPageHeader('Live View')}
          <div className="camera-selector control-strip">
            <select value={selectedCamera} onChange={(e) => setSelectedCamera(e.target.value)}>
              {activeCameras.length === 0 && <option value="">No cameras available</option>}
              {activeCameras.map((camera) => (
                <option key={camera.cameraId} value={camera.cameraId}>{camera.cameraId}</option>
              ))}
            </select>
            <button type="button" className="back-button" onClick={fetchCameras}>Refresh cameras</button>
          </div>
          <div className="camera-mosaic">
            {registeredCameras.length === 0 && <div className="empty-state"><strong>No cameras configured</strong><span>Add a camera before opening live monitoring.</span></div>}
            {registeredCameras.map((camera) => (
              <button
                type="button"
                className={`mosaic-tile ${selectedCamera === camera.cameraId ? 'selected' : ''}`}
                key={camera.cameraId}
                onClick={() => setSelectedCamera(camera.cameraId)}
              >
                <img src={`${API_BASE_URL}/stream/${camera.cameraId}`} alt={`${camera.cameraId} stream`} />
                <span className="mosaic-gradient" />
                <span className={`camera-status-pill ${camera.status === 'online' ? 'online' : 'offline'}`}>{camera.status}</span>
                <strong>{camera.cameraId}</strong>
                <small>{cameraStats[camera.cameraId] || 0} alerts today</small>
              </button>
            ))}
          </div>
          <div className="live-view-grid">
            <div className="live-preview">
              <div className="preview-topbar">
                <div>
                  <div className="preview-label">Camera {selectedCamera}</div>
                  <div className="preview-subtitle">Primary live feed with detection overlay</div>
                </div>
                <span className="recording-pill">Live</span>
              </div>
              <div className="camera-stage">
                <div className="camera-frame">
                  <span className="corner top-left" />
                  <span className="corner top-right" />
                  <span className="corner bottom-left" />
                  <span className="corner bottom-right" />
                  {!selectedCamera && <div className="camera-frame-text">Select a camera</div>}
                  {selectedCamera && <img src={`${API_BASE_URL}/stream/${selectedCamera}`} alt="Live Camera Feed" />}
                  <div className="camera-overlay top-overlay">
                    <span>{selectedCamera || 'No camera'}</span>
                    <span>{backendStatus.state === 'online' ? 'Signal locked' : 'Signal pending'}</span>
                  </div>
                  <div className="camera-overlay bottom-overlay">
                    <span>People {liveStats.people ?? livePeople}</span>
                    <span>FPS {Number(liveStats.fps || 0).toFixed(1)}</span>
                    <span>Tracked {liveStats.tracked ?? 0}</span>
                  </div>
                </div>
              </div>
              <div className="preview-metrics">
                <span><strong>{liveStats.people ?? livePeople}</strong>People</span>
                <span><strong>{liveStats.tracked ?? 0}</strong>Tracked</span>
                <span><strong>{Number(liveStats.fps || 0).toFixed(1)}</strong>FPS</span>
              </div>
            </div>
            <div className="live-side-panel">
              <h3>Live Events</h3>
              {renderEventList(activeEvents.slice(0, 6), 'No live events right now')}
            </div>
          </div>
        </div>
      );
    }

    if (currentPage === 'events') {
      return (
        <div className="page-panel">
          {renderStatusNotice()}
          {renderPageHeader('Events')}
          <div className="event-command-bar">
            <div className="event-search">
              <input
                type="search"
                placeholder="Search camera, event, state, or track"
                value={eventSearch}
                onChange={(event) => setEventSearch(event.target.value)}
              />
            </div>
            <select value={eventTypeFilter} onChange={(event) => setEventTypeFilter(event.target.value)}>
              <option value="all">All types</option>
              {eventTypes.map((type) => <option value={type} key={type}>{type}</option>)}
            </select>
            <select value={eventStateFilter} onChange={(event) => setEventStateFilter(event.target.value)}>
              <option value="all">All states</option>
              <option value="start">Start</option>
              <option value="active">Active</option>
              <option value="end">End</option>
            </select>
            <select value={eventCameraFilter} onChange={(event) => setEventCameraFilter(event.target.value)}>
              <option value="all">All cameras</option>
              {eventCameras.map((camera) => <option value={camera} key={camera}>{camera}</option>)}
            </select>
            <button className="back-button" onClick={fetchAlerts}>Refresh</button>
          </div>
          <div className="event-results-summary">
            Showing {filteredAlerts.length} of {alerts.length} events
          </div>
          {renderEventTable(filteredAlerts, 'No matching events')}
        </div>
      );
    }

    if (currentPage === 'zones') {
      const selectedZones = zones.filter((zone) => zone.camera_id === selectedCamera);
      const hasSelectedCamera = Boolean(selectedCamera && registeredCameras.some((camera) => camera.cameraId === selectedCamera));
      return (
        <div className="page-panel">
          {renderPageHeader('Zones')}
          <div className="zone-workspace">
            <div className="zone-editor">
              <div className="zone-toolbar">
                <select value={selectedCamera} onChange={(e) => setSelectedCamera(e.target.value)}>
                  {registeredCameras.length === 0 && <option value="">No registered cameras</option>}
                  {registeredCameras.map((camera) => (
                    <option key={camera.cameraId} value={camera.cameraId}>{camera.cameraId}</option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Zone name"
                  value={zoneName}
                  onChange={(event) => setZoneName(event.target.value)}
                />
                <select value={zoneType} onChange={(event) => setZoneType(event.target.value)}>
                  <option value="intrusion">Intrusion</option>
                  <option value="queue">Queue</option>
                  <option value="fire_risk">Fire Risk</option>
                </select>
                <button type="button" className="back-button" onClick={undoDraftPoint} disabled={!draftPoints.length}>Undo Point</button>
                <button type="button" className="back-button" onClick={clearDraftZone}>Clear</button>
                <button type="button" className="view-camera-btn" onClick={saveZone} disabled={!hasSelectedCamera}>Save Zone</button>
              </div>
              {zoneMessage && <div className="form-message">{zoneMessage}</div>}
              <div
                className={`zone-canvas ${hasSelectedCamera ? '' : 'zone-canvas-disabled'}`}
                style={{ aspectRatio: `${frameSize.width} / ${frameSize.height}` }}
                onClick={hasSelectedCamera ? addDraftPoint : undefined}
              >
                {hasSelectedCamera ? (
                  <img
                    ref={zoneImageRef}
                    src={`${API_BASE_URL}/stream/${selectedCamera}`}
                    alt="Zone editor camera feed"
                    onLoad={handleZoneImageLoad}
                  />
                ) : (
                  <div className="zone-empty-state">Add or select a camera to draw zones</div>
                )}
                <svg viewBox={`0 0 ${frameSize.width} ${frameSize.height}`} preserveAspectRatio="none">
                  {selectedZones.map((zone) => (
                    <g key={zone.id}>
                      <polygon points={zone.points.map((point) => point.join(',')).join(' ')} className={`zone-polygon zone-${zone.zone_type}`} />
                      <text x={zone.points[0]?.[0] || 8} y={(zone.points[0]?.[1] || 8) + 18}>{zone.zone_name}</text>
                    </g>
                  ))}
                  {draftPoints.length > 0 && (
                    <g>
                      <polyline points={draftPoints.map((point) => point.join(',')).join(' ')} className="zone-draft-line" />
                      {draftPoints.length >= 3 && <polygon points={draftPoints.map((point) => point.join(',')).join(' ')} className="zone-draft-fill" />}
                      {draftPoints.map(([x, y], index) => (
                        <circle key={`${x}-${y}-${index}`} cx={x} cy={y} r="5" className="zone-point" />
                      ))}
                    </g>
                  )}
                </svg>
              </div>
            </div>

            <div className="zone-list-panel">
              <div className="zone-list-header">
                <h3>Camera Zones</h3>
                <button
                  type="button"
                  className="back-button"
                  onClick={clearCameraZones}
                  disabled={!selectedZones.length}
                >
                  Clear All
                </button>
              </div>
              {selectedZones.length === 0 && <div className="empty-state">No zones configured for this camera</div>}
              {selectedZones.map((zone) => (
                <div className="zone-row" key={zone.id}>
                  <div>
                    <div className="camera-name">{zone.zone_name}</div>
                    <div className="recent-details">{zone.zone_type} | {zone.points.length} points</div>
                  </div>
                  <button type="button" className="delete-camera-btn" onClick={() => deleteZone(zone.id)}>Delete</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (currentPage === 'cameras') {
      return (
        <div className="page-panel">
          {renderPageHeader('Cameras')}
          <div className="camera-form-panel">
            <h3>Add camera URL</h3>
            <form className="camera-form" onSubmit={addCamera}>
              <input
                type="text"
                placeholder="Enter RTSP / MJPEG camera URL"
                value={newCameraUrl}
                onChange={(event) => setNewCameraUrl(event.target.value)}
              />
              <input
                type="text"
                placeholder="Optional camera name"
                value={newCameraName}
                onChange={(event) => setNewCameraName(event.target.value)}
              />
              <button type="submit">Connect Camera</button>
            </form>
            {cameraMessage && <div className="form-message">{cameraMessage}</div>}
          </div>

          <div className="camera-grid">
            {registeredCameras.length === 0 && <div className="empty-state">No registered cameras found</div>}
            {registeredCameras.map((camera) => (
              <div className="camera-card" key={camera.cameraId}>
                <div>
                  <div className="camera-name">{camera.cameraId}</div>
                  <div className="camera-status">{camera.status === 'online' ? 'Online' : 'Offline'}</div>
                  <div className="recent-details">{camera.url}</div>
                </div>
                <div className="camera-actions">
                  <button
                    type="button"
                    className="delete-camera-btn"
                    onClick={(e) => deleteCamera(camera.cameraId, e)}
                    title="Delete camera"
                  >
                    Delete
                  </button>
                  <button
                    type="button"
                    className="view-camera-btn"
                    onClick={() => {
                      setSelectedCamera(camera.cameraId);
                      setCurrentPage('live-view');
                    }}
                  >
                    Live
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (currentPage === 'analytics') {
      return (
        <div className="page-panel">
          {renderPageHeader('Analytics')}
          <div className="analytics-grid">
            <div className="chart-card">
              <h3>Events by Type</h3>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={typeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={82}>
                    {typeData.map((entry, index) => <Cell fill={COLORS[index % COLORS.length]} key={entry.name} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-card">
              <h3>Events by Camera</h3>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={cameraChartData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      );
    }

    if (currentPage === 'reports') {
      return (
        <div className="page-panel">
          {renderPageHeader('Reports')}
          <div className="report-grid">
            <div className="report-panel">
              <h3>Event Summary</h3>
              <p>Total events: {stats.total || 0}</p>
              <p>Active events: {activeEvents.length}</p>
              <p>Active cameras: {activeCameras.length}</p>
            </div>
            <div className="report-panel">
              <h3>Export</h3>
              <div className="toolbar-row">
                <button className="back-button" onClick={() => downloadReport('csv')}>Download CSV</button>
                <button className="back-button" onClick={() => downloadReport('json')}>Download JSON</button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (currentPage === 'settings') {
      return (
        <div className="page-panel">
          {renderPageHeader('Settings')}
          <div className="settings-panel">
            <label className="setting-row">
              <span>Auto refresh dashboard data</span>
              <input type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} />
            </label>
            <label className="setting-row">
              <span>Sound alerts</span>
              <input type="checkbox" checked={soundAlerts} onChange={(event) => setSoundAlerts(event.target.checked)} />
            </label>
            <div className="setting-row">
              <span>API endpoint</span>
              <code>{API_BASE_URL}</code>
            </div>
            <div className="toolbar-row">
              <button className="back-button" onClick={() => { fetchAlerts(); fetchStats(); fetchLiveStats(); }}>Refresh now</button>
            </div>
          </div>
        </div>
      );
    }

    if (currentPage === 'total-events') {
      return (
        <div className="page-panel">
          {renderPageHeader('Total Events')}
          {renderEventList(alerts, 'No events recorded yet')}
        </div>
      );
    }

    if (currentPage === 'active-events') {
      return (
        <div className="page-panel">
          {renderPageHeader('Active Events')}
          {renderEventList(activeEvents, 'No active events right now')}
        </div>
      );
    }

    if (currentPage === 'active-cameras') {
      return (
        <div className="page-panel">
          {renderPageHeader('Active Cameras')}
          <div className="camera-grid">
            {activeCameras.length === 0 && <div className="empty-state">No active cameras found</div>}
            {activeCameras.map((camera) => (
              <div className="camera-card" key={camera.cameraId}>
                <div>
                  <div className="camera-name">{camera.cameraId}</div>
                  <div className="camera-status">Online</div>
                </div>
                <div className="camera-count">{camera.count}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return renderDashboard();
  };

  return (
    <div className="app">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <div className="main-layout">
        <nav className="navbar">
          <div>
            <span>{pageTitle}</span>
            <div className="navbar-subtitle">Real-time surveillance operations</div>
          </div>
          <div className="navbar-right">
            <div className={`connection-pill ${backendStatus.state}`}>
              <span className="status-dot" />
              {backendStatus.state === 'online' ? 'API online' : backendStatus.state === 'offline' ? 'API offline' : 'Checking'}
            </div>
            <select value={dateRange} onChange={(e) => setDateRange(e.target.value)}>
              <option>24h</option>
              <option>7d</option>
              <option>30d</option>
            </select>
            <div className="user-profile">User</div>
          </div>
        </nav>

        <header className="header">
          <div className="header-left">
            <div>
              <h1>Surveillance Dashboard</h1>
              <p>Live detection, event triage, camera health, and reporting in one workspace.</p>
            </div>
            <span className="live-tag">LIVE</span>
          </div>
          <div className="stats-summary">
            <button className="stat-card clickable-stat" onClick={() => setCurrentPage('total-events')}>
              <div>Total Events</div>
              <div>{stats.total || 0}</div>
            </button>
            <button className="stat-card clickable-stat" onClick={() => setCurrentPage('active-events')}>
              <div>Active Events</div>
              <div>{activeEvents.length}</div>
            </button>
            <button className="stat-card clickable-stat" onClick={() => setCurrentPage('active-cameras')}>
              <div>Active Cameras</div>
              <div>{activeCameras.length}</div>
            </button>
            <div className="stat-card">
              <div>Live People</div>
              <div>{liveStats.people ?? livePeople}</div>
            </div>
          </div>
        </header>

        {renderCurrentPage()}
      </div>

      {selectedAlert && (
        <div className="modal">
          <div className="modal-content">
            <h2>Event Details</h2>
            <div className="event-summary">
              <span className="activity-badge-large">{selectedAlert.activity_type.toUpperCase()}</span>
              <span className="state-badge-large">{getStateBadge(selectedAlert.state)}</span>
              <p>Camera: {selectedAlert.camera_id}</p>
              <p>People: {parseJsonValue(selectedAlert.extra_data, {}).count || 0}</p>
              <p>Time: {formatTimestamp(selectedAlert.timestamp)}</p>
            </div>
            {selectedAlert.snapshot_path && (
              <img
                src={`${API_BASE_URL}/snapshots/${getSnapshotFilename(selectedAlert.snapshot_path)}`}
                alt="Snapshot"
                className="modal-snapshot"
              />
            )}
            {parseJsonValue(selectedAlert.extra_data, {}).clip_path && (
              <video
                controls
                className="modal-clip"
                src={`${API_BASE_URL}/clips/${getClipFilename(parseJsonValue(selectedAlert.extra_data, {}).clip_path)}`}
              />
            )}
            <button onClick={() => setSelectedAlert(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
