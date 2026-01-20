function toNumber(v) {
  if (v === null || v === undefined) return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function normalizeRow(r) {
  const timestamp = r.timestamp ?? r.ts ?? null;

  return {
    timestamp,
    temperature: toNumber(r.temperature),
    humidity: toNumber(r.humidity),
    mq2: toNumber(r.mq2),
    mq7: toNumber(r.mq7),
    thresholds: r.thresholds ?? null,
  };
}

export async function getHistory() {
  const res = await fetch("/api/data");
  const data = await res.json();

  const rows = Array.isArray(data) ? data : [];

  const normalized = rows
    .map(normalizeRow)
    .filter(r => r.timestamp);

  // sort po czasie rosnąco – wykresy przestają "skakać"
  normalized.sort((a, b) =>
    String(a.timestamp).localeCompare(String(b.timestamp))
  );

  return normalized;
}
