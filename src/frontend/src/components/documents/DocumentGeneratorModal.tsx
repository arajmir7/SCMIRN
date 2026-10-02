import { useEffect, useState, type FormEvent } from 'react';
import { apiPost } from '@/api/http';
import { DialogFrame } from '@/components/shared/DialogFrame';
import { buildTemplateData, DOCUMENT_TYPES, type DocumentFormValues, type DocumentType } from '@/utils/documentTemplates';

interface GenerateResponse {
  success: boolean;
  content?: string;
  error?: string;
}

interface DocumentGeneratorModalProps {
  open: boolean;
  initialType: DocumentType;
  onClose: () => void;
}

const labels: Record<DocumentType, string> = {
  rti: 'RTI Application',
  fir: 'FIR Complaint',
  consumer: 'Consumer Complaint',
  electricity: 'Electricity Grievance',
  rent: 'Rent Dispute Notice',
  scholarship: 'Scholarship Grievance',
  pension: 'Pension Grievance',
  cybercrime: 'Cybercrime Complaint',
};

const initialValues: DocumentFormValues = {
  docType: 'rti', department: '', name: '', phone: '', address: '', issue: '',
};

export function DocumentGeneratorModal({ open, initialType, onClose }: DocumentGeneratorModalProps) {
  const [values, setValues] = useState<DocumentFormValues>(initialValues);
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [syntheticDataConfirmed, setSyntheticDataConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setValues((previous) => ({ ...previous, docType: initialType }));
    setError(null);
    setSyntheticDataConfirmed(false);
  }, [open, initialType]);

  const update = (field: keyof DocumentFormValues, value: string) => {
    setValues((previous) => ({ ...previous, [field]: value }));
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!syntheticDataConfirmed) return;
    setLoading(true);
    setError(null);
    const result = await apiPost<GenerateResponse>('/api/documents/generate', {
      doc_type: values.docType,
      template_data: buildTemplateData(values),
    });
    setLoading(false);
    if (!result.ok) {
      setError(result.error);
      setOutput('');
      return;
    }
    if (!result.data?.success) {
      setError(result.data?.error ?? 'Failed to generate draft.');
      setOutput('');
      return;
    }
    setOutput(result.data.content ?? 'No content returned');
  }

  return (
    <DialogFrame open={open} title="Generate Unreviewed Draft" onClose={onClose} size="large">
      <div className="modal-body">
        <div className="alert alert-warning small" role="note">
          Prototype template only. Do not enter real names, phone numbers, addresses, or case details. The backend may retain generated drafts. Output is not legally reviewed and is not filed with an agency.
        </div>
        <form onSubmit={submit}>
          <div className="row g-3 mb-3">
            <div className="col-md-6">
              <label className="form-label small text-muted" htmlFor="document-type">Application Type</label>
              <select id="document-type" name="doc_type" className="form-select" required value={values.docType}
                onChange={(event) => update('docType', event.target.value as DocumentType)}>
                {DOCUMENT_TYPES.map((type) => <option value={type} key={type}>{labels[type]}</option>)}
              </select>
            </div>
            <div className="col-md-6">
              <label className="form-label small text-muted" htmlFor="document-department">Department / Authority</label>
              <input id="document-department" type="text" className="form-control" placeholder="Department name"
                value={values.department} onChange={(event) => update('department', event.target.value)} />
            </div>
          </div>
          <div className="row g-3 mb-3">
            <div className="col-md-6">
              <label className="form-label small text-muted" htmlFor="document-name">Applicant Name</label>
              <input id="document-name" type="text" className="form-control" placeholder="Your full name" required
                value={values.name} onChange={(event) => update('name', event.target.value)} />
            </div>
            <div className="col-md-6">
              <label className="form-label small text-muted" htmlFor="document-phone">Contact Number</label>
              <input id="document-phone" type="tel" className="form-control" placeholder="+91..." required
                value={values.phone} onChange={(event) => update('phone', event.target.value)} />
            </div>
          </div>
          <div className="mb-3">
            <label className="form-label small text-muted" htmlFor="document-address">Address</label>
            <input id="document-address" type="text" className="form-control" placeholder="Full address" required
              value={values.address} onChange={(event) => update('address', event.target.value)} />
          </div>
          <div className="mb-3">
            <label className="form-label small text-muted" htmlFor="document-issue">Issue / Request Summary</label>
            <textarea id="document-issue" className="form-control" rows={4} placeholder="Describe your case in 4-6 lines" required
              value={values.issue} onChange={(event) => update('issue', event.target.value)} />
          </div>
          <div className="form-check mb-3">
            <input id="document-synthetic-data" className="form-check-input" type="checkbox" checked={syntheticDataConfirmed} onChange={(event) => setSyntheticDataConfirmed(event.target.checked)} />
            <label htmlFor="document-synthetic-data" className="form-check-label small">I have entered synthetic test information only.</label>
          </div>
          {error ? <div className="alert alert-danger" role="alert">Generation error: {error}</div> : null}
          <button type="submit" className="btn btn-primary w-100 fw-bold py-2" disabled={loading || !syntheticDataConfirmed}>
            {loading ? <><i className="fas fa-circle-notch fa-spin me-2" aria-hidden="true" />Generating...</> : <><i className="fas fa-file-signature me-2" aria-hidden="true" />Generate Draft</>}
          </button>
        </form>
        <div className="mt-4">
          <label className="form-label small text-muted" htmlFor="generated-document">Unreviewed Draft Output</label>
          <textarea id="generated-document" className="form-control doc-preview" rows={14}
            placeholder="Generated application will appear here..." readOnly value={output} />
        </div>
      </div>
    </DialogFrame>
  );
}
