import { useMemo, useState } from "react";
import {
  CHAT_CONNECTION_LABEL,
  createMockAssistantAnswer,
} from "../services/chatService";
import "../styles/ChatSection.css";

export default function ChatSection({
  selectedModule,
  question,
  setQuestion,
  onSuggestionClick,
  role,
}) {
  const [messages, setMessages] = useState([]);

  const moduleMessages = useMemo(() => {
    return messages.filter((message) => {
      return String(message.moduleId) === String(selectedModule.id);
    });
  }, [messages, selectedModule.id]);

  const handleSend = () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    const messageTimestamp = Date.now();
    const moduleId = String(selectedModule.id);

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: `${moduleId}-${messageTimestamp}-user-${currentMessages.length}`,
        sender: "user",
        text: trimmedQuestion,
        moduleId,
        moduleName: selectedModule.name,
        role,
      },
        {
          id: `${moduleId}-${messageTimestamp}-assistant-${currentMessages.length}`,
          sender: "assistant",
          text: createMockAssistantAnswer(),
          moduleId,
          moduleName: selectedModule.name,
        },
    ]);

    setQuestion("");
  };

  const hasMessages = moduleMessages.length > 0;
  const hasSuggestions = selectedModule.suggestions.length > 0;
  const loading = false;
  const canSend = true;

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
              aria-busy={loading}
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
            {CHAT_CONNECTION_LABEL}
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
            </div>
          </div>

          <div className="question-box chat-bottom-input">
            <input
              type="text"
              placeholder="Poser une question"
              className="question-input"
              value={question}
              aria-busy={loading}
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
            {CHAT_CONNECTION_LABEL}
          </p>
        </div>
      )}
    </section>
  );
}
