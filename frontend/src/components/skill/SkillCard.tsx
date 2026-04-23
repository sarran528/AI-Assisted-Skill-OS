import { BrutalCard as Card } from '../brutal/BrutalCard';
import { BrutalButton as Button } from '../brutal/BrutalButton';
import { Badge } from '../ui/Badge';

export interface Skill {
  skill_id: string;
  name: string;
  complexity: number;
}

interface SkillCardProps {
  skill: Skill;
  onSelect: (skillId: string) => void;
}

export function SkillCard({ skill, onSelect }: SkillCardProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(skill.skill_id);
    }
  };

  return (
    <div 
      className="cursor-pointer hover:shadow-lg transition-shadow"
      tabIndex={0}
      onClick={() => onSelect(skill.skill_id)}
      onKeyDown={handleKeyDown}
      role="button"
      aria-label={`Select skill: ${skill.name}`}
    >
      <Card className="h-full">
        <div className="p-4">
          <h2 className="text-lg font-bold">{skill.name}</h2>
        </div>
        <div className="p-4 space-y-4">
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
            onClick={(e) => {
              e.stopPropagation();
              onSelect(skill.skill_id);
            }}
            aria-label={`Begin grounding for ${skill.name}`}
          >
            Begin Grounding
          </Button>
        </div>
      </Card>
    </div>
  );
}
