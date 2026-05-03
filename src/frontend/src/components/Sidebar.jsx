import "../styles/Sidebar.css";

export default function Sidebar({
  sidebarOpen,
  selectedModule,
  expandedModuleId,
  modules,
  documents = [],
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
              const moduleDocuments = documents.filter(
                (document) => document.course === module.nom
              );

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
                      {module.nom}
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
                      {moduleDocuments.length > 0 ? (
                        moduleDocuments.map((document) => (
                          <p key={document.id}>{document.title}</p>
                        ))
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
