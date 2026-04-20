import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useDoubt } from "../../hooks/useDoubt";
import { useResources } from "../../hooks/useResources";
import { useTip } from "../../hooks/useTip";
import { BrutalButton } from "./BrutalButton";
import { BrutalCard } from "./BrutalCard";
import { BrutalInput } from "./BrutalInput";
import { TipCard } from "./TipCard";

const doubtSchema = z.object({
  question: z.string().min(5, "Please enter at least 5 characters."),
});

type SupportTab = "doubt" | "resources" | "correction";

type DoubtForm = z.infer<typeof doubtSchema>;

interface SupportPanelProps {
  open: boolean;
  onClose: () => void;
  skillId: string;
  phase: string;
  techniqueId?: string;
  sessionId?: string;
  tipPending?: boolean;
}

export function SupportPanel({
  open,
  onClose,
  skillId,
  phase,
  techniqueId = "default-technique",
  sessionId,
  tipPending = false,
}: SupportPanelProps) {
  const [tab, setTab] = useState<SupportTab>(tipPending ? "correction" : "doubt");
  const [resourceQuery, setResourceQuery] = useState("");

  const doubtMutation = useDoubt();
  const resourcesQuery = useResources(skillId, phase, resourceQuery || undefined);
  const tipQuery = useTip(sessionId ?? null, tipPending || tab === "correction");

  const { register, handleSubmit, formState, reset } = useForm<DoubtForm>({
    resolver: zodResolver(doubtSchema),
    defaultValues: { question: "" },
  });
  const questionField = register("question");

  useEffect(() => {
    if (tipPending) {
      setTab("correction");
    }
  }, [tipPending]);

  if (!open) {
    return null;
  }

  return (
    <aside className="support-panel" data-testid="support-panel">
      <div className="support-panel__header">
        <h3>Need Support?</h3>
        <BrutalButton onClick={onClose} data-testid="support-close-btn">
          Close
        </BrutalButton>
      </div>

      <div className="support-panel__tabs">
        <BrutalButton
          variant={tab === "doubt" ? "primary" : "secondary"}
          onClick={() => setTab("doubt")}
          data-testid="support-tab-doubt"
        >
          Ask Doubt
        </BrutalButton>
        <BrutalButton
          variant={tab === "resources" ? "primary" : "secondary"}
          onClick={() => setTab("resources")}
          data-testid="support-tab-resources"
        >
          Resources
        </BrutalButton>
        <BrutalButton
          variant={tab === "correction" ? "primary" : "secondary"}
          onClick={() => setTab("correction")}
          data-testid="support-tab-correction"
        >
          Corrective Tip
        </BrutalButton>
      </div>

      {tab === "doubt" ? (
        <BrutalCard accent="white" className="support-panel__section">
          <form
            className="support-form"
            onSubmit={handleSubmit((values) => {
              doubtMutation.mutate(
                {
                  skill_id: skillId,
                  phase,
                  technique_id: techniqueId,
                  question: values.question,
                },
                {
                  onSuccess: () => reset(),
                }
              );
            })}
          >
            <BrutalInput
              multiline
              rows={4}
              label="What exactly is blocking you?"
              placeholder="Describe the issue, what you tried, and expected output."
              testId="doubt-question"
              error={formState.errors.question?.message}
              name={questionField.name}
              onBlur={questionField.onBlur}
              onChange={questionField.onChange}
              inputRef={questionField.ref}
            />
            <BrutalButton
              type="submit"
              variant="primary"
              data-testid="ask-doubt-btn"
              disabled={doubtMutation.isPending}
            >
              {doubtMutation.isPending ? "Asking..." : "Ask Doubt"}
            </BrutalButton>
          </form>

          {doubtMutation.isError ? <p className="error-text">Doubt request failed.</p> : null}
          {doubtMutation.data ? (
            <BrutalCard accent="blue" className="support-answer" testId="doubt-answer-card">
              <strong>AI Answer</strong>
              <p>{doubtMutation.data.answer}</p>
              {doubtMutation.data.caveat ? <p className="small-copy">Caveat: {doubtMutation.data.caveat}</p> : null}
            </BrutalCard>
          ) : null}
        </BrutalCard>
      ) : null}

      {tab === "resources" ? (
        <BrutalCard accent="white" className="support-panel__section">
          <div className="resource-toolbar">
            <BrutalInput
              label="Search keyword"
              placeholder="gesture, perspective, debugging"
              value={resourceQuery}
              onChange={(event) => setResourceQuery(event.target.value)}
              testId="resource-query"
            />
            <BrutalButton onClick={() => resourcesQuery.refetch()} data-testid="resource-refresh-btn">
              Refresh
            </BrutalButton>
          </div>

          {resourcesQuery.isLoading ? <p>Loading resources...</p> : null}
          {resourcesQuery.isError ? <p className="error-text">Unable to load resources.</p> : null}

          <div className="resource-list" data-testid="resource-list">
            {(resourcesQuery.data?.items ?? []).map((item) => (
              <article className="resource-item" key={item.id}>
                <div className="resource-item__meta">
                  <span>{item.doc_type}</span>
                  <span>{Math.round(item.relevance * 100)}%</span>
                </div>
                <p>{item.snippet}</p>
              </article>
            ))}
          </div>
        </BrutalCard>
      ) : null}

      {tab === "correction" ? (
        <BrutalCard accent="white" className="support-panel__section" testId="correction-tip-section">
          {tipQuery.isLoading ? <p>Checking for correction tip...</p> : null}
          {tipQuery.isError ? <p className="error-text">No correction tip available right now.</p> : null}
          {tipQuery.data?.available ? (
            <TipCard
              text={tipQuery.data.text ?? "Keep protocol strict and retry slowly."}
              severity={tipQuery.data.severity}
              focusStep={tipQuery.data.focus_step}
              testId="tip-card"
            />
          ) : (
            <p>No corrective tip pending.</p>
          )}
        </BrutalCard>
      ) : null}
    </aside>
  );
}
