import type { Page, Route } from "@playwright/test";

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(data),
  });
}

export async function mockFirstTenApis(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();

    if (url.endsWith("/auth/register") || url.endsWith("/auth/login")) {
      return json(route, {
        access_token: "test-token",
        token_type: "bearer",
        user_id: "user-1",
        email: "test@example.com",
      });
    }

    if (url.endsWith("/auth/refresh")) {
      return json(route, {
        access_token: "test-token-2",
        token_type: "bearer",
      });
    }

    if (url.endsWith("/assessment/start")) {
      return json(route, { session_id: "assessment-session-1", levels: [1, 2, 3, 4, 5, 6] });
    }

    if (url.endsWith("/assessment/submit")) {
      return json(route, { ok: true, status: "level_submitted" }, 201);
    }

    if (url.endsWith("/assessment/complete")) {
      return json(route, { ok: true, profile_id: "profile-1" }, 201);
    }

    if (url.endsWith("/skills")) {
      return json(route, [
        { skill_id: "drawing", name: "Drawing", domain: "arts" },
        { skill_id: "python_basics", name: "Python Basics", domain: "coding" },
      ]);
    }

    if (url.endsWith("/skills/baseline")) {
      return json(route, { id: "baseline-1", skill_id: "drawing", perceived_level: 0.5 });
    }

    if (url.endsWith("/roadmaps/generate")) {
      return json(route, {
        roadmap_id: "roadmap-1",
        fingerprint: "fp-drawing-v1",
        status: "completed",
      });
    }

    if (url.endsWith("/sessions/start")) {
      return json(route, {
        session_id: "session-1",
        status: "active",
      });
    }

    if (url.endsWith("/sessions/metrics")) {
      return json(route, { status: "captured" });
    }

    if (url.endsWith("/evidence/upload")) {
      return json(route, {
        evidence_id: "evidence-1",
        session_id: "session-1",
        checkpoint_id: "checkpoint-1",
        artifact_url: "/local-evidence/evidence-1",
        mime_type: "image/png",
        file_size_bytes: 128,
        validated: false,
      }, 201);
    }

    if (url.endsWith("/sessions/complete")) {
      const body = route.request().postDataJSON() as { completed_steps?: string[] } | null;
      const completedCount = body?.completed_steps?.length ?? 0;
      return json(route, {
        session_id: "session-1",
        passed: completedCount >= 4,
        tip_pending: completedCount < 4,
        failure_reason: completedCount < 4 ? "Protocol incomplete" : undefined,
        completed_steps: body?.completed_steps ?? ["1", "2", "3", "4"],
      });
    }

    if (url.endsWith("/doubt/ask")) {
      return json(route, {
        answer: "Use slower pen pressure and confirm step ordering before retry.",
        confidence: "high",
        caveat: "Tip assumes foundation-level stroke control.",
        sources_used: 3,
      });
    }

    if (url.includes("/support/resources")) {
      return json(route, {
        items: [
          {
            id: "res-1",
            doc_type: "guide",
            snippet: "Practice contour lines in 30-second loops before full pass.",
            relevance: 0.91,
          },
          {
            id: "res-2",
            doc_type: "example",
            snippet: "Compare high-contrast references to stabilize edge detection.",
            relevance: 0.82,
          },
        ],
      });
    }

    if (url.includes("/tip/")) {
      return json(route, {
        available: true,
        severity: "moderate",
        text: "You are skipping review; enforce a 20-second review after every execution step.",
        focus_step: "3",
      });
    }

    if (url.endsWith("/validation/checkpoint/validate")) {
      return json(route, {
        passed: true,
        reason: "validated",
        session_id: "session-1",
        checkpoint_id: "checkpoint-1",
      });
    }

    return json(route, { message: "Not mocked", url }, 404);
  });
}
