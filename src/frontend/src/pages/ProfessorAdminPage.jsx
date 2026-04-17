import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../routes/paths";
import { getModules } from "../services/moduleService";
import { getProfessorDashboardData } from "../services/professorDashboardService";
import { buildApiUrl } from "../services/apiClient"; // <-- Nouvel import
import "../styles/ProfessorAdminPanel.css";

// On garde le mock uniquement pour les documents affichés et le prompt pour le moment
const professorDashboardData = getProfessorDashboardData();

export default function ProfessorAdminPage({ user, onLogout }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("documents");
  
  // Nouveaux états pour gérer les vraies données de l'API
  const [modulesData, setModulesData] = useState([]);
  const [selectedModuleId, setSelectedModuleId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false); // <-- État de chargement

  const [systemPrompt, setSystemPrompt] = useState(
    professorDashboardData.systemPromptTemplate
  );

  // Charger les modules au démarrage
  useEffect(() => {
    getModules().then((data) => {
      setModulesData(data);
      if (data.length > 0) {
        setSelectedModuleId(data[0].id); // Sélectionner le premier module par défaut
      }
    }).catch(err => console.error("Erreur de chargement des modules:", err));
  }, []);

  const uploadedDocuments = professorDashboardData.uploadedDocuments;

  const handleBackToMainWorkspace = () => {
    navigate(ROUTES.workspace);
  };

  const handleLogout = () => {
    onLogout();
    navigate(ROUTES.login, { replace: true });
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || !selectedModuleId) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("module_id", selectedModuleId);
      formData.append("enseignant_id", user.id);

      const response = await fetch(buildApiUrl("/ingestion/documents/upload"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Erreur lors de l'envoi du document");
      }

      // Gérer la réponse (succès)
      alert("Document importé et indexé avec succès !");
      setSelectedFile(null); // Réinitialiser le fichier
      
      // Ici on pourrait plus tard rafraîchir la liste des documents
    } catch (error) {
      console.error(error);
      alert("Une erreur est survenue lors de l'importation.");
    } finally {
      setUploading(false);
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
            <div className="prof-user-avatar">{user?.name?.charAt(0) || "P"}</div>
            <div>
              <p className="prof-user-name">{user?.name}</p>
              <p className="prof-user-role">{user?.role}</p>
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

              {/* Formulaire lié à handleUpload */}
              <form className="prof-upload-grid" onSubmit={handleUpload}>
                <label className="prof-field">
                  <span>Cours (Module)</span>
                  <select
                    value={selectedModuleId}
                    onChange={(event) => setSelectedModuleId(event.target.value)}
                    disabled={uploading}
                  >
                    {modulesData.map((module) => (
                      <option key={module.id} value={module.id}>
                        {module.nom || module.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="prof-field">
                  <span>Document du cours</span>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.ppt,.pptx"
                    disabled={uploading}
                    onChange={(event) => {
                      setSelectedFile(event.target.files?.[0] || null);
                      // Reset l'input value si on annule
                      if (!event.target.files?.[0]) event.target.value = "";
                    }}
                  />
                </label>

                <div className="prof-upload-actions">
                  <button 
                    type="submit" 
                    className="prof-primary-button" 
                    disabled={!selectedFile || !selectedModuleId || uploading}
                  >
                    {uploading ? "Importation en cours..." : "Importer et indexer le document"}
                  </button>
                  <p className="prof-upload-hint">
                    {selectedFile
                      ? `${selectedFile.name} sélectionné.`
                      : "Choisissez un cours et un fichier."}
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

              {uploadedDocuments.length > 0 ? (
                <div className="prof-documents-list">
                  {uploadedDocuments.map((document) => (
                    <div key={document.id} className="prof-document-card">
                      <p className="prof-empty-title">{document.name}</p>
                      <p className="prof-empty-copy">{document.course}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="prof-empty-state">
                  <p className="prof-empty-title">
                    {professorDashboardData.emptyDocumentsMessage.title}
                  </p>
                  <p className="prof-empty-copy">
                    {professorDashboardData.emptyDocumentsMessage.description}
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
              <span className="prof-save-indicator">Non enregistré</span>
            </div>

            <label className="prof-field">
              <span>Instructions globales du prompt</span>
              <textarea
                className="prof-prompt-editor"
                value={systemPrompt}
                onChange={(event) => setSystemPrompt(event.target.value)}
              />
            </label>

            <div className="prof-inline-actions">
              <button type="button" className="prof-primary-button" disabled>
                Enregistrer le prompt système
              </button>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}