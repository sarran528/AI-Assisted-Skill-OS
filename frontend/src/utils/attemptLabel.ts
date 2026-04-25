const LABELS = ['never', 'once', 'twice', 'thrice', 'four times', 'five times'];

export const getAttemptLabel = (attempts: number): string => {
  return LABELS[Math.min(attempts, LABELS.length - 1)];
};
