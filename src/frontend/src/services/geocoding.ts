export interface GeocodedPlace {
  lat: number;
  lng: number;
  label: string;
}

export async function geocodePlace(query: string, signal?: AbortSignal): Promise<GeocodedPlace | null> {
  const params = new URLSearchParams({ format: 'json', limit: '1', q: query });
  const response = await fetch(`https://nominatim.openstreetmap.org/search?${params.toString()}`, {
    headers: { Accept: 'application/json' },
    signal,
  });
  if (!response.ok) throw new Error('Search service unavailable. Please try again.');
  const results: unknown = await response.json();
  if (!Array.isArray(results) || !results.length) return null;

  const first = results[0] as { lat?: string; lon?: string; display_name?: string };
  const lat = Number(first.lat);
  const lng = Number(first.lon);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) throw new Error('Invalid location result.');
  return { lat, lng, label: first.display_name ?? query };
}
