import { BrutalCard as Card } from "../components/brutal/BrutalCard";
import { useNavigationStore } from "../store/navigationStore";

export function ResourcesView() {
  const { roadmapState, currentSkill } = useNavigationStore();
  const hasRoadmap = roadmapState.isGenerated;
  const techniqueResources = [
    { title: "Technique walkthrough video", type: "video" },
    { title: "Checkpoint preparation guide", type: "guide" },
  ];
  const phaseResources = [{ title: "Phase reading pack", type: "article" }];
  const generalResources = [{ title: "General learning principles", type: "guide" }];

  return (
    <main style={{ padding: "2rem" }}>
      <h1 className="headline">Resources</h1>
      {!hasRoadmap ? (
        <Card>
          <p>Resources will be tailored to your active skill once a roadmap is generated.</p>
          <ul>
            {generalResources.map((resource) => <li key={resource.title}>{resource.title}</li>)}
          </ul>
        </Card>
      ) : (
        <div className="resource-list">
          <Card>
            <h2>Current technique first</h2>
            <p className="small-copy">{currentSkill.skillName} / {roadmapState.currentPhase} / {roadmapState.currentTechnique}</p>
            <ul>{techniqueResources.map((resource) => <li key={resource.title}>{resource.title}</li>)}</ul>
          </Card>
          <Card>
            <h2>Phase-level resources</h2>
            <ul>{phaseResources.map((resource) => <li key={resource.title}>{resource.title}</li>)}</ul>
          </Card>
          <Card>
            <h2>General skill resources</h2>
            <ul>{generalResources.map((resource) => <li key={resource.title}>{resource.title}</li>)}</ul>
          </Card>
        </div>
      )}
    </main>
  );
}
