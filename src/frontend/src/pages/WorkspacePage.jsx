import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import ProfileMenu from "../components/ProfileMenu";
import ChatSection from "../components/ChatSection";
import { ROUTES } from "../routes/paths";
import { getDefaultModule, getModules } from "../services/moduleService";
import "../styles/MainWorkspace.css";

const modulesData = getModules();
const defaultModule = getDefaultModule();

export default function WorkspacePage({ user, onLogout }) {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedModule, setSelectedModule] = useState(defaultModule);
  const [expandedModuleId, setExpandedModuleId] = useState(defaultModule?.id);
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
    alert("Le profil sera connecte au backend lors de l'integration.");
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

  if (!selectedModule) {
    return null;
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
          role={user?.role}
        />
      </main>
    </div>
  );
}
