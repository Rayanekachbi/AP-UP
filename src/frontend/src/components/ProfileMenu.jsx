import "../styles/ProfileMenu.css";
import { canAccessProfessorDashboard } from "../services/authService";

export default function ProfileMenu({
  user,
  profileMenuOpen,
  profileMenuRef,
  onToggleProfileMenu,
  onViewProfile,
  onOpenProfessorAdminPanel,
  onLogout,
}) {
  const canOpenProfessorDashboard = canAccessProfessorDashboard(user);

  return (
    <div className="topbar-right" ref={profileMenuRef}>
      <button className="icon-button">◔</button>

      <button
        type="button"
        className="profile-button"
        onClick={onToggleProfileMenu}
        aria-haspopup="menu"
        aria-expanded={profileMenuOpen}
        aria-label="Ouvrir le menu du profil"
      >
        <div className="profile-circle">{user.name.charAt(0)}</div>
      </button>

      {profileMenuOpen && (
        <div className="profile-menu" role="menu">
          <div className="profile-menu-header">
            <div className="profile-menu-avatar">{user.name.charAt(0)}</div>
            <div>
              <p className="profile-menu-name">{user.name}</p>
              <p className="profile-menu-email">{user.email}</p>
              <p className="profile-menu-role">{user.role}</p>
            </div>
          </div>

          <button
            type="button"
            className="profile-menu-item"
            onClick={onViewProfile}
            role="menuitem"
          >
            Voir le profil
          </button>

          {canOpenProfessorDashboard ? (
            <button
              type="button"
              className="profile-menu-item profile-menu-item-accent"
              onClick={onOpenProfessorAdminPanel}
              role="menuitem"
            >
              Administration professeur
            </button>
          ) : null}

          <button
            type="button"
            className="profile-menu-item profile-menu-item-danger"
            onClick={onLogout}
            role="menuitem"
          >
            Se déconnecter
          </button>
        </div>
      )}
    </div>
  );
}
