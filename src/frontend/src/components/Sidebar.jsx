import "../styles/Sidebar.css";

export default function Sidebar({
  sidebarOpen,
  selectedModule,
  expandedModuleId,
  modules,
  onToggleSidebar,
  onSelectModule,
  onToggleModule,
  onLogout,
}) {
  return (
    <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
      <div className="sidebar-top">
        <div className="sidebar-logo">
          <img
            src="/logoApUp.png"
            alt="Logo AP-UP"
            className="sidebar-logo-img"
          />
        </div>

        <button className="sidebar-toggle" onClick={onToggleSidebar}>
          ☰
        </button>
      </div>

      {sidebarOpen && (
        <>
          <div className="sidebar-content">
            <h2 className="sidebar-title">Cours</h2>

            {modules.map((module) => {
              const isExpanded = expandedModuleId === module.id;
              const isSelected = selectedModule.id === module.id;

              return (
                <div
                  key={module.id}
                  className={`course-section ${isSelected ? "active" : ""}`}
                >
                  <div className="course-header">
                    <button
                      className="course-name-button"
                      onClick={() => onSelectModule(module)}
                    >
                      {module.name}
                    </button>

                    <button
                      className="expand-button"
                      onClick={() => onToggleModule(module.id)}
                    >
                      {isExpanded ? "▴" : "▸"}
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="course-files">
                      {module.files.length > 0 ? (
                        module.files.map((file, index) => <p key={index}>{file}</p>)
                      ) : (
                        <p className="course-placeholder">Aucun document</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="sidebar-bottom">
            <button className="logout-button" onClick={onLogout}>
              Se déconnecter
            </button>
          </div>
        </>
      )}
    </aside>
  );
}
