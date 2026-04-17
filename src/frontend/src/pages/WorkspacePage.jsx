import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import ProfileMenu from "../components/ProfileMenu";
import ChatSection from "../components/ChatSection";
import { ROUTES } from "../routes/paths";
import { getModules } from "../services/moduleService";
import { getAuthenticatedUser } from "../services/authService";
import "../styles/MainWorkspace.css";

export default function WorkspacePage({ user, onLogout }) {
  const navigate = useNavigate();
  
  // Déclaration des nouveaux états pour les données de l'API
  const [modulesData, setModulesData] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [expandedModuleId, setExpandedModuleId] = useState(null);
  
  // Les autres états de ton interface
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [question, setQuestion] = useState("");
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const profileMenuRef = useRef(null);

  // nouveau useEffect pour charger les modules au démarrage
  useEffect(() => {
    getModules().then((data) => {
      // Adapter nom → name pour la Sidebar
      const adapted = data.map((m) => ({ 
        ...m, 
        name: m.nom, 
        files: [], 
        suggestions: [] 
      }));
      
      setModulesData(adapted);
      
      // Sélectionner le premier module par défaut s'il y en a
      if (adapted.length > 0) {
        setSelectedModule(adapted[0]);
        setExpandedModuleId(adapted[0].id);
      }
    }).catch(err => console.error("Erreur de chargement des modules:", err));
  }, []);

  // Gestion du clic en dehors du menu profil
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

  const handleSuggestionClick = (suggestion) => {
    setQuestion(suggestion);
  };

  const handleToggleProfileMenu = () => {
    setProfileMenuOpen((prev) => !prev);
  };

  const handleViewProfile = () => {
    alert("Le profil sera connecté au backend lors de l'intégration.");
    setProfileMenuOpen(false);
  };

  const handleOpenProfessorAdminPanel = () => {
    setProfileMenuOpen(false);
    navigate(ROUTES.professorAdmin);
  };

  const handleLogout = () => {
    setProfileMenuOpen(false);
    onLogout();
    navigate(ROUTES.login, { replace: true });
  };

  // Tant que l'API n'a pas répondu, on n'affiche rien (ou on pourrait mettre un loader)
  if (!selectedModule) {
    return <div className="dashboard-page">Chargement des modules...</div>;
  }

  return (
    <div className="dashboard-page">
      <Sidebar
        sidebarOpen={sidebarOpen}
        selectedModule={selectedModule}
        expandedModuleId={expandedModuleId}
        modules={modulesData}
        onToggleSidebar={handleToggleSidebar}
        onSelectModule={handleSelectModule}
        onToggleModule={handleToggleModule}
        onLogout={handleLogout}
      />

      <main className="dashboard-main">
        <header className="topbar">
          <div className="topbar-left"></div>
          <h1 className="topbar-title">Cours: {selectedModule.name}</h1>

          <ProfileMenu
            user={user}
            profileMenuOpen={profileMenuOpen}
            profileMenuRef={profileMenuRef}
            onToggleProfileMenu={handleToggleProfileMenu}
            onViewProfile={handleViewProfile}
            onOpenProfessorAdminPanel={handleOpenProfessorAdminPanel}
            onLogout={handleLogout}
          />
        </header>

        <ChatSection 
          selectedModule={selectedModule} 
          question={question} 
          setQuestion={setQuestion} 
          onSuggestionClick={handleSuggestionClick} 
          role={user?.role} /* <-- J'ai corrigé userRole ici */
          user={user} 
        />
      </main>
    </div>
  );
}