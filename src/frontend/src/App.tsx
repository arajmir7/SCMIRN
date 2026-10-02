import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { UiContext, type CivicLocation } from '@/app/UiContext';
import { AssistantOrb, AssistantPanel } from '@/components/assistant/AssistantPanel';
import { DocumentGeneratorModal } from '@/components/documents/DocumentGeneratorModal';
import { Footer } from '@/components/layout/Footer';
import { Navigation } from '@/components/layout/Navigation';
import { ReportIssueModal } from '@/components/reports/ReportIssueModal';
import { HomePage } from '@/pages/HomePage';
import type { DocumentType } from '@/utils/documentTemplates';

const OfficesPage = lazy(() => import('@/pages/OfficesPage'));
const HeatmapPage = lazy(() => import('@/pages/HeatmapPage'));
const TrackerPage = lazy(() => import('@/pages/TrackerPage'));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'));
const DocumentsPage = lazy(() => import('@/pages/DocumentsPage'));
const PlatformPage = lazy(() => import('@/pages/PlatformPage'));

function RouteScrollManager() {
  const location = useLocation();
  useEffect(() => {
    if (location.hash) {
      const frame = window.requestAnimationFrame(() => document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({ behavior: 'smooth' }));
      return () => window.cancelAnimationFrame(frame);
    } else {
      window.scrollTo({ top: 0 });
    }
  }, [location.pathname, location.hash]);
  return null;
}

function AppFrame() {
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantPrompt, setAssistantPrompt] = useState<string>();
  const [reportOpen, setReportOpen] = useState(false);
  const [documentOpen, setDocumentOpen] = useState(false);
  const [documentType, setDocumentType] = useState<DocumentType>('rti');
  const [issuesRevision, setIssuesRevision] = useState(0);
  const [userLocation, setUserLocation] = useState<CivicLocation | null>(null);

  const openAssistant = useCallback((prompt?: string) => {
    setAssistantPrompt(prompt);
    setAssistantOpen(true);
  }, []);
  const closeAssistant = useCallback(() => setAssistantOpen(false), []);
  const openReport = useCallback(() => setReportOpen(true), []);
  const closeReport = useCallback(() => setReportOpen(false), []);
  const openDocument = useCallback((type: DocumentType = 'rti') => {
    setDocumentType(type);
    setDocumentOpen(true);
  }, []);
  const closeDocument = useCallback(() => setDocumentOpen(false), []);
  const refreshIssues = useCallback(() => setIssuesRevision((revision) => revision + 1), []);

  const ui = useMemo(() => ({
    openAssistant,
    openReport,
    openDocument,
    issuesRevision,
    refreshIssues,
    userLocation,
    setUserLocation,
  }), [openAssistant, openReport, openDocument, issuesRevision, refreshIssues, userLocation]);

  return (
    <UiContext.Provider value={ui}>
      <RouteScrollManager />
      <a className="visually-hidden-focusable skip-link" href="#main-content">Skip to content</a>
      <Navigation />
      <main id="main-content">
        <Suspense fallback={<div className="container py-5 mt-5 text-muted" role="status">Loading SCMIRN workspace...</div>}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/offices" element={<OfficesPage />} />
            <Route path="/heatmap" element={<HeatmapPage />} />
            <Route path="/tracker" element={<TrackerPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/platform" element={<PlatformPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
      <AssistantPanel open={assistantOpen} initialPrompt={assistantPrompt} onClose={closeAssistant} />
      <AssistantOrb onClick={() => assistantOpen ? closeAssistant() : openAssistant()} expanded={assistantOpen} />
      <ReportIssueModal open={reportOpen} location={userLocation} onClose={closeReport} onSubmitted={refreshIssues} />
      <DocumentGeneratorModal open={documentOpen} initialType={documentType} onClose={closeDocument} />
    </UiContext.Provider>
  );
}

export function App() {
  return <BrowserRouter><AppFrame /></BrowserRouter>;
}

export default App;
