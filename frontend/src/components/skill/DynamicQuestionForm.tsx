import React from "react";
import { BrutalButton } from "../brutal/BrutalButton";
import { SkillQuestion } from "../../api/skillApi";

interface DynamicQuestionFormProps {
  questions: SkillQuestion[];
  answers: Record<string, any>;
  onAnswerChange: (questionId: string, value: any) => void;
}

export const DynamicQuestionForm: React.FC<DynamicQuestionFormProps> = ({
  questions,
  answers,
  onAnswerChange,
}) => {
  return (
    <div className="dynamic-form" style={{ display: "grid", gap: "24px" }}>
      {questions.map((q) => (
        <div key={q.id} className="dashboard-value-row">
          <label className="section-title" style={{ marginBottom: "8px", display: "block" }}>
            {q.text}
          </label>

          {q.type === "single_select" && (
            <select
              className="brutal-input"
              value={answers[q.id] || ""}
              onChange={(e) => onAnswerChange(q.id, e.target.value)}
              style={{ width: "100%" }}
            >
              <option value="">Select an option...</option>
              {q.options?.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          )}

          {q.type === "multi_select" && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {q.options?.map((opt) => {
                const isSelected = (answers[q.id] || []).includes(opt);
                return (
                  <BrutalButton
                    key={opt}
                    variant={isSelected ? "primary" : "secondary"}
                    onClick={() => {
                      const current = answers[q.id] || [];
                      const next = isSelected
                        ? current.filter((i: string) => i !== opt)
                        : [...current, opt];
                      onAnswerChange(q.id, next);
                    }}
                    style={{ fontSize: "10px", padding: "4px 8px" }}
                  >
                    {opt}
                  </BrutalButton>
                );
              })}
            </div>
          )}

          {q.type === "numeric" && (
            <input
              type="number"
              className="brutal-input"
              min={q.min}
              max={q.max}
              value={answers[q.id] || ""}
              onChange={(e) => onAnswerChange(q.id, Number(e.target.value))}
              style={{ width: "100%" }}
            />
          )}

          {q.type === "slider" && (
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <input
                type="range"
                className="brutal-slider"
                min={q.min || 1}
                max={q.max || 5}
                step={q.step || 1}
                value={answers[q.id] || q.min || 1}
                onChange={(e) => onAnswerChange(q.id, Number(e.target.value))}
                style={{ flex: 1 }}
              />
              <span className="mono-caps" style={{ width: "24px", textAlign: "right" }}>
                {answers[q.id] || q.min || 1}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
