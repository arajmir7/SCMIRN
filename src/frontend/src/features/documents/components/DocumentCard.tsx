import type { FC, HTMLAttributes, ReactNode } from 'react';
import { useDocument } from '../hooks/useDocument';
import { Button, Badge, Skeleton } from '@/components/atoms';

interface DocumentCardProps {
  documentId: string;
  onDownload: (id: string) => void;
}

interface MotionDivProps extends HTMLAttributes<HTMLDivElement> {
  initial?: unknown;
  animate?: unknown;
  whileHover?: unknown;
}

const MotionDiv: FC<MotionDivProps> = ({ initial, animate, whileHover, ...rest }) => (
  <div {...rest} />
);

const motion = {
  div: MotionDiv,
};

export const DocumentCard: FC<DocumentCardProps> = ({
  documentId,
  onDownload
}) => {
  const { data: doc, isLoading, error } = useDocument(documentId);

  if (isLoading) return <DocumentCardSkeleton />;
  if (error) return <ErrorState error={error} />;
  if (!doc) return <ErrorState error={new Error('Document not found.')} />;

  const handleShare = async () => {
    const shareText = `${doc.title} (${doc.type})`;
    const shareUrl = typeof window !== 'undefined' ? window.location.href : '';

    try {
      if (typeof navigator !== 'undefined' && navigator.share) {
        await navigator.share({
          title: doc.title,
          text: shareText,
          url: shareUrl,
        });
        return;
      }

      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrl || shareText);
      }
    } catch {
      // Best-effort sharing; ignore errors to keep UI responsive.
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}
      className="document-card"
    >
      <div className="card-header">
        <Badge variant={getStatusVariant(doc.status)}>
          {doc.status}
        </Badge>
        <h3>{doc.title}</h3>
      </div>

      <div className="card-body">
        <MetadataGrid>
          <MetadataItem label="Created" value={formatDate(doc.createdAt)} />
          <MetadataItem label="Type" value={doc.type} />
          <MetadataItem label="Size" value={formatBytes(doc.fileSize)} />
        </MetadataGrid>
      </div>

      <div className="card-actions">
        <Button
          variant="primary"
          onClick={() => onDownload(documentId)}
          icon={<DownloadIcon />}
        >
          Download PDF
        </Button>
        <Button variant="ghost" onClick={handleShare}>
          Share
        </Button>
      </div>
    </motion.div>
  );
};

const DocumentCardSkeleton: FC = () => (
  <div className="document-card skeleton">
    <div className="card-header">
      <Skeleton width="86px" height="20px" />
      <Skeleton width="60%" height="24px" />
    </div>
    <div className="card-body">
      <Skeleton width="90%" height="16px" />
      <Skeleton width="70%" height="16px" />
      <Skeleton width="40%" height="16px" />
    </div>
    <div className="card-actions">
      <Skeleton width="120px" height="36px" />
      <Skeleton width="80px" height="36px" />
    </div>
  </div>
);

const ErrorState: FC<{ error: Error }> = ({ error }) => (
  <div className="document-card error-state" role="alert">
    <h4>Unable to load document</h4>
    <p>{error.message}</p>
  </div>
);

const MetadataGrid: FC<{ children: ReactNode }> = ({ children }) => (
  <div className="metadata-grid">{children}</div>
);

const MetadataItem: FC<{ label: string; value: string | number }> = ({ label, value }) => (
  <div className="metadata-item">
    <span className="metadata-label">{label}</span>
    <span className="metadata-value">{value}</span>
  </div>
);

const DownloadIcon: FC = () => (
  <svg
    aria-hidden="true"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const getStatusVariant = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'warning';
    case 'failed':
      return 'danger';
    default:
      return 'neutral';
  }
};

const formatDate = (value: string) => {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(parsed);
};

const formatBytes = (value: number) => {
  if (!Number.isFinite(value) || value <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
};
