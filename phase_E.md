Phase E — everything needed, in full detail, with the complete design system and component specification.

---

## Design system decision — before any code is written

The three reference images establish the aesthetic vocabulary. Image 1 (JEDI trainer platform) shows thick borders, high-contrast yellow accent cards, monospaced headings, and structured grid layouts. Image 2 (Retro platform) shows card-based content grids with rounded illustrations, clean hierarchy, and category pill filters. Image 3 (audiobook reader) shows a warm cream background, bold orange CTAs, strong typographic hierarchy, and consistent card patterns.

The SkillOS UI synthesizes these into one coherent neo-brutalist design system using shadcn as the component base.

**Design language**: neo-brutalism with educational utility. Think bold black borders (3px solid), hard box shadows offset by 4px (no blur), cream/white background with electric yellow (`#FFDD00`) and black as the two dominant accent colors, monospaced display font for headings and data, sans-serif for body. Every interactive element has a visible border and a hard shadow that shifts on hover — the shadow moves to 2px offset when pressed, giving a physical push-down effect. No gradients anywhere. No rounded corners beyond 4px. Cards look like physical objects with visible edges.

**Color palette** (committed globally):
```
--background:     #FFFEF0   (warm off-white, from image 3)
--foreground:     #0A0A0A   (near-black)
--accent-yellow:  #FFDD00   (primary accent, from image 1 trainer card)
--accent-green:   #B8F5A0   (success / passed states)
--accent-red:     #FF4D4D   (failure / blocked states)
--accent-blue:    #A8D8FF   (info / active states)
--border:         #0A0A0A   (all borders)
--shadow:         #0A0A0A   (hard shadow color)
--card-bg:        #FFFFFF
--muted:          #F0EFE0
```

**Typography**:
- Display / headings: `Space Mono` (Google Fonts) — monospaced, raw, technical. Matches the JEDI platform heading style.
- Body: `DM Sans` — clean, readable, modern warmth without being generic.
- Monospace data (scores, metrics, parameters): `JetBrains Mono`

**Shadcn component overrides** — every shadcn component gets these base overrides in `globals.css`:
```css
/* Override shadcn's rounded-md and shadow-sm with brutalist equivalents */
.card { border: 3px solid #0A0A0A; box-shadow: 4px 4px 0px #0A0A0A; border-radius: 4px; }
.button { border: 3px solid #0A0A0A; box-shadow: 3px 3px 0px #0A0A0A; border-radius: 4px; transition: box-shadow 0.1s, transform 0.1s; }
.button:hover { box-shadow: 5px 5px 0px #0A0A0A; transform: translate(-1px, -1px); }
.button:active { box-shadow: 1px 1px 0px #0A0A0A; transform: translate(2px, 2px); }
.input { border: 2px solid #0A0A0A; border-radius: 4px; box-shadow: 3px 3px 0px #0A0A0A; }
.badge { border: 2px solid #0A0A0A; border-radius: 2px; font-family: 'Space Mono', monospace; }
```

**Neo-brutalism reference components to pull from**:
- From neobrutalism.dev: the Card component with `shadow` prop, Button with `variant="brutal"`, Badge with hard borders
- From retroui.dev: the stat display blocks (matching image 1's `10+ experience` blocks exactly), the profile header layout
- From brutalistui.site: the progress bar style (thick border, filled with accent color, no rounded ends), the table style

---

## Project setup — what to do before writing a single view

**Tech stack**:
React 18 + TypeScript + Vite (not Next.js — Vite for a college project is simpler to configure and has faster HMR). shadcn/ui components. Tailwind CSS as the styling engine (shadcn requires it). React Router v6 for client-side routing. TanStack Query (React Query) v5 for server state management. React Hook Form + Zod for form validation. Axios for HTTP calls.

**Initialize the project**:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npx shadcn@latest init
```

During shadcn init: choose New York style (cleaner base components), CSS variables yes, no to default colors (you are overriding them).

**Install all packages at once**:
```bash
npm install @tanstack/react-query axios react-router-dom react-hook-form @hookform/resolvers zod
npm install class-variance-authority clsx tailwind-merge lucide-react
npm install -D @types/node
```

**Google Fonts** — add to `index.html` `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

**`tailwind.config.ts`** — extend with the design system:
```typescript
extend: {
  fontFamily: {
    mono: ["Space Mono", "monospace"],
    sans: ["DM Sans", "sans-serif"],
    code: ["JetBrains Mono", "monospace"],
  },
  colors: {
    background: "#FFFEF0",
    foreground: "#0A0A0A",
    "accent-yellow": "#FFDD00",
    "accent-green": "#B8F5A0",
    "accent-red": "#FF4D4D",
    "accent-blue": "#A8D8FF",
    border: "#0A0A0A",
    muted: "#F0EFE0",
  },
  boxShadow: {
    brutal: "4px 4px 0px #0A0A0A",
    "brutal-sm": "2px 2px 0px #0A0A0A",
    "brutal-lg": "6px 6px 0px #0A0A0A",
    "brutal-hover": "6px 6px 0px #0A0A0A",
  }
}
```

**`src/globals.css`** — full design system overrides applied on top of shadcn base.

**Folder structure**:
```
/frontend/src
  /components
    /ui           -- shadcn auto-generated components (do not edit directly)
    /brutal       -- your neo-brutalist override wrappers
      BrutalCard.tsx
      BrutalButton.tsx
      BrutalBadge.tsx
      BrutalInput.tsx
      StatBlock.tsx
      PhaseCard.tsx
      CheckpointRow.tsx
      MetricBar.tsx
      TipCard.tsx
  /views
    AssessmentView.tsx
    DashboardView.tsx
    SessionView.tsx
    RoadmapView.tsx
    DoubtTipView.tsx
  /hooks
    useAssessment.ts
    useRoadmap.ts
    useSession.ts
    useResources.ts
    useDoubt.ts
    useTip.ts
  /api
    client.ts
    assessment.ts
    roadmap.ts
    session.ts
    evidence.ts
    support.ts
  /store
    authStore.ts
  /types
    index.ts
  App.tsx
  main.tsx
```

**`src/api/client.ts`** — Axios instance with auth interceptor:
```typescript
const client = axios.create({ baseURL: import.meta.env.VITE_API_URL });

client.interceptors.request.use(config => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  res => res,
  async error => {
    if (error.response?.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed) return client.request(error.config);
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);
```

**`src/store/authStore.ts`** — Zustand store (add `npm install zustand`) for auth state:
```typescript
interface AuthStore {
  accessToken: string | null;
  user: { userId: string; email: string } | null;
  setToken: (token: string) => void;
  logout: () => void;
}
```

**`src/App.tsx`** — React Router setup with protected route wrapper:
```typescript
<QueryClientProvider client={queryClient}>
  <Router>
    <Routes>
      <Route path="/login" element={<LoginView />} />
      <Route path="/register" element={<RegisterView />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/assessment" element={<AssessmentView />} />
        <Route path="/roadmap/:skillId" element={<RoadmapView />} />
        <Route path="/session/:sessionId" element={<SessionView />} />
      </Route>
    </Routes>
  </Router>
</QueryClientProvider>
```

---

## Brutal component library — what to build before the views

These go in `src/components/brutal/`. Every view imports from here, never from shadcn directly.

**`BrutalCard.tsx`**:
```tsx
interface BrutalCardProps {
  children: React.ReactNode;
  accent?: "yellow" | "green" | "red" | "blue" | "white";
  className?: string;
}
// Renders: border-3 border-foreground shadow-brutal bg-{accent} p-4
// accent="yellow" → background: #FFDD00 — used for active/highlight cards (matching image 1's trainer card)
// accent="green" → background: #B8F5A0 — passed states
// accent="red" → background: #FF4D4D — failed/blocked states
```

**`BrutalButton.tsx`**:
```tsx
// Wraps shadcn Button with brutalist override
// variant="primary": bg-accent-yellow border-foreground shadow-brutal
// variant="secondary": bg-white border-foreground shadow-brutal
// variant="danger": bg-accent-red border-foreground shadow-brutal
// All have: hover:shadow-brutal-hover hover:-translate-x-px hover:-translate-y-px
//           active:shadow-brutal-sm active:translate-x-1 active:translate-y-1
```

**`StatBlock.tsx`** — directly inspired by image 1's `10+ experience`, `#1 on platform` blocks:
```tsx
interface StatBlockProps {
  value: string;    // "0.84" or "32" or "Active"
  label: string;    // "cognitive capacity" or "parameters"
  accent?: boolean; // if true, yellow background
}
// Renders as a bordered box with:
// value in Space Mono bold 24px
// label in DM Sans 11px uppercase tracking-widest
// border: 2px solid #0A0A0A
// box-shadow: 3px 3px 0px #0A0A0A
// padding: 12px 16px
```

**`PhaseCard.tsx`** — card for each roadmap phase:
```tsx
interface PhaseCardProps {
  phase: string;
  status: "locked" | "active" | "completed";
  estimatedWeeks: number;
  checkpoints: CheckpointSummary[];
  onEnter?: () => void;
}
// locked: gray border, muted background, lock icon
// active: yellow background, bold border, "Enter Phase" button
// completed: green background, checkmark
```

**`CheckpointRow.tsx`** — single checkpoint display:
```tsx
// status pill: "pending" | "attempted" | "passed" | "failed"
// passed: bg-accent-green pill with check
// failed: bg-accent-red pill with x
// pending: bg-muted pill with dash
```

**`MetricBar.tsx`** — progress bar for ProfileVector dimensions and learning parameters:
```tsx
// No rounded corners
// Container: border-2 border-foreground h-6
// Fill: bg-accent-yellow height 100% width={value * 100}%
// Label: DM Sans 12px left of bar
// Value: JetBrains Mono 12px right of bar
// Matching the thick bar style from brutalistui.site
```

**`TipCard.tsx`** — triggered on session failure:
```tsx
// BrutalCard with accent="red"
// Header: "CORRECTION NEEDED" in Space Mono bold uppercase
// Tip text: DM Sans 16px
// Severity badge: "minor" | "moderate" | "critical" — color coded
// Target step if present: "Focus: Step 3"
// Bottom border stripe: 4px solid black bottom border only, no other shadow
```

---

## Step 24 — Assessment UI

**What it is**

Six sequential level interfaces. The user completes each level's 10 questions. Metrics are captured in real time and sent to `POST /assessment/submit`. The UI must display: current level, question count, lives remaining (3 lives shown as icons), a timer, and the question/task interface. After all 6 levels are complete, `POST /assessment/complete` is called and the user is redirected to skill selection.

**File**: `src/views/AssessmentView.tsx`

**Layout structure**:
```
┌─────────────────────────────────────────────────────┐
│  SKILLOS          Level 3/6     ♥ ♥ ♡     [14:23]  │  ← top bar: Space Mono, yellow bg
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │  EXECUTIVE CONTROL ASSESSMENT              │    │  ← BrutalCard accent="yellow"
│  │  Working memory + inhibition               │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  ┌───────────────────────┐  ┌───────────────────┐  │
│  │  QUESTION 4 / 10      │  │  PERFORMANCE      │  │
│  │                       │  │  acc:  ████░░ 0.7 │  │  ← MetricBar components
│  │  [Task display area]  │  │  lat:  ██░░░░ 0.4 │  │
│  │                       │  │  retry: ██████ 0  │  │
│  └───────────────────────┘  └───────────────────┘  │
│                                                     │
│         [BrutalButton primary "Submit Response"]    │
└─────────────────────────────────────────────────────┘
```

**`src/hooks/useAssessment.ts`** — manages assessment state:
```typescript
interface AssessmentState {
  currentLevel: number;        // 1-6
  currentQuestion: number;     // 1-10
  livesRemaining: number;      // 0-3
  sessionId: string | null;
  levelStartTime: number;      // timestamp for response time tracking
  responseTimings: number[];   // ms per question
  accuracyRecord: boolean[];   // correct/incorrect per question
  retryCount: number;
}
```

Hooks: `useStartAssessment()` → calls `POST /assessment/start`. `useSubmitLevel(levelData)` → calls `POST /assessment/submit` with computed metrics. `useCompleteAssessment()` → calls `POST /assessment/complete`.

**Metric capture logic** — captured automatically in the hook, not manually by the user. When a question is displayed, record `startTime = Date.now()`. When the user submits an answer, record `responseTime = Date.now() - startTime`. Push to `responseTimings`. Track `accuracyRecord[i] = isCorrect`. On level completion, compute `mean_response_time`, `response_time_variance`, `performance_decay` (accuracy drop from first 5 questions to last 5 questions), `retry_depth` from `retryCount`, and send to `POST /assessment/submit`.

**Life loss visualization** — three heart icons from lucide-react. Full heart = remaining life. Empty heart = lost life. On life loss: the border of the entire assessment card flashes red for 500ms using a CSS animation. Lives display updates immediately.

**Timer** — `useEffect` with `setInterval` counting down from 900 seconds (15 minutes). Displayed in `Space Mono` in the top bar. When time reaches 0, the level automatically completes with current state.

**Level selection** — before any level starts, show a 6-card grid where each card represents one level. Cards are `PhaseCard`-style. Status: `available` (white), `completed` (green), `in_progress` (yellow). Free order — user can click any available card. This directly matches the free-order completion rule from the system architecture.

**shadcn components used**: `Progress` (for question counter), `Alert` (for life loss notification), `Dialog` (for level complete confirmation). All overridden with brutal styles.

---

## Step 25 — Dashboard

**What it is**

The landing view after login. Shows active roadmap status, current phase, last session result, and cognitive profile summary. References image 2's multi-column layout with left sidebar, center content, and right panel.

**File**: `src/views/DashboardView.tsx`

**Layout** — three-column matching image 2:
```
┌──────────┬─────────────────────────┬────────────────┐
│ SIDEBAR  │  MAIN CONTENT           │  RIGHT PANEL   │
│          │                         │                │
│ Nav      │  Active Roadmap         │  Profile       │
│ links    │  ┌──────────────────┐   │  Summary       │
│          │  │ DRAWING          │   │                │
│          │  │ Phase 2/4 Active │   │  4 stat blocks │
│          │  └──────────────────┘   │  (like image 1)│
│          │                         │                │
│          │  Recent Sessions        │  Recent        │
│          │  [session cards]        │  Activity      │
└──────────┴─────────────────────────┴────────────────┘
```

**Left sidebar** — fixed width 200px, `border-r-3 border-foreground`. Nav items: Home, My Skills, Assessment, Settings. Each nav item: `DM Sans 14px`, hover state has `bg-accent-yellow` background fill. Active state has black background, white text. Skill selection dropdown shows available skills — clicking one updates the main content area to show that skill's roadmap.

**Main content — active roadmap card**:
```tsx
<BrutalCard accent="yellow">
  <div className="font-mono text-xs uppercase tracking-widest">Active Skill</div>
  <div className="font-mono text-3xl font-bold">DRAWING</div>
  <div className="text-sm">Phase 2 of 4 — Intermediate Shading</div>
  <div className="flex gap-4 mt-4">
    {phases.map(phase => <PhaseProgressPip status={phase.status} />)}
  </div>
  <BrutalButton variant="primary" onClick={enterSession}>Enter Today's Session</BrutalButton>
</BrutalCard>
```

`PhaseProgressPip` — small square 20×20px, filled yellow if completed, filled black border active, gray if locked. A row of four of these communicates roadmap progress at a glance.

**Recent sessions grid** — matching image 1's "Students reviews" row but for session history:
- Each session card: `BrutalCard` white, shows technique name, date, status badge (Passed/Failed), and key metric (accuracy %).
- "View all" link top right in `Space Mono`.

**Right panel — profile summary**:
```tsx
// Directly implementing the StatBlock row from image 1
// 4 stat blocks in a 2×2 grid
<div className="grid grid-cols-2 gap-3">
  <StatBlock value="0.84" label="cognitive cap." accent />
  <StatBlock value="0.71" label="attn stability" />
  <StatBlock value="0.65" label="learn tolerance" />
  <StatBlock value="0.78" label="stress resilience" />
</div>
```

**`src/hooks/useRoadmap.ts`**:
```typescript
const { data: roadmap } = useQuery({
  queryKey: ["roadmap", userId],
  queryFn: () => api.get(`/roadmap/${userId}`).then(r => r.data),
  staleTime: 60_000,
});
```

**`src/hooks/useDashboard.ts`** — combines roadmap query, profile query, and recent sessions query into one convenient hook with a loading/error state that covers all three.

**Empty state** — if no roadmap exists: a large `BrutalCard` with yellow background showing "NO ACTIVE ROADMAP" in `Space Mono` 32px, and two buttons: "Start Assessment" (if no profile) and "Pick a Skill" (if profile exists). This follows the pattern from image 2's "Upgrade to a PRO plan" bottom-left card.

---

## Step 26 — Session interface

**What it is**

The view where the user actually practices. Shows the protocol steps one by one. Captures metrics as the user works. Allows evidence file upload. Shows real-time feedback on metric performance. The most complex view in the application.

**File**: `src/views/SessionView.tsx`

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│  BLIND CONTOUR DRAWING      Session #3    [LIVE ●]  │  ← top bar yellow bg
├────────────────────────────┬────────────────────────┤
│  PROTOCOL                  │  METRICS               │
│                            │                        │
│  ✓ Step 1: Set up materials│  acc:   ████████ 0.91  │
│  ● Step 2: Execute         │  time:  ███░░░░░ 12m   │
│  ○ Step 3: Review output   │  errors:██░░░░░░ 2     │
│  ○ Step 4: Record obs.     │  retry: ░░░░░░░░ 0     │
│                            │                        │
│  [STEP 2 EXPANDED]:        │  ┌──────────────────┐  │
│  ┌─────────────────────┐   │  │ UPLOAD EVIDENCE  │  │
│  │ Draw a continuous   │   │  │                  │  │
│  │ line without lifting │  │  │ [drag & drop     │  │
│  │ your pen...         │   │  │  area]           │  │
│  └─────────────────────┘   │  └──────────────────┘  │
│                            │                        │
│  [Mark Step Complete]      │  [Complete Session]    │
└────────────────────────────┴────────────────────────┘
```

**Protocol steps display** — each step is a row. States: completed (left border green, checkmark), current (yellow background, full border), pending (gray, locked). Clicking a pending step while a previous one is incomplete shows an error toast. Steps cannot be skipped. This enforces protocol adherence visually.

**Real-time metrics panel** — `MetricBar` components for each captured metric. Metrics update on a 10-second interval via `useEffect` → `POST /session/metrics`. The bars animate smoothly using CSS transitions when values update.

**Evidence upload** — drag-and-drop zone built with native HTML drag events (no library needed):
```tsx
const [isDragging, setIsDragging] = useState(false);

// Drop zone: BrutalCard with dashed border (border-dashed border-3) 
// when isDragging: bg-accent-yellow, solid border
// Shows uploaded files as list with remove button
// "Upload Evidence" button triggers POST /evidence/upload
```

File type display: uploaded images show a thumbnail. PDFs show a document icon. Videos show a play icon. All from lucide-react.

**`src/hooks/useSession.ts`**:
```typescript
// Manages: session start, metric submission interval, step completion tracking,
// evidence upload, session completion
// Key interval: every 10 seconds sends accumulated metrics to POST /session/metrics
// On unmount: clears interval and sends final metric batch
useEffect(() => {
  const interval = setInterval(() => {
    submitMetrics(accumulatedMetrics);
  }, 10_000);
  return () => clearInterval(interval);
}, []);
```

**Complete session flow**: user clicks "Complete Session" → validation modal opens (shadcn `Dialog` with brutal override) showing: steps completed count, evidence uploaded count, "Are you sure?" confirm. On confirm → `POST /session/complete` → response includes `passed: bool` and optionally `tip_pending: bool`. If passed → success animation (yellow card flashes, checkmark appears) → redirect to RoadmapView. If failed → red card appears with failure reason → if `tip_pending`, shows "Generating correction..." → polls `GET /tip/:session_id` every 2 seconds → when tip arrives, renders `TipCard` component.

**Live indicator** — top bar shows `[LIVE ●]` with the dot pulsing using CSS `@keyframes pulse`. This communicates that metrics are being captured actively.

---

## Step 27 — Roadmap viewer

**What it is**

Shows the full roadmap for a selected skill. All phases, all checkpoints, all evidence requirements. Phase statuses: locked, active, completed. Checkpoint statuses: pending, attempted, passed, failed. This is the primary navigation hub for skill progression.

**File**: `src/views/RoadmapView.tsx`

**Layout** — vertical timeline-style. Matching image 3's organized left-to-right content structure but made vertical:

```
DRAWING ROADMAP                          Profile v3 | Est. 8 weeks
Fingerprint verified ✓

┌─────────────────────────────────────────────────────┐
│ PHASE 1: FUNDAMENTALS          ✓ COMPLETED          │  ← BrutalCard green
│ Weeks 1-2                                           │
│ ✓ Line control   ✓ Basic shapes   ✓ Proportions    │
└─────────────────────────────────────────────────────┘
         │
┌─────────────────────────────────────────────────────┐
│ PHASE 2: INTERMEDIATE SHADING  ● ACTIVE             │  ← BrutalCard yellow
│ Weeks 3-5  [ 2 of 3 checkpoints passed ]            │
│                                                     │
│  ✓ Checkpoint 1: Produce 5 shapes...    [PASSED]   │
│  ✓ Checkpoint 2: Demonstrate hatching...  [PASSED]  │
│  ○ Checkpoint 3: Draw room in persp...  [PENDING]   │
│                                                     │
│  [Enter Session →]          [View Evidence]         │
└─────────────────────────────────────────────────────┘
         │
┌─────────────────────────────────────────────────────┐
│ PHASE 3: COMPOSITION           🔒 LOCKED            │  ← BrutalCard muted gray
└─────────────────────────────────────────────────────┘
```

**Phase connector** — the `│` between phase cards is a 3px wide, `#0A0A0A` colored vertical line drawn with a `div` of width 3px, height 40px, background black. This creates the visual timeline flow.

**Checkpoint rows** — inside active phase cards, each checkpoint is a `CheckpointRow` component. Shows: description, evidence type badge (`NUMERIC` / `ARTIFACT` / `LOG` in `Space Mono` tiny caps), status badge, and a "Submit Evidence" button if pending.

**Fingerprint display** — top of the page shows the roadmap integrity status. If `verify_roadmap_integrity` returns true: `"Integrity verified ✓"` in green badge. This is a subtle but powerful neo-brutalist detail — showing technical internals as a UI element. Matches the raw, honest aesthetic.

**Learning parameters panel** — collapsible section showing all 32 parameters as `MetricBar` components grouped by their 8 groups. Toggle with a `BrutalButton variant="secondary"`. This is for power users and satisfies the "technical transparency" theme. The implementation plan shows all 32 parameters — the UI surfaces them. This is distinctive and matches the neo-brutalist philosophy of showing the machine.

**`src/hooks/useRoadmap.ts`** additions — `useVerifyRoadmap(roadmapId)`, `usePhaseStatus(roadmapId, phase)`.

---

## Step 28 — Doubt and tip interface

**What it is**

Not a separate page — a persistent side panel that can be opened from within the Session interface and Roadmap viewer. The doubt input is always accessible during active learning. The tip card appears automatically after a failed session. This matches the inline support pattern from image 2's right panel.

**File**: `src/components/brutal/SupportPanel.tsx` — a slide-in panel component.

**Panel layout**:
```
┌────────────────────────────────┐
│  ✕   LEARNING SUPPORT          │  ← Space Mono, yellow header bar
├────────────────────────────────┤
│  [ DOUBT ]  [ RESOURCES ]      │  ← tab switcher, brutal style
├────────────────────────────────┤
│                                │
│  ASK A QUESTION                │
│  ┌──────────────────────────┐  │
│  │ Type your question...    │  │  ← BrutalInput
│  └──────────────────────────┘  │
│  Context: Drawing > Phase 2 >  │
│           Blind Contour        │
│                                │
│  [BrutalButton "Get Answer"]   │
│                                │
├────────────────────────────────┤
│  ANSWER                        │
│  ┌──────────────────────────┐  │
│  │ [Answer text from API]   │  │  ← BrutalCard white
│  │ Confidence: HIGH         │  │
│  │ Sources: 3 chunks used   │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
```

**Doubt tab**:
- `react-hook-form` with `zod` schema: `{ question: z.string().min(10).max(500) }`
- On submit: `POST /doubt/ask` with `{ session_id, user_question }`
- Loading state: "THINKING..." in `Space Mono` with three dots cycling
- Answer displayed in `BrutalCard` white with confidence badge
- If `caveat` present: yellow warning box below the answer with the caveat text
- Previous questions: a scrollable history list above the input, each showing question and truncated answer

**Resources tab**:
- Auto-populated when panel opens in session context
- Three to five `BrutalCard` components stacked vertically
- Each card: doc type badge (`TUTORIAL` / `GUIDE` / `FAILURE ANALYSIS`), content snippet (first 150 chars), relevance score as a small `MetricBar`
- Refresh button: re-queries with updated context

**Tip card display** — when a session fails and `tip_pending=true`, the support panel opens automatically to a third tab "CORRECTION". Polling state: pulsing yellow card with "Generating correction..." text. When tip arrives, `TipCard` component renders with the full tip. Severity determines border color: `minor` → black, `moderate` → amber, `critical` → red border.

**`src/hooks/useDoubt.ts`**:
```typescript
const { mutate: askDoubt, data: doubtResponse, isPending } = useMutation({
  mutationFn: (question: string) =>
    api.post("/doubt/ask", { sessionId, userQuestion: question }).then(r => r.data),
});
```

**`src/hooks/useTip.ts`**:
```typescript
// Polls GET /tip/:sessionId every 2 seconds when tipPending=true
const { data: tip } = useQuery({
  queryKey: ["tip", sessionId],
  queryFn: () => api.get(`/tip/${sessionId}`).then(r => r.data),
  refetchInterval: tipPending ? 2000 : false,
  enabled: !!sessionId && tipPending,
});
```

**Support panel trigger** — a floating button pinned to the right side of every view when inside a session or roadmap context. `position: fixed, right: 0, top: 50%`. The button is 48px wide, yellow background, black border, "?" in Space Mono. On click, opens the panel from the right with a CSS `transform: translateX()` transition.

---

## Step 29 — End-to-end integration tests

**What it is**

Automated tests that run the full user journey from registration to phase advancement. Verifies every system integration point works together. Uses Playwright for browser-level E2E and pytest for API-level integration.

**New packages**:

Frontend: `npm install -D @playwright/test`. Run `npx playwright install` to download browser binaries.

Backend (already installed): `pytest`, `pytest-asyncio`, `httpx`.

**Playwright config** — `frontend/playwright.config.ts`:
```typescript
export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
```

**`frontend/e2e/` folder structure**:
```
e2e/
  helpers/
    auth.ts        -- login/register helpers
    assessment.ts  -- completes assessment programmatically
    api.ts         -- direct API calls from Playwright tests
  full-loop.spec.ts
  assessment.spec.ts
  session.spec.ts
  roadmap.spec.ts
```

**`e2e/full-loop.spec.ts`** — the main E2E test covering all 13 steps of the execution loop:

```typescript
test("full user journey: register to phase advancement", async ({ page, request }) => {
  // Step 1: Register
  await page.goto("/register");
  await page.fill('[data-testid="email"]', `test-${Date.now()}@test.com`);
  await page.fill('[data-testid="password"]', "TestPass123!");
  await page.click('[data-testid="register-btn"]');
  await expect(page).toHaveURL("/dashboard");

  // Step 2: Start assessment
  await page.click('[data-testid="start-assessment"]');
  await expect(page).toHaveURL("/assessment");

  // Step 3-5: Complete all 6 assessment levels (API shortcut for speed)
  const token = await getTokenFromLocalStorage(page);
  const profileResponse = await request.post("/assessment/complete", {
    headers: { Authorization: `Bearer ${token}` },
    data: buildMockAssessmentPayload(),
  });
  expect(profileResponse.status()).toBe(201);

  // Step 6: Select skill
  await page.goto("/dashboard");
  await page.click('[data-testid="skill-drawing"]');

  // Step 7: Complete grounding probes
  await page.click('[data-testid="grounding-recognition-0"]');
  await page.click('[data-testid="grounding-submit"]');

  // Step 8: Generate roadmap
  await page.click('[data-testid="generate-roadmap"]');
  await expect(page.locator('[data-testid="roadmap-fingerprint"]')).toBeVisible({ timeout: 30_000 });

  // Step 9-10: Start session and submit metrics
  await page.click('[data-testid="enter-session"]');
  await expect(page).toHaveURL(/\/session\//);
  await page.click('[data-testid="step-1-complete"]');
  await page.click('[data-testid="step-2-complete"]');
  await page.click('[data-testid="step-3-complete"]');
  await page.click('[data-testid="step-4-complete"]');

  // Step 11: Upload evidence
  const fileInput = page.locator('[data-testid="evidence-upload"]');
  await fileInput.setInputFiles("e2e/fixtures/test-drawing.png");
  await expect(page.locator('[data-testid="evidence-uploaded"]')).toBeVisible();

  // Step 12: Complete session
  await page.click('[data-testid="complete-session"]');
  await page.click('[data-testid="confirm-complete"]');

  // Step 13: Validate checkpoint (triggered via API to avoid LLM latency)
  const sessionId = await page.getAttribute('[data-testid="session-id"]', 'data-session-id');
  const validationResponse = await request.post("/checkpoint/validate", {
    headers: { Authorization: `Bearer ${token}` },
    data: { sessionId, checkpointId: "checkpoint-1" },
  });
  expect(validationResponse.status()).toBe(200);

  // Verify phase advancement
  await page.goto("/roadmap/drawing");
  await expect(page.locator('[data-testid="phase-1-status"]')).toHaveText("COMPLETED");
});
```

**`data-testid` attributes** — every interactive element in every view gets a `data-testid` attribute. Add these as you build each view. Playwright tests reference only `data-testid`, never CSS classes or text content. This makes tests resilient to design changes.

**Backend integration test** — `backend/tests/e2e/test_full_loop.py`:
```python
@pytest.mark.asyncio
async def test_complete_execution_loop(async_client: AsyncClient, test_db):
    # Register
    r = await async_client.post("/auth/register", json={...})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Assessment complete
    r = await async_client.post("/assessment/complete", headers=headers, json=mock_signals)
    profile_id = r.json()["profile_id"]
    
    # Skill grounding
    r = await async_client.post("/skill/baseline", headers=headers, json=mock_grounding)
    
    # Generate roadmap (sync for test — skip job queue)
    r = await async_client.post("/roadmap/generate", headers=headers, json={"skill_id": "drawing"})
    roadmap_id = r.json()["roadmap_id"]
    
    # Verify roadmap fingerprint
    r = await async_client.get(f"/roadmap/{roadmap_id}/verify", headers=headers)
    assert r.json()["valid"] is True
    
    # Start session
    r = await async_client.post("/session/start", headers=headers, json={...})
    session_id = r.json()["session_id"]
    
    # Submit metrics
    await async_client.post("/session/metrics", headers=headers, json=mock_metrics)
    
    # Complete session
    r = await async_client.post("/session/complete", headers=headers, json={
        "completed_steps": ["s1", "s2", "s3", "s4"]
    })
    assert r.json()["passed"] is True
    
    # Validate checkpoint
    r = await async_client.post("/checkpoint/validate", headers=headers, json={
        "session_id": session_id,
        "checkpoint_id": "checkpoint-1"
    })
    assert r.json()["passed"] is True
    
    # Verify phase advanced
    r = await async_client.get(f"/roadmap/{roadmap_id}", headers=headers)
    phases = r.json()["phases"]
    assert phases["fundamentals"]["status"] == "completed"
    assert phases["intermediate"]["status"] == "active"
```

**CI integration** — add to `ci.yml` GitHub Actions:
```yaml
e2e:
  runs-on: ubuntu-latest
  needs: [backend-tests, frontend-build]
  steps:
    - uses: actions/checkout@v4
    - name: Start services
      run: docker-compose up -d
    - name: Run backend integration tests
      run: pytest backend/tests/e2e/ -v
    - name: Install Playwright
      run: npx playwright install --with-deps
    - name: Run Playwright E2E tests
      run: npx playwright test
    - uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: playwright-traces
        path: frontend/test-results/
```

Playwright traces are uploaded as CI artifacts on failure — this gives you a full video and DOM snapshot of what went wrong.

---

## First 10 execution-loop steps status

✅ Step 1 — Register: completed.

✅ Step 2 — Start assessment: completed.

✅ Step 3 — Assessment level flow initialized: completed.

✅ Step 4 — Assessment level metric submission loop: completed.

✅ Step 5 — Assessment completion and redirect: completed.

✅ Step 6 — Skill selection from dashboard: completed.

✅ Step 7 — Grounding probe submission: completed.

✅ Step 8 — Roadmap generation trigger + fingerprint visibility: completed.

✅ Step 9 — Session start flow: completed.

✅ Step 10 — Session metric submission from protocol actions: completed.

## Steps 11-20 status (iteration update)

✅ Step 11 — Evidence upload wired in Session UI and API (`/evidence/upload`), covered by Playwright first-13 flow.

✅ Step 12 — Session completion confirmation flow wired (`/sessions/complete`), covered by Playwright first-13 flow.

✅ Step 13 — Checkpoint validation trigger wired (`/validation/checkpoint/validate`), covered by Playwright first-13 flow.

✅ Step 14 — Session execution rules completed in `/sessions/complete` (`backend/session/execution.py` + `backend/session/router.py`) with protocol adherence checks, weighted quality scoring, retry limit handling, and structured failure reasons.

✅ Step 15 — Validation engine completed with multi-evidence evaluation (`artifact`, `numeric`, `behavioral_log`) plus persisted validation metadata and explicit reason codes (`backend/validation/engine.py`, `backend/validation/validators.py`, `backend/validation/router.py`, `backend/validation/schemas.py`).

✅ Step 16 — Orchestration transition helpers fully applied across session and checkpoint lifecycle paths (`start`, `metrics`, `complete`, and checkpoint validation transitions) via `backend/orchestration/state_machine.py`, `backend/orchestration/orchestrator.py`, `backend/session/router.py`, and `backend/validation/engine.py`.

✅ Step 17 — Queue execution completed with DB-backed job lifecycle updates (`queued` → `running` → `completed`/`failed`) and concrete checkpoint validation task execution in `backend/shared/queue/tasks.py`, plus async validation enqueue endpoint in `backend/validation/router.py`.

✅ Step 18 — RAG retrieval completed as a hybrid pipeline: semantic ranking (vector distance when embedding is available) plus lexical fallback scoring, with score surfaced in response (`backend/rag/router.py`, `backend/rag/retriever.py`, `backend/rag/query_builder.py`, `backend/rag/schemas.py`).

✅ Step 19 — Offline RAG pipeline completed with configurable chunking, optional run report output, and idempotent source re-index behavior (`scripts/rag/pipeline.py`, `scripts/rag/indexer.py`).

✅ Step 20 — Cross-module wiring and validation completed for steps 14-20 with targeted backend tests (`tests/test_session_execution.py`, `tests/test_validation_rules.py`, `tests/test_rag_retriever.py` all passing in focused run) and frontend regression checks (`npm run build`, `npm run test:e2e:first13` passing).

## Steps 24-29 status (iteration update)

✅ Step 24 — Assessment UI upgraded in `frontend/src/views/AssessmentView.tsx` with free-order level cards, per-level timer, life-loss flash, real-time metric accumulation, and complete flow redirect.

✅ Step 25 — Dashboard expanded in `frontend/src/views/DashboardView.tsx` with phase pips, recent session cards, and profile/stat layout continuity.

✅ Step 26 — Session interface expanded in `frontend/src/views/SessionView.tsx` with strict protocol ordering feedback, 10-second metric submission loop, drag-and-drop evidence zone, and completion confirmation summary.

✅ Step 27 — Roadmap viewer expanded in `frontend/src/views/RoadmapView.tsx` with timeline cards, checkpoint status rows, integrity banner, and collapsible roadmap parameters panel.

✅ Step 28 — Doubt and tip side panel implemented through `frontend/src/components/brutal/SupportPanel.tsx`, `frontend/src/components/brutal/TipCard.tsx`, `frontend/src/api/support.ts`, and hooks `useDoubt`, `useTip`, `useResources`; integrated into Session and Roadmap views, with backend endpoints wired at `/support/resources`, `/support/doubt/ask`, and `/tip/{session_id}`.

✅ Step 29 — Frontend E2E suite expanded with `frontend/e2e/full-loop.spec.ts`, `frontend/e2e/assessment.spec.ts`, `frontend/e2e/session.spec.ts`, `frontend/e2e/roadmap.spec.ts`, plus `frontend/e2e/helpers/api.ts` support mocks and dedicated npm scripts; backend integration loop test scaffolded in `backend/tests/e2e/test_full_loop.py`.

---

## Phase E completion gate

Phase E is complete when all of the following are true.

All five views render without console errors in Chromium, Firefox, and WebKit (Playwright's three browser targets).

The neo-brutalist design system is applied consistently: every card has a hard shadow, every button has the push-down interaction, `Space Mono` is used for all headings and data values, the color palette matches the defined CSS variables with no hardcoded hex values outside `globals.css`.

`npx playwright test` passes all tests in `e2e/full-loop.spec.ts`, `assessment.spec.ts`, `session.spec.ts`, `roadmap.spec.ts` — zero failures.

`pytest backend/tests/e2e/test_full_loop.py` passes — the full 13-step execution loop completes without errors.

Evidence upload works end-to-end: a PNG file uploaded from the Playwright test appears in MinIO (local) with a valid presigned URL that returns 200 when fetched.

The Doubt system returns a grounded answer within 10 seconds in the E2E test — verified by Playwright `toBeVisible` with a 10-second timeout on the answer element.

The Tip card appears automatically after a forced session failure — the E2E test triggers two failures for the same technique and asserts the `TipCard` component becomes visible.

The roadmap fingerprint verification element (`data-testid="roadmap-fingerprint"`) shows "Integrity verified ✓" on the Roadmap viewer.

Lighthouse score in CI using `playwright-lighthouse` plugin: Performance ≥ 80, Accessibility ≥ 90 — enforced as a CI gate.

`import-linter` passes — no frontend view imports from backend modules, no backend modules import from each other in violation of the declared contracts.

System is complete. All 13 steps of the Technical Implementation Plan execution loop are covered end to end.