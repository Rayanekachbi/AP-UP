import { useEffect, useState } from "react";
import { getChatHistory, sendChatMessage } from "../services/chatService";
import "../styles/ChatSection.css";

export default function ChatSection({
  user,
  selectedModule,
  question,
  setQuestion,
  role,
}) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  function createMessage({ id, sender, text }) {
    return {
      id,
      sender,
      text,
      moduleName: selectedModule.nom,
      role,
    };
  }

  useEffect(() => {
    let ignore = false;

    async function loadHistory() {
      if (!user?.id || !selectedModule?.id) {
        return;
      }

      setHistoryLoading(true);

      try {
        const history = await getChatHistory({
          utilisateurId: user.id,
          moduleId: selectedModule.id,
        });

        if (ignore) {
          return;
        }

        const historyMessages = history.flatMap((entry) => {
          return [
            createMessage({
              id: `history-${entry.id}-user`,
              sender: "user",
              text: entry.question,
            }),
            createMessage({
              id: `history-${entry.id}-assistant`,
              sender: "assistant",
              text: entry.reponse,
            }),
          ];
        });

        setMessages(historyMessages);
      } catch {
      } finally {
        if (!ignore) {
          setHistoryLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      ignore = true;
    };
  }, [role, selectedModule.id, selectedModule.nom, user?.id]);

  const handleSend = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading || historyLoading) {
      return;
    }

    const messageTimestamp = Date.now();
    const moduleId = String(selectedModule.id);
    const userMessage = createMessage({
      id: `${moduleId}-${messageTimestamp}-user`,
      sender: "user",
      text: trimmedQuestion,
    });

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await sendChatMessage({
        utilisateurId: user.id,
        moduleId: selectedModule.id,
        question: trimmedQuestion,
      });

      setMessages((currentMessages) => [
        ...currentMessages,
        createMessage({
          id: `${moduleId}-${messageTimestamp}-assistant`,
          sender: "assistant",
          text: response.reponse,
        }),
      ]);
    } catch (error) {
      setMessages((currentMessages) => [
        ...currentMessages,
        createMessage({
          id: `${moduleId}-${messageTimestamp}-error`,
          sender: "assistant",
          text:
            error instanceof Error
              ? error.message
              : "Impossible d'obtenir une réponse.",
        }),
      ]);
    } finally {
      setLoading(false);
    }
  };

  const hasMessages = messages.length > 0;
  const showLoadingState = loading || historyLoading;
  const canSend = !showLoadingState && question.trim().length > 0;

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
              aria-busy={showLoadingState}
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

          {showLoadingState ? (
            <p className="chat-status pending">
              {historyLoading ? "Chargement de l'historique..." : "Réponse en cours..."}
            </p>
          ) : null}
        </div>
      ) : (
        <div className="chat-active-state">
          <div className="chat-messages">
            <div className="chat-messages-inner">
              {messages.map((message) => (
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
            </div>
          </div>

          <div className="question-box chat-bottom-input">
            <input
              type="text"
              placeholder="Poser une question"
              className="question-input"
              value={question}
              aria-busy={showLoadingState}
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

          {showLoadingState ? (
            <p className="chat-status pending">
              {historyLoading ? "Chargement de l'historique..." : "Réponse en cours..."}
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
