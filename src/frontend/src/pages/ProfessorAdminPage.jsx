import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../routes/paths";
import { getModules, updateModulePrompt } from "../services/moduleService";
import {
  deleteDocument,
  getUploadedDocuments,
  uploadDocument,
} from "../services/professorDashboardService";
import "../styles/ProfessorAdminPanel.css";

export default function ProfessorAdminPage({ user, onLogout }) {
  const navigate = useNavigate();
  const fullName = `${user.prenom} ${user.nom}`;
  const initial = user.prenom?.charAt(0) || user.email.charAt(0);
  const [activeTab, setActiveTab] = useState("documents");
  const [modulesData, setModulesData] = useState([]);
  const [documentsData, setDocumentsData] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [modulesError, setModulesError] = useState("");
  const [documentsError, setDocumentsError] = useState("");
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [customCourse, setCustomCourse] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [promptSaving, setPromptSaving] = useState(false);
  const [promptMessage, setPromptMessage] = useState("");

  const courses = useMemo(
    () => [...new Set(modulesData.map((module) => module.nom))],
    [modulesData]
  );

  const documentTitle = customCourse.trim() || selectedFile?.name || "";
  const uploadedDocuments = useMemo(() => {
    return documentsData.filter((document) => document.course === selectedCourse);
  }, [documentsData, selectedCourse]);
  const selectedModule = modulesData.find((module) => module.nom === selectedCourse);
  const canUpload = Boolean(selectedModule && selectedFile && !uploading);

  async function loadDocuments() {
    try {
      setDocumentsLoading(true);
      setDocumentsError("");
      const documents = await getUploadedDocuments();
      setDocumentsData(documents);
    } catch (error) {
      setDocumentsError(
        error instanceof Error
          ? error.message
          : "Impossible de charger les documents."
      );
    } finally {
      setDocumentsLoading(false);
    }
  }

  useEffect(() => {
    let ignore = false;

    async function loadModules() {
      try {
        setModulesError("");
        const modules = await getModules();

        if (ignore) {
          return;
        }

        setModulesData(modules);
        setSelectedCourse(modules[0]?.nom || "");
      } catch (error) {
        if (!ignore) {
          setModulesError(
            error instanceof Error
              ? error.message
              : "Impossible de charger les cours."
          );
        }
      }
    }

    loadModules();

    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedModule) {
      return;
    }

    setSystemPrompt(selectedModule.system_prompt || "");
    setPromptMessage("");
  }, [selectedModule?.id]);

  useEffect(() => {
    let ignore = false;

    async function loadDocumentsFromApi() {
      try {
        const documents = await getUploadedDocuments();

        if (ignore) {
          return;
        }

        setDocumentsData(documents);
      } catch (error) {
        if (!ignore) {
          setDocumentsError(
            error instanceof Error
              ? error.message
              : "Impossible de charger les documents."
          );
        }
      } finally {
        if (!ignore) {
          setDocumentsLoading(false);
        }
      }
    }

    setDocumentsLoading(true);
    setDocumentsError("");
    loadDocumentsFromApi();

    return () => {
      ignore = true;
    };
  }, []);

  const handleBackToMainWorkspace = () => {
    navigate(ROUTES.workspace);
  };

  const handleLogout = () => {
    onLogout();
    navigate(ROUTES.login, { replace: true });
  };

  const handleUploadDocument = async (event) => {
    event.preventDefault();

    if (!selectedModule || !selectedFile) {
      setUploadMessage("Choisissez un cours et un fichier.");
      return;
    }

    try {
      setUploading(true);
      setUploadMessage("Import du document en cours...");
      await uploadDocument({
        moduleId: selectedModule.id,
        enseignantId: user.id,
        title: documentTitle,
        file: selectedFile,
      });
      setSelectedFile(null);
      setCustomCourse("");
      setUploadMessage("Document importé et indexé.");
      await loadDocuments();
    } catch (error) {
      setUploadMessage(
        error instanceof Error
          ? error.message
          : "Impossible d'importer le document."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    try {
      setDocumentsError("");
      await deleteDocument(documentId);
      setDocumentsData((documents) =>
        documents.filter((document) => document.id !== documentId)
      );
    } catch (error) {
      setDocumentsError(
        error instanceof Error
          ? error.message
          : "Impossible de supprimer le document."
      );
    }
  };

  const handleSaveSystemPrompt = async () => {
    if (!selectedModule) {
      setPromptMessage("Choisissez un cours avant d'enregistrer.");
      return;
    }

    try {
      setPromptSaving(true);
      setPromptMessage("Enregistrement du prompt...");
      const updatedModule = await updateModulePrompt(selectedModule.id, systemPrompt);

      setModulesData((modules) =>
        modules.map((module) =>
          module.id === updatedModule.id
            ? { ...module, system_prompt: updatedModule.system_prompt }
            : module
        )
      );
      setPromptMessage("Prompt enregistré.");
    } catch (error) {
      setPromptMessage(
        error instanceof Error
          ? error.message
          : "Impossible d'enregistrer le prompt."
      );
    } finally {
      setPromptSaving(false);
    }
  };

  return (
    <div className="prof-dashboard-page">
      <header className="prof-topbar">
        <div>
          <p className="prof-eyebrow">Espace d'administration</p>
          <h1 className="prof-title">Tableau de bord enseignant</h1>
          <p className="prof-subtitle">
            Gérez les documents pédagogiques et le comportement de l'assistant
            pour chaque cours.
          </p>
        </div>

        <div className="prof-topbar-actions">
          <div className="prof-user-badge">
            <div className="prof-user-avatar">{initial}</div>
            <div>
              <p className="prof-user-name">{user.prenom}</p>
              <p className="prof-user-role">{user.role}</p>
            </div>
          </div>

          <button
            type="button"
            className="prof-secondary-button"
            onClick={handleBackToMainWorkspace}
          >
            Retour a l'espace principal
          </button>

          <button
            type="button"
            className="prof-ghost-button"
            onClick={handleLogout}
          >
            Se deconnecter
          </button>
        </div>
      </header>

      <main className="prof-content">
        <div
          className="prof-tabs"
          role="tablist"
          aria-label="Onglets du tableau de bord enseignant"
        >
          <button
            type="button"
            className={`prof-tab ${activeTab === "documents" ? "active" : ""}`}
            onClick={() => setActiveTab("documents")}
          >
            Documents
          </button>
          <button
            type="button"
            className={`prof-tab ${activeTab === "prompt" ? "active" : ""}`}
            onClick={() => setActiveTab("prompt")}
          >
            Prompt système
          </button>
        </div>

        {activeTab === "documents" ? (
          <section className="prof-panel-stack">
            <section className="prof-panel">
              <div className="prof-panel-header">
                <div>
                  <p className="prof-section-kicker">Import</p>
                  <h2>Ajouter un document</h2>
                </div>
              </div>

              <form
                className="prof-upload-grid"
                onSubmit={handleUploadDocument}
              >
                <label className="prof-field">
                  <span>Cours</span>
                  <select
                    value={selectedCourse}
                    onChange={(event) => setSelectedCourse(event.target.value)}
                  >
                    {courses.length === 0 ? (
                      <option value="">Aucun cours disponible</option>
                    ) : null}
                    {courses.map((course) => (
                      <option key={course} value={course}>
                        {course}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="prof-field">
                  <span>Nom du document</span>
                  <input
                    type="text"
                    placeholder="ex. TP réseaux"
                    value={customCourse}
                    onChange={(event) => setCustomCourse(event.target.value)}
                  />
                </label>

                <label className="prof-field">
                  <span>Document du cours</span>
                  <input
                    key={selectedFile?.name || "empty-file"}
                    type="file"
                    accept=".pdf,.doc,.docx,.ppt,.pptx,.mp3,.mp4"
                    onChange={(event) =>
                      setSelectedFile(event.target.files?.[0] || null)
                    }
                  />
                </label>

                <div className="prof-upload-actions">
                  <button
                    type="submit"
                    className="prof-primary-button"
                    disabled={!canUpload}
                  >
                    {uploading
                      ? "Import en cours..."
                      : "Importer et indexer le document"}
                  </button>
                  <p className="prof-upload-hint">
                    {uploadMessage ||
                    modulesError ||
                    (selectedFile
                      ? `${documentTitle} sélectionné pour ${selectedCourse}.`
                      : "Choisissez un cours et un fichier.")}
                  </p>
                </div>
              </form>
            </section>

            <section className="prof-panel">
              <div className="prof-panel-header prof-panel-header-spread">
                <h2>Documents importés</h2>
                <span className="prof-counter">
                  {uploadedDocuments.length} document
                  {uploadedDocuments.length > 1 ? "s" : ""}
                </span>
              </div>

              {documentsLoading ? (
                <div className="prof-empty-state">
                  <p className="prof-empty-title">Chargement des documents...</p>
                </div>
              ) : documentsError ? (
                <div className="prof-empty-state">
                  <p className="prof-empty-title">{documentsError}</p>
                </div>
              ) : uploadedDocuments.length > 0 ? (
                <div className="prof-documents-list">
                  {uploadedDocuments.map((document) => (
                    <div key={document.id} className="prof-document-card">
                      <div>
                        <p className="prof-empty-title">{document.title}</p>
                        <p className="prof-empty-copy">{document.status}</p>
                      </div>
                      <button
                        type="button"
                        className="prof-delete-document-button"
                        onClick={() => handleDeleteDocument(document.id)}
                        aria-label={`Supprimer ${document.title}`}
                      >
                        <img src="/delete.png" alt="" className="prof-delete-document-icon" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="prof-empty-state">
                  <p className="prof-empty-title">Aucun document importé</p>
                  <p className="prof-empty-copy">
                    Aucun document n'est associé au cours {selectedCourse}.
                  </p>
                </div>
              )}
            </section>
          </section>
        ) : null}

        {activeTab === "prompt" ? (
          <section className="prof-panel">
            <div className="prof-panel-header prof-panel-header-spread">
              <div>
                <p className="prof-section-kicker">Configuration</p>
                <h2>Prompt système de l'assistant</h2>
              </div>
              <span className="prof-save-indicator">
                {promptMessage || "Module actuel"}
              </span>
            </div>

            <label className="prof-field">
              <span>Cours</span>
              <select
                value={selectedCourse}
                onChange={(event) => setSelectedCourse(event.target.value)}
              >
                {courses.length === 0 ? (
                  <option value="">Aucun cours disponible</option>
                ) : null}
                {courses.map((course) => (
                  <option key={course} value={course}>
                    {course}
                  </option>
                ))}
              </select>
            </label>

            <label className="prof-field">
              <span>Instructions globales du prompt</span>
              <textarea
                className="prof-prompt-editor"
                value={systemPrompt}
                onChange={(event) => setSystemPrompt(event.target.value)}
              />
            </label>

            <div className="prof-inline-actions">
              <button
                type="button"
                className="prof-primary-button"
                disabled={!selectedModule || promptSaving}
                onClick={handleSaveSystemPrompt}
              >
                {promptSaving ? "Enregistrement..." : "Enregistrer le prompt système"}
              </button>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}
