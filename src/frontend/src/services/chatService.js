// src/frontend/src/services/chatService.js
import { buildApiUrl } from "./apiClient";

export const CHAT_CONNECTION_LABEL = "Connecté à l'API"; 

export async function sendMessage({ utilisateur_id, module_id, question }) {
  const response = await fetch(buildApiUrl("/chat/message"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ utilisateur_id, module_id, question }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Erreur lors de l'envoi du message.");
  }

  return response.json(); // Retourne : { id, question, reponse, chunks_sources, ... }
}