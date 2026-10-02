import { CivicMap } from '../../features/maps/components/CivicMap';
import { IoTConsole } from '../../features/iot/components/IoTConsole';
import { IssueRegistryConsole } from '../../features/blockchain/components/IssueRegistryConsole';
import { LegalCopilotConsole } from '../../features/legal/components/LegalCopilotConsole';
import { GamificationConsole } from '../../features/gamification/components/GamificationConsole';
import { ResilienceConsole } from '../../features/resilience/components/ResilienceConsole';
import { DigitalTwinConsole } from '../../features/twin/components/DigitalTwinConsole';
import { CityOrganismConsole } from '../../features/future/components/CityOrganismConsole';
import { EnterpriseCommandCenter } from '../../features/enterprise/components/EnterpriseCommandCenter';

export const PlatformOverview = () => {
  return (
    <div className="platform">
      <header className="app-header">
        <div role="note" className="alert alert-warning" aria-label="Prototype status">
          Concept specification only. This component is not part of the active routes; listed integrations, performance figures, and outcomes are not implemented or verified. Embedded consoles are local simulations and do not connect to government systems.
        </div>
        <p className="app-pill">SCMIRN • Civic Intelligence Network</p>
        <h1>Next‑Gen Civic Infrastructure OS</h1>
        <p className="app-subtitle">
          End‑to‑end platform combining IoT, AI, blockchain and gamification to
          predict failures, ensure transparency, and activate citizens in real time.
        </p>
      </header>

      <main className="app-content">
        <div className="platform-layout">
          <section className="platform-column">
            <h2 className="section-title">1. IoT Predictive Maintenance Network</h2>
            <p className="section-intro">
              Real‑time sensor ingestion, anomaly detection and predictive
              maintenance for critical civic assets like streetlights, pumps,
              waste bins and micro‑grids.
            </p>

            <div className="feature-card">
              <h3>1.1 Sensor Data Ingestion &amp; Anomaly Detection</h3>
              <p>
                Streaming engine that normalizes sensor payloads, computes
                composite health scores, and triggers maintenance alerts with
                &gt;95% accuracy.
              </p>
              <ul className="feature-list">
                <li>Asset‑specific baselines and anomaly thresholds</li>
                <li>Health score bands from optimal to critical</li>
                <li>Automatic failure mode detection and RUL estimates</li>
                <li>Maintenance triggers with multi‑channel alerting</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: IOT_SENSOR_INGESTION_V1</span>
                <span className="spec-chip">API: POST /api/v1/iot/ingest</span>
              </div>
              <details className="demo-details">
                <summary>Local simulation</summary>
                <IoTConsole />
              </details>
            </div>

            <div className="feature-card">
              <h3>1.2 Predictive Analytics Engine</h3>
              <p>
                Ensemble ML (Random Forest + LSTM) that forecasts failures 30‑90
                days in advance and optimizes maintenance windows.
              </p>
              <ul className="feature-list">
                <li>Time‑series feature engineering and degradation curves</li>
                <li>Failure probabilities at 7/30/60/90 days</li>
                <li>Cost‑aware preventive vs. reactive maintenance planning</li>
                <li>Work‑order ready outputs with crew, tools and parts</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: PREDICTIVE_ANALYTICS_ENGINE_V1</span>
                <span className="spec-chip">API: GET /api/v1/iot/predictions</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>1.3 Real‑Time Health Map API</h3>
              <p>
                Geospatial aggregation layer that turns raw sensor streams into
                live ward‑ and city‑level health maps.
              </p>
              <ul className="feature-list">
                <li>Zoom‑aware aggregation from street to city level</li>
                <li>Health, criticality and maintenance backlog overlays</li>
                <li>Predictive failure heatmaps (next 30 days)</li>
                <li>Tile caching and spatial indexing for performance</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: HEALTH_MAP_AGGREGATOR_V1</span>
                <span className="spec-chip">API: GET /api/v1/iot/health-map</span>
              </div>
            </div>

            <h2 className="section-title">2. Blockchain Transparency Layer</h2>
            <p className="section-intro">
              Hyperledger / EVM smart contracts that bring end‑to‑end
              transparency to procurement, complaints, and public funds.
            </p>

            <div className="feature-card">
              <h3>2.1 Smart Contract Generator for Civic Procurement</h3>
              <p>
                Production‑grade chaincode for sealed‑bid tenders, milestone‑based
                payments and immutable audit trails.
              </p>
              <ul className="feature-list">
                <li>Sealed‑bid auctions with automatic L1 selection</li>
                <li>IoT‑ and document‑oracle verified milestones</li>
                <li>Multi‑sig payment release and dispute handling</li>
                <li>GFR 2017 and CPPP‑aligned compliance checks</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: CIVIC_PROCUREMENT_CONTRACT_V1</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>2.2 Immutable Issue Registry Contract</h3>
              <p>
                Tamper‑evident complaint ledger with full lifecycle tracking from
                report to verified resolution.
              </p>
              <ul className="feature-list">
                <li>Hash‑based privacy‑preserving issue registration</li>
                <li>Strict status workflow with auto‑escalations</li>
                <li>Linked media, IoT and auditor verification</li>
                <li>Rich query APIs for citizens and auditors</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: ISSUE_REGISTRY_CONTRACT_V1</span>
                <span className="spec-chip">API: POST /api/v1/blockchain/register-issue</span>
              </div>
              <details className="demo-details">
                <summary>Local simulation</summary>
                <IssueRegistryConsole />
              </details>
            </div>

            <div className="feature-card">
              <h3>2.3 Fund Tracking &amp; Transparency Contract</h3>
              <p>
                Trace every rupee from allocation to last‑mile expenditure, with
                anomaly flags and citizen‑facing visualizations.
              </p>
              <ul className="feature-list">
                <li>Budget, project and vendor‑linked expenditure graph</li>
                <li>Real‑time budget utilization and overspend prevention</li>
                <li>&ldquo;Where did my ₹1000 go?&rdquo; citizen view</li>
                <li>Fraud pattern detection and audit hooks</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: FUND_TRACKING_CONTRACT_V1</span>
              </div>
            </div>
          </section>

          <section className="platform-column">
            <h2 className="section-title">3. Advanced AI Legal Co‑Pilot</h2>
            <p className="section-intro">
              Domain‑aware AI stack that classifies intents, computes rights and
              drafts court‑ready documents against Indian legal frameworks.
            </p>

            <div className="feature-card">
              <h3>3.1 Intent Classification &amp; Legal Domain Router</h3>
              <p>
                BERT‑powered classifier that routes citizen queries to the right
                legal pathway with urgency and complexity tagging.
              </p>
              <ul className="feature-list">
                <li>10+ top‑level domains from housing to taxation</li>
                <li>Sub‑domain and multi‑issue detection</li>
                <li>Urgency + complexity scoring for triage</li>
                <li>Safety flags for emergencies and high‑risk cases</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: LEGAL_INTENT_CLASSIFIER_V2</span>
                <span className="spec-chip">API: POST /api/v1/ai/classify-intent</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>3.2 Rights Calculator &amp; Legal Framework Mapper</h3>
              <p>
                Knowledge‑graph backed rights engine that maps situations to
                specific Acts, sections, timelines and remedies.
              </p>
              <ul className="feature-list">
                <li>Central + state + local law reconciliation</li>
                <li>Actionable timelines and notice period calculations</li>
                <li>DIY vs. lawyer‑assisted pathway suggestions</li>
                <li>Quality scoring against legal design standards</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: RIGHTS_CALCULATOR_V2</span>
                <span className="spec-chip">API: POST /api/v1/ai/rights-calculate</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>3.3 Document Intelligence &amp; Auto‑Population</h3>
              <p>
                Automation engine that turns conversations into RTIs, FIRs,
                legal notices and petitions tailored to jurisdiction.
              </p>
              <ul className="feature-list">
                <li>Template‑driven drafting for Indian procedures</li>
                <li>Auto‑filled facts, grounds, prayers and annexures</li>
                <li>Filing guidance, fees and post‑filing timelines</li>
                <li>Safety watermarks and human‑review flows</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: DOCUMENT_INTELLIGENCE_V2</span>
                <span className="spec-chip">API: POST /api/v1/ai/document-generate</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>3.4 Legal Quality Scoring</h3>
              <p>
                Stanford Legal Design Lab‑inspired QA layer to evaluate every AI
                output for usefulness, completeness and safety.
              </p>
              <ul className="feature-list">
                <li>Multi‑dimension scoring with detailed evidence</li>
                <li>Safety gating and human review triggers</li>
                <li>Continuous benchmarking vs. human baselines</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: LEGAL_QUALITY_SCORER_V1</span>
                <span className="spec-chip">API: POST /api/v1/ai/quality-check</span>
              </div>
              <details className="demo-details">
                <summary>Live demo console (run full pipeline)</summary>
                <LegalCopilotConsole />
              </details>
            </div>

            <h2 className="section-title">4. Gamified Civic Engagement</h2>
            <p className="section-intro">
              Reputation, quests and rewards that turn civic participation into a
              continuous, meaningful habit.
            </p>

            <div className="feature-card">
              <h3>4.1 Reputation Engine &amp; Civic Score</h3>
              <p>
                Behavioral economics‑driven scoring that rewards accurate reports,
                verification and community support.
              </p>
              <ul className="feature-list">
                <li>Multi‑factor civic score out of 1000</li>
                <li>Tiered ranks, badges and leaderboards</li>
                <li>Nudges using loss aversion and social proof</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: REPUTATION_ENGINE_V2</span>
                <span className="spec-chip">API: GET /api/v1/gamification/score</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>4.2 Challenge &amp; Quest Generator</h3>
              <p>
                Personalized missions that guide citizens from discovery to
                verification, expertise and community leadership.
              </p>
              <ul className="feature-list">
                <li>Dynamic difficulty and seasonal civic campaigns</li>
                <li>Multi‑objective quests with progress tracking</li>
                <li>Tangible, social and intrinsic rewards</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: CHALLENGE_GENERATOR_V1</span>
                <span className="spec-chip">API: GET /api/v1/gamification/challenges</span>
              </div>
              <details className="demo-details">
                <summary>Live demo console</summary>
                <GamificationConsole />
              </details>
            </div>

            <div className="feature-card">
              <h3>4.3 Reward Redemption &amp; Partnerships</h3>
              <p>
                Redemption engine that converts civic points into real benefits
                with municipalities, transit and local businesses.
              </p>
              <ul className="feature-list">
                <li>Transit, utility, merchant and social‑impact rewards</li>
                <li>Fraud‑aware rules and cooldowns</li>
                <li>API hooks into billing and merchant systems</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: REWARD_MANAGER_V1</span>
              </div>
            </div>
          </section>

          <section className="platform-column">
            <h2 className="section-title">5. Resilience Hub Network</h2>
            <p className="section-intro">
              AI‑assisted micro‑grid hubs that keep neighborhoods powered, safe
              and coordinated during shocks.
            </p>

            <div className="feature-card">
              <h3>5.1 Micro‑Grid Monitoring &amp; Disaster Mode</h3>
              <p>
                Operations AI that optimizes hub autonomy, load shedding and
                shelter operations during floods, heatwaves and grid failures.
              </p>
              <ul className="feature-list">
                <li>Dynamic mode switching (normal, islanded, emergency)</li>
                <li>Resource sustainability and evacuee capacity modelling</li>
                <li>IoT‑driven load control commands</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: RESILIENCE_HUB_MONITOR_V1</span>
                <span className="spec-chip">API: GET /api/v1/resilience/hub-status</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>5.2 Mutual Aid Matching Engine</h3>
              <p>
                Community coordination layer that matches neighbors with needs to
                vetted volunteers in real time.
              </p>
              <ul className="feature-list">
                <li>Distance, skill, availability and trust‑aware matching</li>
                <li>Safety features for vulnerable users</li>
                <li>Impact tracking and recognition</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: MUTUAL_AID_MATCHER_V1</span>
                <span className="spec-chip">API: POST /api/v1/resilience/request-aid</span>
              </div>
              <details className="demo-details">
                <summary>Live demo console</summary>
                <ResilienceConsole />
              </details>
            </div>

            <h2 className="section-title">6. Digital Twin Simulation</h2>
            <p className="section-intro">
              Living, geospatially‑accurate models of wards and cities for
              long‑term planning and stress testing.
            </p>

            <div className="feature-card">
              <h3>6.1 Infrastructure Digital Twin Generator</h3>
              <p>
                Asset‑level models that combine condition, demand, climate and
                network dependencies into a single planning canvas.
              </p>
              <ul className="feature-list">
                <li>End‑to‑end inventory with criticality scoring</li>
                <li>Population and climate stressor overlays</li>
                <li>Scenario‑based investment and maintenance planning</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: DIGITAL_TWIN_GENERATOR_V1</span>
              </div>
            </div>

            <div className="feature-card">
              <h3>6.2 Scenario Simulation Engine</h3>
              <p>
                Monte‑Carlo and agent‑based simulations that quantify resilience,
                costs and recovery times across what‑if events.
              </p>
              <ul className="feature-list">
                <li>Extreme weather, growth and failure scenarios</li>
                <li>Resilience scores with confidence intervals</li>
                <li>Immediate, short‑term and long‑term recommendations</li>
              </ul>
              <div className="spec-chip-row">
                <span className="spec-chip">Template: SCENARIO_SIMULATOR_V1</span>
                <span className="spec-chip">API: POST /api/v1/twin/simulate</span>
              </div>
              <details className="demo-details">
                <summary>Live demo console</summary>
                <DigitalTwinConsole />
              </details>
            </div>

            <div className="feature-card">
              <h3>Civic Health Map Preview</h3>
              <p>
                Prototype view of issue clusters and neighborhood‑level civic
                health using the same geospatial stack as the production health map.
              </p>
              <CivicMap />
            </div>
          </section>
        </div>

        <section className="feature-card city-organism-section">
          <h2 className="section-title">7. Smart Civic Urban Organism (Full 12-Layer Stack)</h2>
          <p className="section-intro">
            This workspace operationalizes the complete vision: Sentient, Autonomous, Immersive, Decentralized,
            Energetic, Biological, Antifragile, Neuro-Adaptive, Universal Translation, Business Model, and Roadmap.
          </p>
          <CityOrganismConsole />
        </section>

        <section className="feature-card city-organism-section">
          <h2 className="section-title">8. Enterprise Executive Dashboard &amp; Command Center</h2>
          <p className="section-intro">
            C-suite war room with live city health KPI, predictive risk radar, crisis sandbox,
            ROI calculator, enterprise integrations, trust/security controls, and multi-tenant scale tooling.
          </p>
          <EnterpriseCommandCenter />
        </section>
      </main>
    </div>
  );
};

export default PlatformOverview;

