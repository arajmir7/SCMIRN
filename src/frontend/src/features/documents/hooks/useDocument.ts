import { useEffect, useState } from 'react';
import { documentApi, type DocumentDetails } from '../api/documentApi';

interface UseDocumentState {
  data: DocumentDetails | null;
  isLoading: boolean;
  error: Error | null;
}

export const useDocument = (id: string): UseDocumentState => {
  const [state, setState] = useState<UseDocumentState>({
    data: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let isActive = true;

    setState((prev) => ({
      data: null,
      isLoading: true,
      error: null,
    }));

    documentApi
      .getById(id)
      .then((doc) => {
        if (!isActive) return;
        setState({
          data: doc,
          isLoading: false,
          error: null,
        });
      })
      .catch((err: unknown) => {
        if (!isActive) return;
        const error = err instanceof Error ? err : new Error('Unable to load document');
        setState({
          data: null,
          isLoading: false,
          error,
        });
      });

    return () => {
      isActive = false;
    };
  }, [id]);

  return state;
};
