const API_BASE_URL = "http://localhost:8000";

export async function getModules() {
  const response = await fetch(`${API_BASE_URL}/database/modules`);
  const modules = await response.json();

  if (!response.ok) {
    throw new Error(modules?.detail || "Impossible de charger les cours.");
  }

  return modules;
}

export async function getDefaultModule() {
  const modules = await getModules();
  return modules[0] || null;
}

export async function updateModulePrompt(moduleId, systemPrompt) {
  const response = await fetch(`${API_BASE_URL}/database/modules/${moduleId}/prompt`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ system_prompt: systemPrompt }),
  });
  const module = await response.json();

  if (!response.ok) {
    throw new Error(module?.detail || "Impossible d'enregistrer le prompt.");
  }

  return module;
}
