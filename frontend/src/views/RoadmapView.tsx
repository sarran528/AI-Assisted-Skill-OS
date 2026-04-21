import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useRoadmap } from "../hooks/useRoadmap";

export function RoadmapView() {
  const { skillId } = useParams<{ skillId: string }>();
  const { roadmap, generateRoadmap, getRoadmapStatus, error } = useRoadmap(skillId);

  useEffect(() => {
    if (!roadmap) {
      generateRoadmap(skillId, {
        onSuccess: (data) => {
          const poll = setInterval(() => {
            getRoadmapStatus(data.job_id, {
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
  }, [roadmap, skillId, generateRoadmap, getRoadmapStatus]);

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
