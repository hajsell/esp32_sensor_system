export async function getHistory() {
  const res = await fetch("/data");
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}
