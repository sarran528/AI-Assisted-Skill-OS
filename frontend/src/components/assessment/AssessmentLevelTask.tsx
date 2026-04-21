import { CountdownChallengeTask } from "./CountdownChallengeTask";
import { FlankerTask } from "./FlankerTask";
import { GoNoGoTask } from "./GoNoGoTask";
import { PatternSwitchTask } from "./PatternSwitchTask";
import { RapidTapTask } from "./RapidTapTask";
import { TimeBudgetTask } from "./TimeBudgetTask";

export interface AssessmentLevelTaskProps {
  level: number;
  onComplete: (results: Record<string, unknown>) => void;
  onRunStateChange?: (running: boolean) => void;
}

export function AssessmentLevelTask({ level, onComplete, onRunStateChange }: AssessmentLevelTaskProps) {
  const common = { onComplete, onRunStateChange, sessionLevel: level };
  switch (level) {
    case 1:
      return <GoNoGoTask {...common} />;
    case 2:
      return <FlankerTask {...common} />;
    case 3:
      return <PatternSwitchTask {...common} />;
    case 4:
      return <RapidTapTask {...common} />;
    case 5:
      return <CountdownChallengeTask {...common} />;
    case 6:
      return <TimeBudgetTask {...common} />;
    default:
      return <GoNoGoTask {...common} />;
  }
}
