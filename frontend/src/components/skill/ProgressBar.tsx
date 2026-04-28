interface ProgressBarProps {
  currentStage: "idle" | "discover" | "aggregate" | "llm" | "form" | "generate";
  isLoading?: boolean;
}

export function ProgressBar({ currentStage, isLoading = false }: ProgressBarProps) {
  const stages = ["discover", "aggregate", "llm", "form", "generate"];
  const stageLabels: Record<string, string> = {
    idle: "Ready",
    discover: "Searching...",
    aggregate: "Processing...",
    llm: "Analyzing...",
    form: "Questions",
    generate: "Generating roadmap...",
  };

  const currentIndex = stages.indexOf(currentStage);
  const progress = currentStage === "idle" ? 0 : ((currentIndex + 1) / stages.length) * 100;

  return (
    <div
      style={{
        border: "3px solid var(--border)",
        boxShadow: "4px 4px 0 var(--shadow)",
        padding: "16px",
        marginBottom: "16px",
        background: "#fff",
      }}
    >
      <div
        style={{
          height: "24px",
          background: "#f0f0f0",
          border: "2px solid var(--border)",
          marginBottom: "12px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            background: "var(--border)",
            width: `${progress}%`,
          }}
        />
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "var(--font-secondary)",
          fontSize: "13px",
        }}
      >
        <span style={{ color: "var(--foreground)", fontWeight: 600 }}>
          {isLoading ? stageLabels[currentStage] : "Ready"}
        </span>
        <span style={{ color: "#888" }}>
          {currentStage === "idle" ? "0" : currentIndex + 1} / {stages.length}
        </span>
      </div>
    </div>
  );
}
