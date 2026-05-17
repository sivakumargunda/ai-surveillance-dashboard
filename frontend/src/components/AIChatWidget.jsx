import { useEffect, useRef, useState } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

const SUGGESTED_PROMPTS = [
  "Summarize today's alerts",
  "Which camera has highest activity?",
  "Show most active zone",
  "Explain recent anomalies",
  "Generate incident report",
  "Current threat level?",
];

const INITIAL_MESSAGE = {
  role: "ai",
  text: "Hello! I'm your Sentinel AI Assistant.\nAsk me about alerts, cameras, incidents, or analytics.",
  time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
};

export default function AIChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [incidentSummary, setIncidentSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const getTime = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const sendMessage = async (text) => {
    const userMsg = text || input.trim();
    if (!userMsg) return;
    setInput("");
    const time = getTime();
    setMessages((prev) => [...prev, { role: "user", text: userMsg, time }]);
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.response, time: getTime() },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "Connection error. Is the backend running?", time, error: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const generateIncidentSummary = async () => {
    setSummaryLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/incident-summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          zone: "Warehouse Zone B",
          start_time: "7:00 PM",
          end_time: "9:00 PM",
        }),
      });
      const data = await res.json();
      setIncidentSummary(data.summary);
    } catch {
      setIncidentSummary("Failed to generate summary. Check backend connection.");
    } finally {
      setSummaryLoading(false);
    }
  };

  return (
    <>
      <button
        className="ai-chat-button"
        onClick={() => setOpen(!open)}
        title="AI Assistant"
        type="button"
      >
        {open ? "X" : "AI"}
      </button>

      {open && (
        <div className="ai-chat-panel">
          <div className="ai-chat-header">
            <div className="ai-avatar">AI</div>
            <div>
              <div className="ai-title">Sentinel AI Assistant</div>
              <div className="ai-status">
                <span />
                Online - gemini-1.5-flash
              </div>
            </div>
            <div className="ai-tabs">
              {["chat", "incident"].map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className={activeTab === tab ? "active" : ""}
                >
                  {tab === "chat" ? "Chat" : "Report"}
                </button>
              ))}
            </div>
          </div>

          {activeTab === "chat" && (
            <>
              <div className="ai-messages">
                {messages.map((msg, index) => (
                  <div className={`ai-message-row ${msg.role}`} key={`${msg.time}-${index}`}>
                    <div className={`ai-message ${msg.role} ${msg.error ? "error" : ""}`}>
                      {msg.text}
                      <div className="ai-message-time">{msg.time}</div>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="ai-typing">
                    {[0, 1, 2].map((item) => (
                      <span key={item} />
                    ))}
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              <div className="ai-prompts">
                {SUGGESTED_PROMPTS.slice(0, 3).map((prompt) => (
                  <button key={prompt} type="button" onClick={() => sendMessage(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>

              <div className="ai-input-row">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder="Ask about alerts, cameras, zones..."
                />
                <button
                  type="button"
                  onClick={() => sendMessage()}
                  disabled={loading || !input.trim()}
                >
                  Send
                </button>
              </div>
            </>
          )}

          {activeTab === "incident" && (
            <div className="ai-report-tab">
              <div className="ai-report-title">AI Incident Summary</div>
              <div className="ai-report-meta">
                <div>Zone: <span>Warehouse Zone B</span></div>
                <div>Period: <span>7:00 PM - 9:00 PM</span></div>
              </div>
              <button type="button" onClick={generateIncidentSummary} disabled={summaryLoading}>
                {summaryLoading ? "Generating..." : "Generate AI Report"}
              </button>
              {incidentSummary && <div className="ai-report-output">{incidentSummary}</div>}
            </div>
          )}
        </div>
      )}
    </>
  );
}
