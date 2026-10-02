export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string; details?: unknown };

async function safeJson(res: Response): Promise<unknown> {
  try {
    return (await res.json()) as unknown;
  } catch {
    return null;
  }
}

function responseError(payload: unknown, status: number): string {
  if (payload && typeof payload === 'object' && !Array.isArray(payload) && 'error' in payload) {
    const message = payload.error;
    if (typeof message === 'string' && message.length > 0) return message;
    if (message && typeof message === 'object' && !Array.isArray(message) && 'message' in message) {
      const detail = message.message;
      if (typeof detail === 'string' && detail.length > 0) return detail;
    }
  }
  return `HTTP ${status}`;
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetch(path, { method: 'GET', signal });
  } catch (error: unknown) {
    return { ok: false, error: error instanceof Error ? error.message : 'Network error' };
  }

  const payload = await safeJson(res);
  if (!res.ok) {
    return { ok: false, error: responseError(payload, res.status), details: payload };
  }
  return { ok: true, data: payload as T };
}

export async function apiPost<T>(path: string, body: unknown, signal?: AbortSignal, headers?: HeadersInit): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...Object.fromEntries(new Headers(headers).entries()) },
      body: JSON.stringify(body),
      signal,
    });
  } catch (error: unknown) {
    return { ok: false, error: error instanceof Error ? error.message : 'Network error' };
  }

  const payload = await safeJson(res);
  if (!res.ok) {
    return { ok: false, error: responseError(payload, res.status), details: payload };
  }
  return { ok: true, data: payload as T };
}

export async function apiPostForm<T>(path: string, body: FormData, signal?: AbortSignal): Promise<ApiResult<T>> {
  let res: Response;
  try {
    res = await fetch(path, { method: 'POST', body, signal });
  } catch (error: unknown) {
    return { ok: false, error: error instanceof Error ? error.message : 'Network error' };
  }

  const payload = await safeJson(res);
  if (!res.ok) {
    return { ok: false, error: responseError(payload, res.status), details: payload };
  }
  return { ok: true, data: payload as T };
}
