const API_BASE_URL = "http://localhost:8000";

export async function getUploadedDocuments() {
  const response = await fetch(`${API_BASE_URL}/ingestion/documents`);
  const documents = await response.json();

  if (!response.ok) {
    throw new Error(documents?.detail || "Impossible de charger les documents.");
  }

  return documents;
}

export async function uploadDocument({ moduleId, enseignantId, title, file }) {
  const formData = new FormData();
  formData.append("module_id", moduleId);
  formData.append("enseignant_id", enseignantId);
  formData.append("title", title);
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/ingestion/documents/upload`, {
    method: "POST",
    body: formData,
  });
  const result = await response.json();

  if (!response.ok) {
    throw new Error(result?.detail || "Impossible d'importer le document.");
  }

  return result;
}

export async function deleteDocument(documentId) {
  const response = await fetch(`${API_BASE_URL}/ingestion/documents/${documentId}`, {
    method: "DELETE",
  });
  const result = await response.json();

  if (!response.ok) {
    throw new Error(result?.detail || "Impossible de supprimer le document.");
  }

  return result;
}
