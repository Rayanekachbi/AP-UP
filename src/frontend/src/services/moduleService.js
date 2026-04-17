// src/frontend/src/services/moduleService.js
import { buildApiUrl } from "./apiClient";

export async function getModules() {
  const response = await fetch(buildApiUrl("/database/modules"));
  if (!response.ok) throw new Error("Impossible de charger les modules.");
  return response.json(); // [{ id, nom, description }]
}