import { useMemo, useState } from 'react';
import { Circle, MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Button, Badge, JsonViewer } from '@/components/atoms';
import { apiGet, apiPost } from '@/api/http';
import { asJsonObject, getJsonValue, type JsonObject } from '@/utils/json';

type IngestResponse = unknown;
type HealthMapResponse = unknown;

const defaultCenter: [number, number] = [28.6139, 77.209];

const statusColor: Record<string, string> = {
  OPTIMAL: '#16a34a',
  GOOD: '#22c55e',
  FAIR: '#2563eb',
  POOR: '#f97316',
  CRITICAL: '#dc2626',
};

function assetIcon(status: string) {
  const color = statusColor[status] ?? '#64748b';
  return L.divIcon({
    className: 'civic-map-pin',
    html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 0 2px ${color}40;"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

const samplePayload = {
  sensor_payload: {
    asset_id: '9d3b7a38-5b5b-4a36-9a8d-000000000001',
    asset_type: 'STREETLIGHT',
    location: { lat: 28.6139, lng: 77.209, ward: 'WARD-11' },
    timestamp: new Date().toISOString(),
    sensor_readings: {
      vibration_rms: 5.2,
      temperature_celsius: 71.0,
      pressure_kpa: null,
      energy_consumption_kwh: 0.42,
      fill_level_percent: null,
      voltage: 226.5,
      current: 0.8,
      power_factor: 0.82,
      operational_hours: 1840,
      anomaly_score: 0.78,
    },
    environmental_context: {
      weather: 'EXTREME_HEAT',
      temperature_ambient: 41.5,
      humidity_percent: 38.0,
    },
  },
};

export function IoTConsole() {
  const [payloadText, setPayloadText] = useState<string>(JSON.stringify(samplePayload, null, 2));
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);
  const [healthMap, setHealthMap] = useState<HealthMapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const assets = useMemo(() => {
    const list = getJsonValue(healthMap, 'map_data', 'assets');
    return Array.isArray(list) ? list.map(asJsonObject).filter((asset): asset is JsonObject => asset !== null) : [];
  }, [healthMap]);

  async function ingest() {
    setError(null);
    setLoading(true);
    setIngestResult(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(payloadText);
    } catch {
      setError('Invalid JSON payload.');
      setLoading(false);
      return;
    }

    const res = await apiPost<IngestResponse>('/api/v1/iot/ingest', parsed);
    setLoading(false);
    if (!res.ok) {
      setError(res.error);
      setIngestResult(res.details ?? null);
      return;
    }
    setIngestResult(res.data);
  }

  async function refreshMap() {
    setError(null);
    const qs = new URLSearchParams({
      north: '28.75',
      south: '28.50',
      east: '77.35',
      west: '77.05',
      zoom_level: '13',
      time_range: 'REALTIME',
    });
    qs.append('asset_types', 'STREETLIGHT');
    qs.append('asset_types', 'WATER_PUMP');
    qs.append('asset_types', 'WASTE_BIN');

    const res = await apiGet<HealthMapResponse>(`/api/v1/iot/health-map?${qs.toString()}`);
    if (!res.ok) {
      setError(res.error);
      setHealthMap(res.details ?? null);
      return;
    }
    setHealthMap(res.data);
  }

  return (
    <div className="console">
      <div className="console-grid">
        <p className="helper-text">
          Paste a sensor payload and ingest it. This will compute health score, anomaly detection, RUL and maintenance triggers and store it in the database.
        </p>

        <div className="field">
          <label>Sensor payload (JSON)</label>
          <textarea className="textarea resize-none" value={payloadText} onChange={(e) => setPayloadText(e.target.value)} />
        </div>

        <div className="inline-actions">
          <Button onClick={ingest} disabled={loading}>
            {loading ? 'Ingesting…' : 'Ingest Sensor Payload'}
          </Button>
          <Button variant="ghost" onClick={refreshMap}>
            Refresh Health Map
          </Button>
          {error ? <Badge variant="danger">{error}</Badge> : null}
        </div>

        {ingestResult ? (
          <>
            <div className="spec-chip-row">
              <span className="spec-chip">ingestion_id: {String(getJsonValue(ingestResult, 'ingestion_id') ?? '').slice(0, 8)}…</span>
              <span className="spec-chip">status: {String(getJsonValue(ingestResult, 'asset', 'status') ?? 'UNKNOWN')}</span>
              <span className="spec-chip">health: {String(getJsonValue(ingestResult, 'asset', 'health_score') ?? '-')}</span>
              <span className="spec-chip">priority: {String(getJsonValue(ingestResult, 'maintenance_trigger', 'priority') ?? '-')}</span>
            </div>
            <JsonViewer value={ingestResult} />
          </>
        ) : null}

        <div style={{ height: 360, width: '100%', borderRadius: 12, overflow: 'hidden' }}>
          <MapContainer center={defaultCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
            <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {assets.map((a) => {
              const loc = asJsonObject(a.location);
              if (!loc) return null;
              const lat = Number(loc.lat);
              const lng = Number(loc.lng);
              if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
              const st = String(a.status ?? 'FAIR');
              const color = statusColor[st] ?? '#64748b';
              return (
                <Marker key={String(a.id)} position={[lat, lng]} icon={assetIcon(st)}>
                  <Circle center={[lat, lng]} radius={120} pathOptions={{ color, fillOpacity: 0.12 }} />
                  <Popup>
                    <strong>{String(a.type)}</strong>
                    <div>ID: {String(a.id).slice(0, 8)}…</div>
                    <div>Status: {st}</div>
                    <div>Health: {String(a.health_score)}</div>
                    <div>Updated: {String(a.last_updated)}</div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>

        {healthMap ? <JsonViewer value={healthMap} collapsed /> : null}
      </div>
    </div>
  );
}

export default IoTConsole;
