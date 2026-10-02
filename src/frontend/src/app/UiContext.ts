import { createContext, useContext } from 'react';
import type { DocumentType } from '@/utils/documentTemplates';

export interface CivicLocation {
  lat: number;
  lng: number;
  accuracy?: number;
}

export interface UiContextValue {
  openAssistant: (prompt?: string) => void;
  openReport: () => void;
  openDocument: (docType?: DocumentType) => void;
  issuesRevision: number;
  refreshIssues: () => void;
  userLocation: CivicLocation | null;
  setUserLocation: (location: CivicLocation) => void;
}

export const UiContext = createContext<UiContextValue | null>(null);

export function useCivicUi(): UiContextValue {
  const value = useContext(UiContext);
  if (!value) throw new Error('useCivicUi must be used inside the SCMIRN app shell.');
  return value;
}
