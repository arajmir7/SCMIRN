import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { Circle, LayersControl, MapContainer, Marker, Popup, ScaleControl, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import L, { type Map as LeafletMap, type Marker as LeafletMarker } from 'leaflet';
import type { CivicLocation } from '@/app/UiContext';
import type { CivicIssue } from '@/types/issue';
import { geocodePlace } from '@/services/geocoding';

type IssueFilter = 'all' | 'critical' | 'high';

interface CivicIssueMapProps {
  title: string;
  description: string;
  issues: CivicIssue[];
  loading?: boolean;
  error?: string | null;
  onRefresh: () => void;
  onLocation?: (location: CivicLocation) => void;
  showRecentReports?: boolean;
  className?: string;
}

const fallbackCenter: [number, number] = [28.6139, 77.209];
const priorityColors: Record<CivicIssue['priority'], string> = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#06b6d4',
  low: '#06b6d4',
};

function safePhoto(value?: string): string {
  if (!value) return '/images/issue-placeholder.svg';
  if (value.startsWith('/')) return value;
  return '/images/issue-placeholder.svg';
}

function priorityIcon(priority: CivicIssue['priority']) {
  const size = priority === 'critical' ? 30 : priority === 'high' ? 24 : 20;
  const color = priorityColors[priority];
  const inner = priority === 'critical' ? '<span>!</span>' : '';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div class="civic-issue-marker civic-issue-marker-${priority}" style="--marker-color:${color};width:${size}px;height:${size}px">${inner}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function MapCapture({ onReady }: { onReady: (map: LeafletMap) => void }) {
  const map = useMap();
  useEffect(() => onReady(map), [map, onReady]);
  return null;
}

function IssuePopup({ issue }: { issue: CivicIssue }) {
  const badgeClass = issue.priority === 'critical' ? 'bg-danger' : issue.priority === 'high' ? 'bg-warning text-dark' : 'bg-info text-dark';

  return (
    <div className="issue-popup-content">
      <img src={safePhoto(issue.photos[0])} alt="" className="issue-popup-image" />
      <div className="fw-bold mb-2 issue-popup-title">{issue.title}</div>
      <div className="issue-popup-description">{issue.description.length > 120 ? `${issue.description.slice(0, 120)}...` : issue.description}</div>
      <div className="d-flex gap-2 mb-3">
        <span className={`badge ${badgeClass}`}>{issue.priority}</span>
        <span className="badge bg-light text-dark border">{issue.category}</span>
      </div>
      <p className="small text-muted mb-3">SCMIRN record · not verified by an agency · no funding is collected here</p>
      <a className="btn btn-sm btn-outline-secondary w-100" target="_blank" rel="noopener noreferrer"
        href={`https://www.google.com/maps/dir/?api=1&destination=${issue.lat},${issue.lng}&travelmode=driving`}>
        <i className="fas fa-directions me-1" aria-hidden="true" />Directions
      </a>
    </div>
  );
}

function formatCompact(value: string, limit: number): string {
  return value.length > limit ? `${value.slice(0, limit)}...` : value;
}

export function RecentReports({ issues }: { issues: CivicIssue[] }) {
  return (
    <div className="bg-white rounded-4 p-4 shadow-sm h-100">
      <h2 className="h5 fw-bold mb-4">Recent Reports</h2>
      <div className="recent-reports-list">
        {issues.length ? issues.slice(0, 20).map((issue) => {
          const badgeClass = issue.priority === 'critical' ? 'bg-danger' : issue.priority === 'high' ? 'bg-warning text-dark' : 'bg-info text-dark';
          return (
            <article className="d-flex gap-3 mb-3 p-3 bg-light rounded-3 issue-item" data-tier={issue.priority} key={issue.id}>
              <img src={safePhoto(issue.photos[0])} alt="" className="recent-report-image" />
              <div className="flex-grow-1 min-w-0">
                <div className="d-flex justify-content-between align-items-start gap-2">
                  <h3 className="h6 fw-bold mb-1 small">{formatCompact(issue.title, 40)}</h3>
                  <span className={`badge ${badgeClass}`}>{issue.priority}</span>
                </div>
                <p className="text-muted small mb-1">{formatCompact(issue.description, 60)}</p>
                <div className="d-flex justify-content-between align-items-center">
                  <small className="text-muted">SCMIRN demo record</small>
                </div>
              </div>
            </article>
          );
        }) : <p className="text-muted small mb-0">No civic reports are available yet.</p>}
      </div>
    </div>
  );
}

export function CivicIssueMap({ title, description, issues, loading = false, error, onRefresh, onLocation, showRecentReports = false, className = '' }: CivicIssueMapProps) {
  const [filter, setFilter] = useState<IssueFilter>('all');
  const [query, setQuery] = useState('');
  const [externalSearchConsent, setExternalSearchConsent] = useState(false);
  const [searchStatus, setSearchStatus] = useState('');
  const [searchError, setSearchError] = useState(false);
  const [locationStatus, setLocationStatus] = useState('');
  const [userLocation, setUserLocationState] = useState<CivicLocation | null>(null);
  const [map, setMap] = useState<LeafletMap | null>(null);
  const markers = useRef<Record<string, LeafletMarker | null>>({});
  const searchController = useRef<AbortController | null>(null);
  const validIssues = useMemo(() => issues.filter((issue) => issue.lat != null && issue.lng != null), [issues]);
  const visibleIssues = useMemo(() => filter === 'all' ? validIssues : validIssues.filter((issue) => issue.priority === filter), [filter, validIssues]);

  useEffect(() => () => searchController.current?.abort(), []);

  function useDeviceLocation() {
    if (!navigator.geolocation) {
      setLocationStatus('Device location is unavailable in this browser.');
      return;
    }
    setLocationStatus('Waiting for browser location permission…');
    navigator.geolocation.getCurrentPosition((position) => {
      const location = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy: position.coords.accuracy,
      };
      setUserLocationState(location);
      onLocation?.(location);
      map?.setView([location.lat, location.lng], 17);
      setLocationStatus(`Location shown on this map (accuracy about ${Math.round(location.accuracy ?? 0)} m).`);
    }, () => {
      setLocationStatus('Location permission was not granted or the position could not be read.');
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
  }

  async function searchMapLocation() {
    const value = query.trim();
    setSearchError(false);
    if (!value) {
      setSearchStatus('Enter a search query.');
      return;
    }
    setSearchStatus('Searching...');
    const normalized = value.toLowerCase();
    const matches = visibleIssues.filter((issue) =>
      issue.title.toLowerCase().includes(normalized) || issue.category.toLowerCase().includes(normalized) || issue.description.toLowerCase().includes(normalized)
    );
    if (matches.length && map) {
      const locations = matches.flatMap((issue) => issue.lat != null && issue.lng != null ? [[issue.lat, issue.lng] as [number, number]] : []);
      if (locations.length > 1) map.fitBounds(L.latLngBounds(locations).pad(0.25));
      else if (locations[0]) map.setView(locations[0], 16);
      markers.current[matches[0].id]?.openPopup();
      setSearchStatus(`Found ${matches.length} local result(s).`);
      return;
    }
    if (!externalSearchConsent) {
      setSearchStatus('No local result. Opt in below to search OpenStreetMap for a place name.');
      return;
    }
    try {
      searchController.current?.abort();
      const controller = new AbortController();
      searchController.current = controller;
      const place = await geocodePlace(value, controller.signal);
      if (!place) {
        setSearchStatus('No result found for this query.');
        setSearchError(true);
        return;
      }
      map?.setView([place.lat, place.lng], 16);
      setSearchStatus('External location found.');
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === 'AbortError') return;
      setSearchStatus(cause instanceof Error ? cause.message : 'Search service unavailable. Please try again.');
      setSearchError(true);
    }
  }

  return (
    <div className={`civic-map-layout ${showRecentReports ? 'with-recent-reports' : ''} ${className}`}>
      <div className={showRecentReports ? 'row align-items-end mb-5' : 'd-flex flex-wrap justify-content-between align-items-end mb-4 gap-3'}>
        <div className={showRecentReports ? 'col-lg-8' : ''}>
          <h2 className="display-5 fw-bold">{title}</h2>
          <p className={showRecentReports ? 'lead text-muted' : 'text-muted mb-0'}>{description}</p>
        </div>
      <div className={`map-tools ${showRecentReports ? 'col-lg-4 text-lg-end' : 'mt-3 mt-md-0'}`}>
        <div className="btn-group" role="group" aria-label="Filter civic issue map">
          <button type="button" className={`btn btn-outline-dark ${filter === 'all' ? 'active' : ''}`} aria-pressed={filter === 'all'} onClick={() => setFilter('all')}>{showRecentReports ? 'All Issues' : 'All'}</button>
          <button type="button" className={`btn btn-outline-danger ${filter === 'critical' ? 'active' : ''}`} aria-pressed={filter === 'critical'} onClick={() => setFilter('critical')}>Critical</button>
          <button type="button" className={`btn btn-outline-warning ${filter === 'high' ? 'active' : ''}`} aria-pressed={filter === 'high'} onClick={() => setFilter('high')}>{showRecentReports ? 'High Priority' : 'High'}</button>
        </div>
        <form className="input-group map-search" noValidate onSubmit={(event) => { event.preventDefault(); void searchMapLocation(); }}>
          <span className="input-group-text"><i className="fas fa-search" aria-hidden="true" /></span>
          <label className="visually-hidden" htmlFor="map-search-input">Search area, landmark, or issue</label>
          <input id="map-search-input" type="search" className="form-control" placeholder="Search area, landmark, or issue..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <button className="btn btn-dark" type="submit">Search</button>
        </form>
        <p className="small text-muted mt-2 mb-1">Map tiles use OpenStreetMap/Esri. Device location is off until you request it. Unmatched searches are sent to OpenStreetMap Nominatim only if you opt in; use a place name, not case details.</p>
        <div className="form-check text-start small mt-2">
          <input id="map-external-search-consent" className="form-check-input" type="checkbox" checked={externalSearchConsent} onChange={(event) => setExternalSearchConsent(event.target.checked)} />
          <label className="form-check-label text-muted" htmlFor="map-external-search-consent">Allow unmatched place-name searches to OpenStreetMap Nominatim</label>
        </div>
        <button type="button" className="btn btn-sm btn-outline-secondary mt-1" onClick={useDeviceLocation}><i className="fas fa-location-crosshairs me-2" aria-hidden="true" />Use my location</button>
        {locationStatus ? <small className="d-block text-muted mt-1" role="status" aria-live="polite">{locationStatus}</small> : null}
        <div className="map-search-status d-flex justify-content-between align-items-center">
          <small className={searchError ? 'text-danger' : 'text-muted'} aria-live="polite">{error ?? searchStatus}</small>
        </div>
        {loading ? <small className="text-muted" role="status">Loading civic reports...</small> : null}
      </div>
      </div>
      <div className="civic-map-grid">
        <div className="civic-map-frame">
          <MapContainer id="civicMap" center={fallbackCenter} zoom={15} zoomControl={false} attributionControl={false}>
            <MapCapture onReady={setMap} />
            <LayersControl position="topright">
              <LayersControl.BaseLayer checked name="Detailed Streets">
                <TileLayer maxZoom={22} subdomains="abc" attribution="© OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              </LayersControl.BaseLayer>
              <LayersControl.BaseLayer name="Satellite View">
                <TileLayer maxZoom={19} attribution="© Esri" url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
              </LayersControl.BaseLayer>
            </LayersControl>
            <ZoomControl position="bottomright" />
            <ScaleControl imperial={false} metric position="bottomleft" />
            {visibleIssues.map((issue) => (
              <Marker key={issue.id} position={[issue.lat!, issue.lng!]} icon={priorityIcon(issue.priority)} title={issue.title}
                ref={(marker) => { markers.current[issue.id] = marker; }}
                eventHandlers={{ mouseover: (event) => event.target.openPopup() }}>
                <Popup maxWidth={350} className="custom-popup">
                  <IssuePopup issue={issue} />
                </Popup>
              </Marker>
            ))}
            {userLocation ? (
              <>
                <Marker position={[userLocation.lat, userLocation.lng]} icon={L.divIcon({
                  className: 'user-location',
                  html: '<div class="civic-user-marker"></div>',
                  iconSize: [16, 16],
                  iconAnchor: [8, 8],
                })} eventHandlers={{ add: (event) => event.target.openPopup() }}>
                  <Popup><strong>You are here</strong><br />Accuracy: {Math.round(userLocation.accuracy ?? 0)} meters</Popup>
                </Marker>
                <Circle center={[userLocation.lat, userLocation.lng]} radius={userLocation.accuracy ?? 0}
                  pathOptions={{ color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 0.1, weight: 1 }} />
              </>
            ) : null}
          </MapContainer>
        </div>
        {showRecentReports ? <RecentReports issues={issues} /> : null}
      </div>
    </div>
  );
}

export default CivicIssueMap;
