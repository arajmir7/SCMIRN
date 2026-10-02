export type JsonObject = Record<string, unknown>;

export function asJsonObject(value: unknown): JsonObject | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as JsonObject)
    : null;
}

export function getJsonValue(value: unknown, ...path: string[]): unknown {
  let current: unknown = value;
  for (const key of path) {
    const record = asJsonObject(current);
    if (!record) return undefined;
    current = record[key];
  }
  return current;
}
