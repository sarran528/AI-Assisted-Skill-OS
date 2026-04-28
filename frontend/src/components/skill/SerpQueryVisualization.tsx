/**
 * SERP Query Visualization — Neo-Brutalist Style
 *
 * Hard borders, pixel font labels, flat yellow/black shadows.
 * No blur, no gradients, no glassmorphism — only raw structure.
 */

export interface SerpQueryConfig {
  skill_name: string;
  isRunning?: boolean;
}

const QUERIES = [
  { id: "roadmap",        label: "PATH",      query: "complete learning roadmap",     icon: "🗺" },
  { id: "prerequisites",  label: "PRE-REQS",  query: "prerequisites beginner",         icon: "🏗" },
  { id: "mistakes",       label: "MISTAKES",  query: "common mistakes learners make",  icon: "⚠" },
  { id: "duration",       label: "TIME",      query: "how long to learn",              icon: "⏱" },
  { id: "resources",      label: "LEARN",     query: "best resources tutorials",        icon: "📚" },
  { id: "jobs",           label: "MARKET",    query: "job requirements professional",   icon: "💼" },
];

export function SerpQueryVisualization({ skill_name, isRunning = false }: SerpQueryConfig) {
  return (
    <div style={{
      border: "3px solid var(--border)",
      boxShadow: "6px 6px 0 var(--shadow)",
      background: "#fff",
      marginTop: "20px",
    }}>
      {/* Header bar — mimics the top-bar style */}
      <div style={{
        background: "var(--color-tertiary)",
        borderBottom: "3px solid var(--border)",
        padding: "8px 12px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <span style={{
          fontFamily: "var(--font-primary)",
          fontSize: "9px",
          color: "#fff",
          letterSpacing: "0.1em",
        }}>
          SERP ENGINE — 6 PARALLEL THREADS
        </span>
        <span style={{
          fontFamily: "var(--font-primary)",
          fontSize: "8px",
          color: isRunning ? "var(--color-primary)" : "#aaa",
          animation: isRunning ? "blink 1s step-end infinite" : "none",
        }}>
          {isRunning ? "● LIVE" : "○ IDLE"}
        </span>
      </div>

      {/* Query grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        borderBottom: "3px solid var(--border)",
      }}>
        {QUERIES.map((q, idx) => (
          <div
            key={q.id}
            style={{
              padding: "10px",
              borderRight: idx % 3 !== 2 ? "2px solid var(--border)" : "none",
              borderBottom: idx < 3 ? "2px solid var(--border)" : "none",
              background: isRunning
                ? idx % 2 === 0 ? "var(--accent-yellow)" : "#fff"
                : "#fff",
              transition: "background 0.4s",
              animation: isRunning ? `brutePulse 1.6s ease-in-out ${idx * 0.25}s infinite` : "none",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
              <span style={{ fontSize: "13px" }}>{q.icon}</span>
              <span style={{
                fontFamily: "var(--font-primary)",
                fontSize: "7px",
                color: "var(--foreground)",
                letterSpacing: "0.05em",
              }}>
                {q.label}
              </span>
            </div>
            <div style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: "8px",
              color: "#444",
              borderLeft: "2px solid var(--border)",
              paddingLeft: "6px",
              wordBreak: "break-word",
              lineHeight: "1.4",
            }}>
              $ "{skill_name}" {q.query}
            </div>
          </div>
        ))}
      </div>

      {/* Status footer */}
      <div style={{
        padding: "8px 12px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: "var(--muted)",
      }}>
        <span style={{ fontFamily: "var(--font-primary)", fontSize: "7px", color: "#666" }}>
          AGGREGATE → DEDUP → LLM CONTEXT
        </span>
        <span style={{
          fontFamily: "var(--font-primary)",
          fontSize: "7px",
          background: isRunning ? "var(--color-primary)" : "var(--muted)",
          border: "2px solid var(--border)",
          padding: "2px 6px",
          color: isRunning ? "var(--foreground)" : "#999",
          boxShadow: isRunning ? "2px 2px 0 var(--shadow)" : "none",
          transition: "all 0.3s",
        }}>
          {isRunning ? "RUNNING" : "STANDBY"}
        </span>
      </div>

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes brutePulse {
          0%, 100% { box-shadow: none; }
          50% { box-shadow: inset 0 0 0 2px var(--color-primary); }
        }
      `}</style>
    </div>
  );
}
