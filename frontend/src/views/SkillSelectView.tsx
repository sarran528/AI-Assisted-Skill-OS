import { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { skillApi } from '../api/skillApi';
import { useRoadmapStore } from '../store/roadmapStore';
import { SkillCard, Skill } from '../components/skill/SkillCard';
import { Input } from '../components/ui/Input';

// Type safety for API responses
interface SkillApiResponse {
  data: Skill[];
}

// Custom debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function SkillSelectView() {
  const navigate = useNavigate();
  const setTargetSkill = useRoadmapStore((state) => state.setTargetSkill);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Debounce search input for performance
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    skillApi
      .listSkills()
      .then((res: SkillApiResponse) => {
        setSkills(res.data);
        setError(null);
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to load skills. Please try again later.');
      })
      .finally(() => setLoading(false));
  }, []);

  // Memoize filtered skills for performance
  const filtered = useMemo(
    () =>
      skills.filter(
        (s) =>
          s.name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
          s.skill_id.toLowerCase().includes(debouncedSearch.toLowerCase())
      ),
    [skills, debouncedSearch]
  );

  // Memoize select skill handler
  const handleSelectSkill = useCallback((skillId: string) => {
    setTargetSkill(skillId);
    navigate(`/skill/grounding?skillId=${skillId}`);
  }, [navigate, setTargetSkill]);

  if (loading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Loading skills...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 flex justify-center items-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-500 text-lg mb-2">⚠️ Error</div>
          <p className="text-red-500">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

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
          aria-label="Search skills"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((skill) => (
          <SkillCard key={skill.skill_id} skill={skill} onSelect={handleSelectSkill} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center text-muted-foreground py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-lg font-semibold mb-2">No skills found</h3>
          <p>No skills found matching your search.</p>
          {search && (
            <button
              onClick={() => setSearch('')}
              className="mt-4 text-primary hover:underline"
            >
              Clear search
            </button>
          )}
        </div>
      )}
    </div>
  );
}
