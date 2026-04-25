// Minimum required contradiction rules
export function detectContradiction(answers: number[]): boolean {
  // Assuming answers index maps to the questions 0-5
  // hrs: 0=<2, 1=2-5, 2=5-10, 3=10+
  // session: 0=15m, 1=30m, 2=45m, 3=60m+
  // days: 0=1-2, 1=3-4, 2=5-6, 3=7
  const [hrs, session, days] = answers;

  // < 2hrs/week + every day + 60min sessions = impossible
  if (hrs === 0 && days === 3 && session === 3) return true;

  // 10+ hrs/week + only 1-2 days = structurally inconsistent
  // max 2 days * say even max 2-3 hours = 4-6 hours, not 10+
  if (hrs === 3 && days === 0) return true;

  // 5-10hrs/week + 15min sessions + every day = mismatch
  // 7 days * 15min = 105min = <2hrs, contradicts 5-10hrs selection
  if (hrs === 2 && session === 0 && days === 3) return true;

  return false;
}
