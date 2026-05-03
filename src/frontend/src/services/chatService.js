const API_BASE_URL = "http://localhost:8000";

export async function sendChatMessage({ utilisateurId, moduleId, question }) {
  const response = await fetch(`${API_BASE_URL}/chat/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      utilisateur_id: utilisateurId,
      module_id: moduleId,
      question,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail || "Aucune reponse(erreur) .");
  }

  return data;
}

export async function getChatHistory({ utilisateurId, moduleId }) {
  const query = new URLSearchParams({
    utilisateur_id: String(utilisateurId),
    module_id: String(moduleId),
  });

  const response = await fetch(`${API_BASE_URL}/chat/history?${query.toString()}`);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail || "Impossible de charger l'historique.");
  }

  return data;
}

export async function clearChatHistory(utilisateurId) {
  const query = new URLSearchParams({
    utilisateur_id: String(utilisateurId),
  });

  const response = await fetch(`${API_BASE_URL}/chat/history?${query.toString()}`, {
    method: "DELETE",
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail || "Impossible de supprimer l'historique.");
  }

  return data;
}
