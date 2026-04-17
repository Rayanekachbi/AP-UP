// src/frontend/src/services/authService.js
import { buildApiUrl, ApiError } from "./apiClient";

const SESSION_STORAGE_KEY = "ap-up-auth-user";

export async function loginUser({ email, password }) {
  const response = await fetch(buildApiUrl("/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Email ou mot de passe incorrect.");
  }

  const user = await response.json();

  // Adapter le format : l'API retourne { id, nom, prenom, email, role }
  const sanitized = {
    id: user.id,
    email: user.email,
    name: `${user.prenom} ${user.nom}`,
    role: user.role,
  };

  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sanitized));
  return sanitized;
}

export function getAuthenticatedUser() {
  try {
    const stored = localStorage.getItem(SESSION_STORAGE_KEY);
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
}

export function clearAuthenticatedUser() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function canAccessProfessorDashboard(user) {
  return Boolean(user) && user.role === "enseignant";
}