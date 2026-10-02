import { useState } from 'react';
import { apiGet, apiPost } from '@/api/http';
import { Badge, Button, JsonViewer } from '@/components/atoms';

type MapState = Record<string, unknown>;
type ErrorState = Record<string, string | null>;
type LoadingState = Record<string, boolean>;

export function CityOrganismConsole() {
  const [zone, setZone] = useState<string>('WARD-11');
  const [heartRate, setHeartRate] = useState<number>(84);
  const [noiseDb, setNoiseDb] = useState<number>(61);
  const [footfall, setFootfall] = useState<number>(28);

  const [incidentType, setIncidentType] = useState<string>('POTHOLE');
  const [crackMm, setCrackMm] = useState<number>(0.35);
  const [materialType, setMaterialType] = useState<string>('BACTERIAL_BIOCONCRETE');

  const [proposalTitle, setProposalTitle] = useState<string>('Flood-resilient bridge and mobility corridor');
  const [designPrompt, setDesignPrompt] = useState<string>(
    'Design a flood-resilient park that generates 50kW solar and can run as a community kitchen in emergencies.'
  );

  const [assetId, setAssetId] = useState<string>('streetlight-ward11-014');
  const [assetValue, setAssetValue] = useState<number>(1500000);
  const [iipTitle, setIipTitle] = useState<string>('Ward-level microgrid and drainage upgrade');
  const [supporters, setSupporters] = useState<number>(220);

  const [siteType, setSiteType] = useState<string>('URBAN_CORE');
  const [pollution, setPollution] = useState<number>(48);
  const [drillType, setDrillType] = useState<string>('FLOOD');
  const [thoughtIntent, setThoughtIntent] = useState<string>('I need a bench and calmer lighting nearby.');
  const [translationText, setTranslationText] = useState<string>('Bees need flowers around the storm-water canal.');
  const [translationTarget, setTranslationTarget] = useState<string>('hi');

  const [households, setHouseholds] = useState<number>(100000);
  const [roadmapYear, setRoadmapYear] = useState<number>(2028);

  const [results, setResults] = useState<MapState>({});
  const [errors, setErrors] = useState<ErrorState>({});
  const [loading, setLoading] = useState<LoadingState>({});

  const setBusy = (key: string, value: boolean) =>
    setLoading((prev) => ({ ...prev, [key]: value }));

  const setError = (key: string, value: string | null) =>
    setErrors((prev) => ({ ...prev, [key]: value }));

  const setResult = (key: string, value: unknown) =>
    setResults((prev) => ({ ...prev, [key]: value }));

  async function runGet(key: string, path: string) {
    setBusy(key, true);
    setError(key, null);
    const res = await apiGet<unknown>(path);
    setBusy(key, false);
    if (!res.ok) {
      setError(key, res.error);
      setResult(key, res.details ?? null);
      return;
    }
    setResult(key, res.data);
  }

  async function runPost(key: string, path: string, payload: unknown) {
    setBusy(key, true);
    setError(key, null);
    const res = await apiPost<unknown>(path, payload);
    setBusy(key, false);
    if (!res.ok) {
      setError(key, res.error);
      setResult(key, res.details ?? null);
      return;
    }
    setResult(key, res.data);
  }

  return (
    <div className="console">
      <div className="console-grid city-grid">
        <div className="feature-card">
          <h3>Sentient Layer: Quantum + Ambient Intelligence</h3>
          <p>Concept simulation only; no live sensing or emotional-response system is connected.</p>
          <div className="field">
            <label>Zone</label>
            <input className="input" value={zone} onChange={(e) => setZone(e.target.value)} />
          </div>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>Heart Rate</label>
              <input
                className="input"
                type="number"
                value={heartRate}
                onChange={(e) => setHeartRate(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Noise dB</label>
              <input
                className="input"
                type="number"
                value={noiseDb}
                onChange={(e) => setNoiseDb(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Footfall/min</label>
              <input
                className="input"
                type="number"
                value={footfall}
                onChange={(e) => setFootfall(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="inline-actions">
            <Button onClick={() => runGet('qnm', `/api/v1/city-brain/sensing/quantum-mesh/status?zone=${encodeURIComponent(zone)}`)} disabled={loading.qnm}>
              {loading.qnm ? 'Running...' : 'Run Quantum Mesh'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('ambient', '/api/v1/city-brain/sensing/ambient-intelligence/simulate', {
                  neighborhood_id: zone,
                  signals: {
                    avg_heart_rate_bpm: heartRate,
                    acoustic_stress_db: noiseDb,
                    footfall_density_per_min: footfall,
                    rain_risk: 0.3,
                    current_hour_local: 14,
                  },
                })
              }
              disabled={loading.ambient}
            >
              {loading.ambient ? 'Running...' : 'Run Ambient Intelligence'}
            </Button>
            {errors.qnm ? <Badge variant="danger">{errors.qnm}</Badge> : null}
            {errors.ambient ? <Badge variant="danger">{errors.ambient}</Badge> : null}
          </div>
          {results.qnm ? <JsonViewer value={results.qnm} collapsed /> : null}
          {results.ambient ? <JsonViewer value={results.ambient} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Autonomous Layer: Robotic Swarms + Self-Healing Materials</h3>
          <p>Feature 3 and 4 with dispatch planning and adaptive material response.</p>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>Incident</label>
              <select className="select" value={incidentType} onChange={(e) => setIncidentType(e.target.value)}>
                <option value="POTHOLE">POTHOLE</option>
                <option value="PIPE_LEAK">PIPE_LEAK</option>
                <option value="BRIDGE_CRACK">BRIDGE_CRACK</option>
                <option value="FLOODING">FLOODING</option>
                <option value="GRID_FAULT">GRID_FAULT</option>
              </select>
            </div>
            <div className="field">
              <label>Crack Width (mm)</label>
              <input
                className="input"
                type="number"
                step="0.01"
                value={crackMm}
                onChange={(e) => setCrackMm(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Material</label>
              <select className="select" value={materialType} onChange={(e) => setMaterialType(e.target.value)}>
                <option value="BACTERIAL_BIOCONCRETE">BACTERIAL_BIOCONCRETE</option>
                <option value="VASCULAR_NETWORK">VASCULAR_NETWORK</option>
                <option value="PROGRAMMABLE_SIDEWALK">PROGRAMMABLE_SIDEWALK</option>
              </select>
            </div>
          </div>
          <div className="inline-actions">
            <Button
              onClick={() =>
                runPost('swarm', '/api/v1/city-brain/autonomy/robotic-swarms/dispatch', {
                  incident_type: incidentType,
                  crack_width_mm: crackMm,
                  pressure_drop_percent: 18,
                  water_level_cm: 12,
                })
              }
              disabled={loading.swarm}
            >
              {loading.swarm ? 'Running...' : 'Dispatch Swarm'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('healing', '/api/v1/city-brain/autonomy/self-healing-materials/plan', {
                  material_type: materialType,
                  crack_width_mm: crackMm,
                  water_intrusion: true,
                })
              }
              disabled={loading.healing}
            >
              {loading.healing ? 'Running...' : 'Plan Self-Heal'}
            </Button>
            {errors.swarm ? <Badge variant="danger">{errors.swarm}</Badge> : null}
            {errors.healing ? <Badge variant="danger">{errors.healing}</Badge> : null}
          </div>
          {results.swarm ? <JsonViewer value={results.swarm} collapsed /> : null}
          {results.healing ? <JsonViewer value={results.healing} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Immersive Layer: Mirror World + Generative Urban AI</h3>
          <p>Feature 5 and 6 with townhall simulation and prompt-to-plan generation.</p>
          <div className="field">
            <label>Townhall Proposal</label>
            <input className="input" value={proposalTitle} onChange={(e) => setProposalTitle(e.target.value)} />
          </div>
          <div className="field">
            <label>Urban Design Prompt</label>
            <textarea className="textarea resize-none" value={designPrompt} onChange={(e) => setDesignPrompt(e.target.value)} />
          </div>
          <div className="inline-actions">
            <Button
              onClick={() =>
                runPost('metaverse', '/api/v1/city-brain/immersive/metaverse/townhall', {
                  proposal_title: proposalTitle,
                  horizon_years: 10,
                  accessibility_focus: true,
                })
              }
              disabled={loading.metaverse}
            >
              {loading.metaverse ? 'Running...' : 'Run Mirror World'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('design', '/api/v1/city-brain/immersive/generative-urban-design', {
                  prompt: designPrompt,
                  constraints: {
                    target_solar_kw: 50,
                    budget_cap_inr: 35000000,
                    emergency_use: 'community kitchen',
                  },
                })
              }
              disabled={loading.design}
            >
              {loading.design ? 'Running...' : 'Generate Urban Design'}
            </Button>
            {errors.metaverse ? <Badge variant="danger">{errors.metaverse}</Badge> : null}
            {errors.design ? <Badge variant="danger">{errors.design}</Badge> : null}
          </div>
          {results.metaverse ? <JsonViewer value={results.metaverse} collapsed /> : null}
          {results.design ? <JsonViewer value={results.design} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Decentralized Layer: DePIN, Tokens, DAO Governance</h3>
          <p>Feature 7 with asset tokenization, resilience dividends and IIP governance.</p>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>Asset ID</label>
              <input className="input" value={assetId} onChange={(e) => setAssetId(e.target.value)} />
            </div>
            <div className="field">
              <label>Asset Valuation (INR)</label>
              <input
                className="input"
                type="number"
                value={assetValue}
                onChange={(e) => setAssetValue(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>IIP Supporters</label>
              <input
                className="input"
                type="number"
                value={supporters}
                onChange={(e) => setSupporters(Number(e.target.value))}
              />
            </div>
          </div>
          <div className="field">
            <label>IIP Title</label>
            <input className="input" value={iipTitle} onChange={(e) => setIipTitle(e.target.value)} />
          </div>
          <div className="inline-actions">
            <Button
              onClick={() =>
                runPost('token', '/api/v1/city-brain/depin/tokenize-asset', {
                  asset_id: assetId,
                  asset_type: 'MICROGRID_NODE',
                  valuation_inr: assetValue,
                  fractional_units: 10000,
                  performance_score: 82,
                })
              }
              disabled={loading.token}
            >
              {loading.token ? 'Running...' : 'Tokenize Asset'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('dao', '/api/v1/city-brain/depin/governance/iip', {
                  title: iipTitle,
                  requested_budget_inr: 12000000,
                  supporters,
                  avg_donation_inr: 150,
                })
              }
              disabled={loading.dao}
            >
              {loading.dao ? 'Running...' : 'Run DAO Proposal'}
            </Button>
            {errors.token ? <Badge variant="danger">{errors.token}</Badge> : null}
            {errors.dao ? <Badge variant="danger">{errors.dao}</Badge> : null}
          </div>
          {results.token ? <JsonViewer value={results.token} collapsed /> : null}
          {results.dao ? <JsonViewer value={results.dao} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Energetic + Biological Layers</h3>
          <p>Feature 8 and 9 with living energy status and bio-integrated site planning.</p>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>Site Type</label>
              <select className="select" value={siteType} onChange={(e) => setSiteType(e.target.value)}>
                <option value="URBAN_CORE">URBAN_CORE</option>
                <option value="HILLSIDE">HILLSIDE</option>
                <option value="RIVER_EDGE">RIVER_EDGE</option>
                <option value="INDUSTRIAL_ZONE">INDUSTRIAL_ZONE</option>
                <option value="COASTAL">COASTAL</option>
              </select>
            </div>
            <div className="field">
              <label>Soil Pollution Index</label>
              <input
                className="input"
                type="number"
                value={pollution}
                onChange={(e) => setPollution(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Energy Zone</label>
              <input className="input" value={zone} onChange={(e) => setZone(e.target.value)} />
            </div>
          </div>
          <div className="inline-actions">
            <Button
              onClick={() =>
                runGet('energy', `/api/v1/city-brain/energy/living-ecosystem/status?zone=${encodeURIComponent(zone)}`)
              }
              disabled={loading.energy}
            >
              {loading.energy ? 'Running...' : 'Get Living Energy'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('bio', '/api/v1/city-brain/bio-integrated/assessment', {
                  site_type: siteType,
                  soil_pollution_index: pollution,
                  rainfall_mm: 140,
                  slope_percent: 8,
                })
              }
              disabled={loading.bio}
            >
              {loading.bio ? 'Running...' : 'Assess Bio-Integrated Site'}
            </Button>
            {errors.energy ? <Badge variant="danger">{errors.energy}</Badge> : null}
            {errors.bio ? <Badge variant="danger">{errors.bio}</Badge> : null}
          </div>
          {results.energy ? <JsonViewer value={results.energy} collapsed /> : null}
          {results.bio ? <JsonViewer value={results.bio} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Resilience + Human Interface Layers</h3>
          <p>Feature 10, 11 and 12 with antifragile drills, neuro-adaptive controls and translation.</p>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>Drill Type</label>
              <select className="select" value={drillType} onChange={(e) => setDrillType(e.target.value)}>
                <option value="FLOOD">FLOOD</option>
                <option value="EARTHQUAKE">EARTHQUAKE</option>
                <option value="CYBERATTACK">CYBERATTACK</option>
                <option value="HEATWAVE">HEATWAVE</option>
                <option value="GRID_FAILURE">GRID_FAILURE</option>
              </select>
            </div>
            <div className="field">
              <label>Thought Intent</label>
              <input className="input" value={thoughtIntent} onChange={(e) => setThoughtIntent(e.target.value)} />
            </div>
            <div className="field">
              <label>Translate To</label>
              <input className="input" value={translationTarget} onChange={(e) => setTranslationTarget(e.target.value)} />
            </div>
          </div>
          <div className="field">
            <label>Translation Text</label>
            <input className="input" value={translationText} onChange={(e) => setTranslationText(e.target.value)} />
          </div>
          <div className="inline-actions">
            <Button
              onClick={() =>
                runPost('drill', '/api/v1/city-brain/resilience/antifragile-drill', {
                  drill_type: drillType,
                  stress_multiplier: 1.4,
                  target_zone: zone,
                })
              }
              disabled={loading.drill}
            >
              {loading.drill ? 'Running...' : 'Run Antifragile Drill'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('neuro', '/api/v1/city-brain/interface/neuro-adaptive/respond', {
                  thought_intent: thoughtIntent,
                  stress_index: 63,
                  neighborhood_id: zone,
                })
              }
              disabled={loading.neuro}
            >
              {loading.neuro ? 'Running...' : 'Run Neuro-Interface'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runPost('translation', '/api/v1/city-brain/interface/universal-translation/translate', {
                  human_text: translationText,
                  from_language: 'en',
                  to_language: translationTarget,
                  species_signal: 'bees need pollinator corridor',
                  machine_protocol: 'modbus',
                })
              }
              disabled={loading.translation}
            >
              {loading.translation ? 'Running...' : 'Run Universal Translation'}
            </Button>
            {errors.drill ? <Badge variant="danger">{errors.drill}</Badge> : null}
            {errors.neuro ? <Badge variant="danger">{errors.neuro}</Badge> : null}
            {errors.translation ? <Badge variant="danger">{errors.translation}</Badge> : null}
          </div>
          {results.drill ? <JsonViewer value={results.drill} collapsed /> : null}
          {results.neuro ? <JsonViewer value={results.neuro} collapsed /> : null}
          {results.translation ? <JsonViewer value={results.translation} collapsed /> : null}
        </div>

        <div className="feature-card">
          <h3>Business Model + 10-Year Roadmap + Value Proposition</h3>
          <p>Section IX and X are now API-driven so the dashboard can forecast revenue and phase progress.</p>
          <div className="console-grid city-inline-3">
            <div className="field">
              <label>Households</label>
              <input
                className="input"
                type="number"
                value={households}
                onChange={(e) => setHouseholds(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Roadmap Year</label>
              <input
                className="input"
                type="number"
                value={roadmapYear}
                onChange={(e) => setRoadmapYear(Number(e.target.value))}
              />
            </div>
            <div className="field">
              <label>Start Year</label>
              <input className="input" type="number" value={2026} readOnly />
            </div>
          </div>
          <div className="inline-actions">
            <Button
              onClick={() =>
                runGet(
                  'business',
                  `/api/v1/city-brain/business-model/forecast?households=${encodeURIComponent(String(households))}`
                )
              }
              disabled={loading.business}
            >
              {loading.business ? 'Running...' : 'Run Business Forecast'}
            </Button>
            <Button
              variant="ghost"
              onClick={() =>
                runGet(
                  'roadmap',
                  `/api/v1/city-brain/roadmap/status?start_year=2026&year=${encodeURIComponent(String(roadmapYear))}`
                )
              }
              disabled={loading.roadmap}
            >
              {loading.roadmap ? 'Running...' : 'Get Roadmap Status'}
            </Button>
            <Button variant="ghost" onClick={() => runGet('value', '/api/v1/city-brain/value-proposition')} disabled={loading.value}>
              {loading.value ? 'Running...' : 'Get Value Proposition'}
            </Button>
            {errors.business ? <Badge variant="danger">{errors.business}</Badge> : null}
            {errors.roadmap ? <Badge variant="danger">{errors.roadmap}</Badge> : null}
            {errors.value ? <Badge variant="danger">{errors.value}</Badge> : null}
          </div>
          {results.business ? <JsonViewer value={results.business} collapsed /> : null}
          {results.roadmap ? <JsonViewer value={results.roadmap} collapsed /> : null}
          {results.value ? <JsonViewer value={results.value} collapsed /> : null}
        </div>
      </div>
    </div>
  );
}

export default CityOrganismConsole;
