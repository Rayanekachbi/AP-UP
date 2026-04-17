// src/frontend/src/components/ChatSection.jsx
import { useMemo, useState } from "react";
import {
  CHAT_CONNECTION_LABEL,
  sendMessage, // <-- Nouvel import
} from "../services/chatService";
import "../styles/ChatSection.css";

export default function ChatSection({
  selectedModule,
  question,
  setQuestion,
  onSuggestionClick,
  role,
  user, // <-- Ajout de 'user' dans les props pour avoir son ID
}) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false); // <-- Véritable état de chargement

  const moduleMessages = useMemo(() => {
    return messages.filter((message) => {
      return String(message.moduleId) === String(selectedModule.id);
    });
  }, [messages, selectedModule.id]);

  const handleSend = async () => {
    const trimmedQuestion = question.trim();
    
    if (!trimmedQuestion || loading) {
      return;
    }

    const moduleId = String(selectedModule.id);
    const timestamp = Date.now();

    // Ajouter le message utilisateur immédiatement
    setMessages((prev) => [
      ...prev,
      {
        id: `${moduleId}-${timestamp}-user`,
        sender: "user",
        text: trimmedQuestion,
        moduleId,
        moduleName: selectedModule.name,
        role,
      },
    ]);
    
    setQuestion("");
    setLoading(true);

    // Interroger l'API Backend
    try {
      const data = await sendMessage({
        utilisateur_id: user.id, // Nécessite que 'user' soit passé en prop
        module_id: selectedModule.id,
        question: trimmedQuestion,
      });

      // Ajouter la réponse de l'assistant
      setMessages((prev) => [
        ...prev,
        {
          id: `${moduleId}-${timestamp}-assistant`,
          sender: "assistant",
          text: data.reponse,
          moduleId,
          moduleName: selectedModule.name,
        },
      ]);
    } catch (err) {
      // Gérer l'erreur proprement
      setMessages((prev) => [
        ...prev,
        {
          id: `${moduleId}-${timestamp}-error`,
          sender: "assistant",
          text: "Une erreur est survenue. Veuillez réessayer.",
          moduleId,
          moduleName: selectedModule.name,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const hasMessages = moduleMessages.length > 0;
  const hasSuggestions = selectedModule.suggestions && selectedModule.suggestions.length > 0;
  const canSend = !loading; 

  return (
    <section className="chat-section">
      {!hasMessages ? (
        <div className="chat-empty-state">
          <p className="chat-subtitle">
            Posez une question pour
            <br />
            commencer
          </p>

          <div className="question-box">
            <input
              type="text"
              placeholder="Poser une question"
              className="question-input"
              value={question}
              disabled={loading}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />
            <button
              className="send-button"
              onClick={handleSend}
              disabled={!canSend}
            >
              ➤
            </button>
          </div>

          <p className={`chat-status ${canSend ? "ready" : "pending"}`}>
            {loading ? "Connexion au modèle..." : CHAT_CONNECTION_LABEL}
          </p>

          {hasSuggestions ? (
            <div className="suggestions">
              {selectedModule.suggestions.map((suggestion, index) => (
                <p key={index} onClick={() => onSuggestionClick(suggestion)}>
                  {suggestion}
                </p>
              ))}
            </div>
          ) : (
            <p className="chat-empty-note">
              Aucune suggestion disponible.
            </p>
          )}
        </div>
      ) : (
        <div className="chat-active-state">
          <div className="chat-messages">
            <div className="chat-messages-inner">
              {moduleMessages.map((message) => (
                <div
                  key={message.id}
                  className={`message-row ${
                    message.sender === "user" ? "user" : "assistant"
                  }`}
                >
                  <div className="message-stack">
                    <div
                      className={`message-bubble ${
                        message.sender === "user" ? "user" : "assistant"
                      }`}
                    >
                      {message.text}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message-row assistant">
                  <div className="message-stack">
                    <div className="message-bubble assistant typing-indicator">
                      ...
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="question-box chat-bottom-input">
            <input
              type="text"
              placeholder="Poser une question"
              className="question-input"
              value={question}
              disabled={loading}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
            />
            <button
              className="send-button"
              onClick={handleSend}
              disabled={!canSend}
            >
              ➤
            </button>
          </div>

          <p className={`chat-status ${canSend ? "ready" : "pending"}`}>
            {loading ? "Génération en cours..." : CHAT_CONNECTION_LABEL}
          </p>
        </div>
      )}
    </section>
  );
}