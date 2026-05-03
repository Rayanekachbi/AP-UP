import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ROUTES } from "../routes/paths";
import "../styles/login.css";

export default function LoginPage({ isAuthenticated, onLogin }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isAuthenticated) {
    return <Navigate to={ROUTES.workspace} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) {
      setErrorMessage("Veuillez renseigner votre email et votre mot de passe.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage("");
      await onLogin({ email, password });
      navigate(location.state?.from?.pathname || ROUTES.workspace, {
        replace: true,
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Une erreur est survenue pendant la connexion."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-left">
        <div className="small-logo">
          <img src="/logoApUp.png" alt="logo" className="small-logo-img" />
        </div>

        <div className="login-box">
          <h1 className="title">
            Connectez-vous pour accéder à l'application
          </h1>

          <form onSubmit={handleSubmit}>
            <label>Adresse e-mail</label>
            <input
              type="email"
              placeholder="exemple@ap-up.fr"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <label>Mot de passe</label>
            <input
              type="password"
              placeholder="******"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {errorMessage ? (
              <p className="login-error">{errorMessage}</p>
            ) : null}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Connexion..." : "Se connecter"}
            </button>
          </form>
        </div>
      </div>

      <div className="login-right">
        <div className="big-logo">
          <img src="/logoApUp.png" alt="logo" className="big-logo-img" />
        </div>
      </div>
    </div>
  );
}
