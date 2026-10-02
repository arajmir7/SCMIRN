import { useEffect, useState, type FormEvent } from 'react';
import { apiPostForm } from '@/api/http';
import type { CivicLocation } from '@/app/UiContext';
import { DialogFrame } from '@/components/shared/DialogFrame';

interface ReportResponse {
  success: boolean;
  error?: string;
}

interface ReportIssueModalProps {
  open: boolean;
  location: CivicLocation | null;
  onClose: () => void;
  onSubmitted: () => void;
}

const initialValues = {
  title: '',
  description: '',
  category: 'road',
  lat: '',
  lon: '',
};

export function ReportIssueModal({ open, location, onClose, onSubmitted }: ReportIssueModalProps) {
  const [values, setValues] = useState(initialValues);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [consent, setConsent] = useState(false);
  const [includeLocation, setIncludeLocation] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'danger'; text: string } | null>(null);

  useEffect(() => {
    const next = files.map((file) => URL.createObjectURL(file));
    setPreviews(next);
    return () => next.forEach((url) => URL.revokeObjectURL(url));
  }, [files]);

  useEffect(() => {
    if (!open) return;
    setFeedback(null);
    setConsent(false);
    setIncludeLocation(false);
  }, [open]);

  const update = (field: keyof typeof initialValues, value: string) => {
    setValues((previous) => ({ ...previous, [field]: value }));
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent) return;
    setFeedback(null);
    setLoading(true);
    const formData = new FormData();
    formData.append('title', values.title);
    formData.append('description', values.description);
    formData.append('category', values.category);
    if (values.lat.trim()) formData.append('lat', values.lat);
    if (values.lon.trim()) formData.append('lon', values.lon);
    files.forEach((file) => formData.append('media', file));

    const result = await apiPostForm<ReportResponse>('/api/report-issue', formData);
    setLoading(false);
    if (!result.ok) {
      setFeedback({ kind: 'danger', text: result.error });
      return;
    }
    if (!result.data?.success) {
      setFeedback({ kind: 'danger', text: result.data?.error ?? 'Unable to submit the report.' });
      return;
    }
    setFeedback({ kind: 'success', text: 'SCMIRN demo record saved. No government agency was contacted and no complaint was filed.' });
    onSubmitted();
  }

  return (
    <DialogFrame open={open} title="Create SCMIRN Demo Record" onClose={onClose} size="large">
      <div className="modal-body">
        <div className="alert alert-warning small" role="note">
          This prototype saves a record to SCMIRN only. It does not notify or file with a government agency. Avoid personal identifiers and do not upload images showing people, documents, or private information.
        </div>
        <form onSubmit={submit} encType="multipart/form-data">
          <div className="mb-3">
            <label className="visually-hidden" htmlFor="report-title">Issue title</label>
            <input id="report-title" type="text" name="title" className="form-control form-control-lg"
              placeholder="What's the issue? (e.g., Dangerous pothole near school)" required maxLength={500}
              value={values.title} onChange={(event) => update('title', event.target.value)} />
          </div>
          <div className="mb-3">
            <label className="visually-hidden" htmlFor="report-description">Issue description</label>
            <textarea id="report-description" name="description" className="form-control" rows={3}
              placeholder="Describe the issue without names, account numbers, or other personal details..." required maxLength={2000}
              value={values.description} onChange={(event) => update('description', event.target.value)} />
          </div>
          {location ? <div className="form-check mb-3">
            <input id="report-include-location" className="form-check-input" type="checkbox" checked={includeLocation}
              onChange={(event) => {
                const checked = event.target.checked;
                setIncludeLocation(checked);
                setValues((previous) => ({
                  ...previous,
                  lat: checked ? String(location.lat) : '',
                  lon: checked ? String(location.lng) : '',
                }));
              }} />
            <label htmlFor="report-include-location" className="form-check-label small">Include detected device coordinates in this SCMIRN demo record (optional; exact coordinates will be sent).</label>
          </div> : null}
          <div className="row g-3 mb-3">
            <div className="col-md-6">
              <label className="visually-hidden" htmlFor="report-category">Issue category</label>
              <select id="report-category" name="category" className="form-select" value={values.category}
                onChange={(event) => update('category', event.target.value)}>
                <option value="road">🛣️ Road Infrastructure</option>
                <option value="water">💧 Water &amp; Sanitation</option>
                <option value="electricity">⚡ Electricity</option>
                <option value="safety">🚨 Public Safety</option>
                <option value="corruption">⚖️ Corruption/Governance</option>
              </select>
            </div>
          </div>
          <div className="row g-3 mb-3">
            <div className="col-md-6">
              <label className="visually-hidden" htmlFor="report-lat">Latitude</label>
              <input id="report-lat" type="number" step="any" name="lat" className="form-control"
                placeholder="Latitude" value={values.lat} onChange={(event) => update('lat', event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="visually-hidden" htmlFor="report-lon">Longitude</label>
              <input id="report-lon" type="number" step="any" name="lon" className="form-control"
                placeholder="Longitude" value={values.lon} onChange={(event) => update('lon', event.target.value)} />
            </div>
          </div>
          <div className="mb-3">
            <label className="border border-dashed rounded-3 p-4 text-center bg-light w-100 report-upload" htmlFor="report-photos">
              <i className="fas fa-camera fa-2x text-muted mb-2" aria-hidden="true" />
              <span className="d-block text-muted">Click to upload photos of the issue</span>
            </label>
            <input id="report-photos" type="file" name="media" multiple accept="image/*" className="visually-hidden"
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))} />
            <div className="d-flex gap-2 mt-2 flex-wrap" aria-live="polite">
              {previews.map((src, index) => (
                <img key={src} src={src} alt={`Issue photo ${index + 1}`} className="report-photo-preview" />
              ))}
            </div>
          </div>
          <div className="form-check mb-3">
            <input id="report-consent" className="form-check-input" type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
            <label htmlFor="report-consent" className="form-check-label small">I understand this saves a prototype record in SCMIRN only and does not file a report with an agency.</label>
          </div>
          {feedback ? <div className={`alert alert-${feedback.kind}`} role="status">{feedback.text}</div> : null}
          <button type="submit" className="btn btn-primary w-100 py-3 fw-bold" disabled={loading || !consent}>
            {loading ? <><i className="fas fa-circle-notch fa-spin me-2" aria-hidden="true" />Saving demo record…</> : <><i className="fas fa-save me-2" aria-hidden="true" />Save SCMIRN Demo Record</>}
          </button>
        </form>
      </div>
    </DialogFrame>
  );
}
