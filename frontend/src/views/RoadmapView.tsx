import { useEffect } from "react";
import { useAuthStore } from "../store/authStore";
import { useRoadmapStore } from "../store/roadmapStore";
import { useRoadmap } from "../hooks/useRoadmap";

export function RoadmapView() {
  const userId = useAuthStore((state) => state.user?.id);
  const skillId = useRoadmapStore((state) => state.targetSkillId);
  const { roadmap, generateRoadmap, getRoadmapStatus, error } = useRoadmap(userId, skillId);

  useEffect(() => {
    if (!roadmap && userId && skillId) {
      generateRoadmap({ userId, skillId }, {
        onSuccess: (data) => {
          const poll = setInterval(() => {
            getRoadmapStatus(userId, {
              onSuccess: (statusData) => {
                if (statusData.status !== "queued") {
                  clearInterval(poll);
                }
              },
            });
          }, 5000);
        },
      });
    }
  }, [roadmap, userId, skillId, generateRoadmap, getRoadmapStatus]);

  if (!userId) {
    return <div>Sign in to view your roadmap.</div>;
  }

  if (!skillId) {
    return <div>Select a skill to generate a roadmap.</div>;
  }

  if (error) {
    return <div>Error loading roadmap</div>;
  }

  if (!roadmap) {
    return <div>Generating roadmap...</div>;
  }

  return (
    <div>
      <h1>Roadmap</h1>
      <p>ID: {roadmap.id}</p>
      <p>Skill ID: {roadmap.skill_id}</p>
    </div>
  );
}
