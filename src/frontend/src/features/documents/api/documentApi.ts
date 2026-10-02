import { apiGet } from '@/api/http';

export type DocumentStatus = 'processing' | 'completed' | 'failed' | 'draft';

export interface DocumentDetails {
  id: string;
  title: string;
  status: DocumentStatus | string;
  type: string;
  createdAt: string;
  fileSize: number;
}

const getById = async (id: string): Promise<DocumentDetails> => {
  const result = await apiGet<{
    data?: Partial<DocumentDetails>;
    success?: boolean;
    error?: string;
  } & Partial<DocumentDetails>>(`/api/documents/${encodeURIComponent(id)}`);
  if (!result.ok) throw new Error(result.error);
  const data = result.data.data ?? result.data;
  if (typeof data.id !== 'string' || data.id.length === 0) {
    throw new Error(result.data.error ?? 'Document not found.');
  }

  return {
    id: data.id,
    title: data.title ?? `Document ${id}`,
    status: data.status ?? 'draft',
    type: data.type ?? 'RTI',
    createdAt: data.createdAt ?? '',
    fileSize: Number.isFinite(data.fileSize) ? Number(data.fileSize) : 0,
  };
};

export const documentApi = {
  getById,
};
