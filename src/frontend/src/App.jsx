import { useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import ProfessorAdminPage from "./pages/ProfessorAdminPage";
import WorkspacePage from "./pages/WorkspacePage";
import { ROUTES } from "./routes/paths";
import {
  canAccessProfessorDashboard,
  clearAuthenticatedUser,
  getAuthenticatedUser,
  loginUser,
} from "./services/authService";

function RequireAuth({ user, children }) {
  const location = useLocation();

  if (!user) {
    return <Navigate to={ROUTES.login} replace state={{ from: location }} />;
  }

  return children;
}

function RequireProfessor({ user, children }) {
  if (!canAccessProfessorDashboard(user)) {
    return <Navigate to={ROUTES.workspace} replace />;
  }

  return children;
}

export default function App() {
  const [user, setUser] = useState(() => getAuthenticatedUser());

  const handleLogin = async (credentials) => {
    const authenticatedUser = await loginUser(credentials);
    setUser(authenticatedUser);
    return authenticatedUser;
  };

  const handleLogout = () => {
    clearAuthenticatedUser();
    setUser(null);
  };

  return (
    <Routes>
      <Route path="/" element={<Navigate to={ROUTES.workspace} replace />} />
      <Route
        path={ROUTES.login}
        element={
          <LoginPage
            isAuthenticated={Boolean(user)}
            onLogin={handleLogin}
          />
        }
      />

      <Route
        path={ROUTES.workspace}
        element={
          <RequireAuth user={user}>
            <WorkspacePage user={user} onLogout={handleLogout} />
          </RequireAuth>
        }
      />

      <Route
        path={ROUTES.professorAdmin}
        element={
          <RequireAuth user={user}>
            <RequireProfessor user={user}>
              <ProfessorAdminPage user={user} onLogout={handleLogout} />
            </RequireProfessor>
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to={ROUTES.workspace} replace />} />
    </Routes>
  );
}
