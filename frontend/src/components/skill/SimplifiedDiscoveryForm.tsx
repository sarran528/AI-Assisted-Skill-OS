import { useState } from "react";
import { BrutalButton } from "../brutal/BrutalButton";

interface SimplifiedDiscoveryFormProps {
  onSubmit: (skillName: string) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

export function SimplifiedDiscoveryForm({
  onSubmit,
  isLoading = false,
  error = null,
}: SimplifiedDiscoveryFormProps) {
  const [skillName, setSkillName] = useState("");

  const handleSubmit = async () => {
    if (!skillName.trim()) return;
    await onSubmit(skillName.trim());
    if (!error) {
      setSkillName("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading && skillName.trim()) {
      handleSubmit();
    }
  };

  return (
    <section className="search-hero">
      <h1 className="headline" style={{ fontSize: "2.3rem" }}>What will you master?</h1>
      <p className="mono-caps" style={{ marginTop: "12px", fontSize: "11px" }}>
        Enter any skill to discover or generate a roadmap
      </p>

      <div className="search-input-wrapper">
        <input
          type="text"
          className="premium-input"
          placeholder="e.g. Public Speaking"
          value={skillName}
          onChange={(e) => setSkillName(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={isLoading}
        />
      </div>

      <div style={{ marginTop: "16px" }}>
        <BrutalButton
          variant="mono"
          onClick={handleSubmit}
          disabled={isLoading || !skillName.trim()}
          style={{
            minWidth: "220px",
            opacity: isLoading || !skillName.trim() ? 0.65 : 1,
          }}
        >
          {isLoading ? "DISCOVERING..." : "DISCOVER SKILL"}
        </BrutalButton>
      </div>

      {error && (
        <div
          style={{
            marginTop: "14px",
            background: "var(--accent-red)",
            border: "2px solid var(--border)",
            color: "var(--foreground)",
            padding: "10px 12px",
            fontFamily: "var(--font-secondary)",
            fontSize: "12px",
            boxShadow: "2px 2px 0 var(--shadow)",
          }}
        >
          {error}
        </div>
      )}
    </section>
  );
}
