import { useCivicUi } from '@/app/UiContext';
import type { DocumentType } from '@/utils/documentTemplates';

const documentInfo: Record<DocumentType, { title: string; copy: string; color: string }> = {
  rti: { title: 'RTI Draft Template', copy: 'Unreviewed sample; verify current requirements and fees before use.', color: 'info' },
  fir: { title: 'FIR Draft Template', copy: 'Unreviewed sample; this does not register a police complaint.', color: 'danger' },
  consumer: { title: 'Consumer Draft Template', copy: 'Unreviewed sample; verify current forum rules before use.', color: 'success' },
  electricity: { title: 'Electricity Draft Template', copy: 'Unreviewed sample; not sent to a provider.', color: 'secondary' },
  rent: { title: 'Rent Dispute Draft', copy: 'Unreviewed sample; not legal advice or a formal notice.', color: 'dark' },
  scholarship: { title: 'Scholarship Draft Template', copy: 'Unreviewed sample; not sent to an authority.', color: 'primary' },
  pension: { title: 'Pension Draft Template', copy: 'Unreviewed sample; not submitted to an authority.', color: 'warning' },
  cybercrime: { title: 'Cybercrime Draft Template', copy: 'Unreviewed sample; urgent fraud should be reported through official channels.', color: 'primary' },
};

export function DocumentsPage() {
  const { openDocument } = useCivicUi();
  const featuredDocumentTypes: DocumentType[] = ['rti', 'fir', 'consumer', 'electricity', 'pension', 'cybercrime'];
  return (
    <section className="py-5">
      <div className="container py-5">
        <div className="row justify-content-center text-center mb-4"><div className="col-lg-8">
          <h1 className="display-5 fw-bold">Unreviewed Draft Templates</h1>
          <p className="lead text-muted">Prototype document samples only · not legal advice · not submitted to agencies</p>
        </div></div>
        <div className="row g-4">
          {featuredDocumentTypes.map((type) => {
            const doc = documentInfo[type];
            return <div className="col-md-4" key={type}><article className="card h-100 border-0 shadow-sm"><div className="card-body">
              <h2 className="h5 fw-bold mb-2">{doc.title}</h2><p className="text-muted small mb-3">{doc.copy}</p>
              <button type="button" className={`btn btn-outline-${doc.color} w-100`} onClick={() => openDocument(type)}>Generate</button>
            </div></article></div>;
          })}
        </div>
      </div>
    </section>
  );
}

export default DocumentsPage;
