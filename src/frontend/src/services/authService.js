const SESSION_STORAGE_KEY = "ap-up-auth-user";
const API_BASE_URL = "http://localhost:8000";

const storage = {
  getItem(key) {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {
      console.warn(
        "Impossible d'enregistrer l'état d'authentification dans localStorage."
      );
    }
  },
  removeItem(key) {
    try {
      localStorage.removeItem(key);
    } catch {
      console.warn(
        "Impossible d'effacer l'état d'authentification depuis localStorage."
      );
    }
  },
};

export async function loginUser({ email, password }) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      email,
      password,
    }),
  });

  let user = null;

  try {
    user = await response.json();
  } catch {
    user = null;
  }

  if (!response.ok) {
    throw new Error(user?.detail || "Email ou mot de passe incorrect.");
  }

  storage.setItem(SESSION_STORAGE_KEY, JSON.stringify(user));
  return user;
}

export function getAuthenticatedUser() {
  const storedUser = storage.getItem(SESSION_STORAGE_KEY);

  if (!storedUser) {
    return null;
  }

  try {
    const user = JSON.parse(storedUser);

    if (!user.nom || !user.prenom || !user.email || !user.role) {
      storage.removeItem(SESSION_STORAGE_KEY);
      return null;
    }

    return user;
  } catch {
    storage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

export function clearAuthenticatedUser() {
  storage.removeItem(SESSION_STORAGE_KEY);
}

export function canAccessProfessorDashboard(user) {
  return Boolean(user) && user.role === "enseignant";
}
