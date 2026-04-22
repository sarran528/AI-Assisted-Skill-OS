import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { skillApi } from '../api/skillApi';
import { useRoadmapStore } from '../store/roadmapStore';
import {
  BrutalCard as Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/brutal/BrutalCard';
import { BrutalButton as Button } from '../components/brutal/BrutalButton';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

interface Skill {
  skill_id: string;
  name: string;
  complexity: number;
}

export function SkillSelectView() {
  const navigate = useNavigate();
  const setTargetSkill = useRoadmapStore((state) => state.setTargetSkill);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    skillApi
      .listSkills()
      .then((res) => setSkills(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.skill_id.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelectSkill = (skillId: string) => {
    setTargetSkill(skillId);
    navigate(`/skill/grounding?skillId=${skillId}`);
  };

  if (loading) return <div className="p-8">Loading skills...</div>;

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Select a Skill</h1>
        <p className="text-muted-foreground">Choose a skill to begin your learning journey</p>
      </div>

      <div>
        <Input
          type="text"
          placeholder="Search skills..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((skill) => (
          <Card key={skill.skill_id} className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg">{skill.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">ID</p>
                <p className="font-mono text-sm">{skill.skill_id}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Complexity</p>
                <Badge>{skill.complexity}/10</Badge>
              </div>

              <Button
                className="w-full"
                onClick={() => handleSelectSkill(skill.skill_id)}
              >
                Begin Grounding
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center text-muted-foreground">
          No skills found matching your search.
        </div>
      )}
    </div>
  );
}
