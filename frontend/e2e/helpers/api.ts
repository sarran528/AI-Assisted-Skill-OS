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

    return json(route, { message: "Not mocked", url }, 404);
  });
}
