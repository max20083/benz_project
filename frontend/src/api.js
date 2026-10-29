async function readError(response, fallback) {
  const data = await response.json().catch(() => null);
  if (typeof data?.detail === "string") return data.detail;
  return fallback;
}

export async function getCatalog() {
  const response = await fetch("/api/catalog");
  if (!response.ok) throw new Error(await readError(response, "Справочник недоступен"));
  return response.json();
}

export async function listSessions() {
  const response = await fetch("/api/sessions?limit=12");
  if (!response.ok) throw new Error(await readError(response, "История недоступна"));
  return response.json();
}

export async function startSession(payload) {
  const response = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await readError(response, "Не удалось начать заправку"));
  return response.json();
}

export async function stopSession(id) {
  const response = await fetch(`/api/sessions/${id}/stop`, { method: "POST" });
  if (!response.ok) throw new Error(await readError(response, "Не удалось остановить колонку"));
  return response.json();
}
