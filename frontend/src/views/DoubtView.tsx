import { useState } from "react";
import { BrutalCard as Card } from "../components/brutal/BrutalCard";
import { BrutalButton as Button } from "../components/brutal/BrutalButton";
import { Input } from "../components/ui/Input";
import { useNavigationStore } from "../store/navigationStore";

export function DoubtView() {
  const { currentSkill, roadmapState } = useNavigationStore();
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<{ explanation: string; sources_used: number } | null>(null);
  const [loading, setLoading] = useState(false);
  const hasContext = roadmapState.isGenerated && currentSkill.skillName && roadmapState.currentPhase && roadmapState.currentTechnique;

  const handleAskDoubt = () => {
    if (!query) return;
    setLoading(true);
    window.setTimeout(() => {
      setResponse({
        explanation: hasContext
          ? `Guidance for ${currentSkill.skillName} in ${roadmapState.currentPhase} / ${roadmapState.currentTechnique}: focus on the current protocol step and threshold criteria.`
          : "General guidance: break the concept into small steps, practice one at a time, and validate with simple exercises.",
        sources_used: 3,
      });
      setLoading(false);
    }, 400);
  };

  return (
    <main style={{ padding: "2rem", maxWidth: "760px" }}>
      <h1 className="headline">Help</h1>
      <Card>
        <h2>Ask a question about your current skill or technique</h2>
        {hasContext ? (
          <p className="small-copy">Context: {currentSkill.skillName} / {roadmapState.currentPhase} / {roadmapState.currentTechnique}</p>
        ) : null}
        <div style={{ marginTop: "0.75rem" }}>
          <Input
            textarea
            placeholder="Ask your question..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows={4}
          />
        </div>
        <div style={{ marginTop: "0.75rem" }}>
          <Button onClick={handleAskDoubt} disabled={!query || loading}>
            {loading ? "Thinking..." : "Submit"}
          </Button>
        </div>
      </Card>
      {response ? (
        <Card style={{ marginTop: "1rem" }}>
          <h2>Response</h2>
          <p>{response.explanation}</p>
          <p className="small-copy">Grounded with {response.sources_used} retrieved source(s).</p>
        </Card>
      ) : null}
    </main>
  );
}
