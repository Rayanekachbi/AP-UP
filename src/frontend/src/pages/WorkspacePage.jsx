import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import ProfileMenu from "../components/ProfileMenu";
import ChatSection from "../components/ChatSection";
import { ROUTES } from "../routes/paths";
import { clearChatHistory } from "../services/chatService";
import { getModules } from "../services/moduleService";
import { getUploadedDocuments } from "../services/professorDashboardService";
import "../styles/MainWorkspace.css";

export default function WorkspacePage({ user, onLogout }) {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [modulesData, setModulesData] = useState([]);
  const [documentsData, setDocumentsData] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [expandedModuleId, setExpandedModuleId] = useState(null);
  const [modulesError, setModulesError] = useState("");
  const [modulesLoading, setModulesLoading] = useState(true);
  const [question, setQuestion] = useState("");
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const profileMenuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        profileMenuRef.current &&
        !profileMenuRef.current.contains(event.target)
      ) {
        setProfileMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    let ignore = false;

    async function loadDocuments() {
      try {
        const documents = await getUploadedDocuments();

        if (!ignore) {
          setDocumentsData(documents);
        }
      } catch {
        if (!ignore) {
          setDocumentsData([]);
        }
      }
    }

    loadDocuments();

    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;

    async function loadModules() {
      try {
        setModulesLoading(true);
        setModulesError("");
        const modules = await getModules();

        if (ignore) {
          return;
        }

        setModulesData(modules);
        setSelectedModule(modules[0] || null);
        setExpandedModuleId(modules[0]?.id || null);
      } catch (error) {
        if (!ignore) {
          setModulesError(
            error instanceof Error
              ? error.message
              : "Impossible de charger les cours."
          );
        }
      } finally {
        if (!ignore) {
          setModulesLoading(false);
        }
      }
    }

    loadModules();

    return () => {
      ignore = true;
    };
  }, []);

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  const handleSelectModule = (module) => {
    setSelectedModule(module);
    setExpandedModuleId(module.id);
    setQuestion("");
  };

  const handleToggleModule = (moduleId) => {
    setExpandedModuleId((prev) => (prev === moduleId ? null : moduleId));
  };

  const handleToggleProfileMenu = () => {
    setProfileMenuOpen((prev) => !prev);
  };

  const handleOpenProfessorAdminPanel = () => {
    setProfileMenuOpen(false);
    navigate(ROUTES.professorAdmin);
  };

  const handleLogout = async () => {
    setProfileMenuOpen(false);
    try {
      await clearChatHistory(user.id);
    } catch {
      // On deconnecte quand meme l'utilisateur meme si la suppression echoue.
    }
    onLogout();
    navigate(ROUTES.login, { replace: true });
  };

  if (modulesLoading) {
    return <div className="dashboard-page">Chargement des cours...</div>;
  }

  if (modulesError) {
    return <div className="dashboard-page">{modulesError}</div>;
  }

  if (!selectedModule) {
    return <div className="dashboard-page">Aucun cours disponible.</div>;
  }

  return (
    <div className="dashboard-page">
      <Sidebar
        sidebarOpen={sidebarOpen}
        selectedModule={selectedModule}
        expandedModuleId={expandedModuleId}
        modules={modulesData}
        documents={documentsData}
        onToggleSidebar={handleToggleSidebar}
        onSelectModule={handleSelectModule}
        onToggleModule={handleToggleModule}
        onLogout={handleLogout}
      />

      <main className="dashboard-main">
        <header className="topbar">
          <div className="topbar-left"></div>
          <h1 className="topbar-title">Cours: {selectedModule.nom}</h1>

          <ProfileMenu
            user={user}
            profileMenuOpen={profileMenuOpen}
            profileMenuRef={profileMenuRef}
            onToggleProfileMenu={handleToggleProfileMenu}
            onOpenProfessorAdminPanel={handleOpenProfessorAdminPanel}
            onLogout={handleLogout}
          />
        </header>

        <ChatSection
          user={user}
          selectedModule={selectedModule}
          question={question}
          setQuestion={setQuestion}
          role={user?.role}
        />
      </main>
    </div>
  );
}
