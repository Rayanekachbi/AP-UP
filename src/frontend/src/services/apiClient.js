export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, { status, details } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function buildApiUrl(path) {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function request() {
  throw new ApiError(
    "Aucun backend n'est connecté pour le moment. Remplacez ce placeholder par un appel FastAPI lorsque l'API sera disponible."
  );
}
