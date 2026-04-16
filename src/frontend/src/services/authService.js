import allowedUsers from "../data/users.json";

const SESSION_STORAGE_KEY = "ap-up-auth-user";

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

const wait = (delay) =>
  new Promise((resolve) => {
    window.setTimeout(resolve, delay);
  });

const sanitizeUser = (user) => ({
  id: user.id,
  email: user.email,
  name: user.name,
  role: user.role,
});

export async function loginUser({ email, password }) {
  await wait(350);

  const normalizedEmail = email.trim().toLowerCase();
  const user = allowedUsers.find(
    (candidate) =>
      candidate.email.toLowerCase() === normalizedEmail &&
      candidate.password === password
  );

  if (!user) {
    throw new Error("Email ou mot de passe incorrect.");
  }

  const sanitizedUser = sanitizeUser(user);
  storage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sanitizedUser));
  return sanitizedUser;
}

export function getAuthenticatedUser() {
  const storedUser = storage.getItem(SESSION_STORAGE_KEY);

  if (!storedUser) {
    return null;
  }

  try {
    return JSON.parse(storedUser);
  } catch {
    storage.removeItem(SESSION_STORAGE_KEY);
    return null;
  }
}

export function clearAuthenticatedUser() {
  storage.removeItem(SESSION_STORAGE_KEY);
}

export function canAccessProfessorDashboard(user) {
  return Boolean(user) && user.role !== "Étudiante";
}
