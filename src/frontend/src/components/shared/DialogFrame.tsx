import { useEffect, useRef, type ReactNode } from 'react';

interface DialogFrameProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  size?: 'default' | 'large';
}

export function DialogFrame({ open, title, onClose, children, size = 'default' }: DialogFrameProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    document.body.classList.add('modal-open');

    const focusable = () => Array.from(
      dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])'
      ) ?? []
    ).filter((element) => !element.hasAttribute('hidden'));

    focusable()[0]?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = focusable();
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousOverflow;
      document.body.classList.remove('modal-open');
      previousFocus?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="modal-backdrop fade show" aria-hidden="true" onMouseDown={onClose} />
      <div className="modal fade show d-block civic-modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className={`modal-dialog modal-dialog-centered ${size === 'large' ? 'modal-lg' : ''}`}>
          <div ref={dialogRef} className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title fs-5 fw-bold">{title}</h2>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
            </div>
            {children}
          </div>
        </div>
      </div>
    </>
  );
}
