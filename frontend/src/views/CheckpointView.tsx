import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { checkpointApi } from "../api/checkpointApi";
import { Badge } from "../components/ui/Badge";
import { BrutalButton as Button } from '../components/brutal/BrutalButton';
import { BrutalCard as Card, CardContent, CardHeader, CardTitle } from "../components/brutal/BrutalCard";

interface Checkpoint {
  checkpoint_id: string;
  status: string;
  phase: string;
}

export function CheckpointView() {
  const { roadmapId } = useParams<{ roadmapId: string }>();
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!roadmapId) return;
    checkpointApi
      .listCheckpoints(roadmapId)
      .then((res) => setCheckpoints(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [roadmapId]);

  if (loading) return <div className="p-8">Loading checkpoints...</div>;

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Checkpoints</h1>
        <p className="text-muted-foreground">Track your progress through key milestones</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {checkpoints.map((cp) => (
          <Card key={cp.checkpoint_id}>
            <CardHeader>
              <CardTitle className="text-lg">{cp.checkpoint_id}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Phase</p>
                <p className="font-medium">{cp.phase}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge
                  variant={
                    cp.status === "completed"
                      ? "default"
                      : cp.status === "active"
                        ? "secondary"
                        : "outline"
                  }
                >
                  {cp.status}
                </Badge>
              </div>

              <Button variant="outline" className="w-full">
                View Details
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {checkpoints.length === 0 && (
        <div className="text-center text-muted-foreground">No checkpoints available yet.</div>
      )}
    </div>
  );
}
