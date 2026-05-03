import "../styles/ProfileMenu.css";
import { canAccessProfessorDashboard } from "../services/authService";

export default function ProfileMenu({
  user,
  profileMenuOpen,
  profileMenuRef,
  onToggleProfileMenu,
  onOpenProfessorAdminPanel,
  onLogout,
}) {
  const canOpenProfessorDashboard = canAccessProfessorDashboard(user);
  const fullName = `${user.prenom} ${user.nom}`;
  const initial = user.prenom?.charAt(0) || user.email.charAt(0);

  return (
    <div className="topbar-right" ref={profileMenuRef}>


      <button
        type="button"
        className="profile-button"
        onClick={onToggleProfileMenu}
        aria-haspopup="menu"
        aria-expanded={profileMenuOpen}
        aria-label="Ouvrir le menu du profil"
      >
        <div className="profile-circle">{initial}</div>
      </button>

      {profileMenuOpen && (
        <div className="profile-menu" role="menu">
          <div className="profile-menu-header">
            <div className="profile-menu-avatar">{initial}</div>
            <div>
              <p className="profile-menu-name">{fullName}</p>
              <p className="profile-menu-email">{user.email}</p>
              <p className="profile-menu-role">{user.role}</p>
            </div>
          </div>

          {canOpenProfessorDashboard ? (
            <button
              type="button"
              className="profile-menu-item profile-menu-item-admin"
              onClick={onOpenProfessorAdminPanel}
              role="menuitem"
            >
              Administration professeur
            </button>
          ) : null}

          <button
            type="button"
            className="profile-menu-item profile-menu-item-logout"
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
