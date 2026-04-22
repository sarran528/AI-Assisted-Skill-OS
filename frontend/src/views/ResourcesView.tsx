import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { resourceApi } from "../api/resourceApi";
import { useRoadmapStore } from "../store/roadmapStore";
import { Badge } from "../components/ui/Badge";
import { BrutalCard as Card } from "../components/brutal/BrutalCard";

interface ResourceItem {
  title: string;
  url: string;
  doc_type: string;
}

export function ResourcesView() {
  const [searchParams] = useSearchParams();
  const skillId = useRoadmapStore((state) => state.roadmap?.skill_id || state.targetSkillId || "");
  const phase = searchParams.get("phase") || "";
  const techniqueId = searchParams.get("technique_id") || undefined;
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!skillId || !phase) return;
    setLoading(true);
    resourceApi
      .getResources(skillId, phase, techniqueId)
      .then((res) => setResources(res.data.resources))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [skillId, phase, techniqueId]);

  if (!skillId) return <div className="p-8">Select a skill to view resources.</div>;
  if (!phase) return <div className="p-8">Select a phase to view resources.</div>;
  if (loading) return <div className="p-8">Loading resources...</div>;

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Resources</h1>
        <p className="text-muted-foreground">Curated material for your current phase</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {resources.map((resource) => (
          <Card key={resource.url}>
            <div className="p-4">
              <h2 className="text-lg font-bold">{resource.title}</h2>
            </div>
            <div className="p-4 space-y-2">
              <Badge variant="secondary">{resource.doc_type}</Badge>
              <a className="text-primary underline" href={resource.url} target="_blank" rel="noreferrer">
                Open resource
              </a>
            </div>
          </Card>
        ))}
      </div>

      {resources.length === 0 && (
        <div className="text-center text-muted-foreground">No resources available yet.</div>
      )}
    </div>
  );
}
