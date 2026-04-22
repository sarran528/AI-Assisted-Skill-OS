import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { skillApi } from '../api/skillApi';
import { useRoadmapStore } from '../store/roadmapStore';
import { BrutalCard as Card, CardContent, CardHeader, CardTitle } from '../components/brutal/BrutalCard';
import { BrutalButton as Button } from '../components/brutal/BrutalButton';
import { Input } from '../components/ui/Input';

export function GroundingView() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const skillId = searchParams.get('skillId');
  const setBaseline = useRoadmapStore((state) => state.setBaseline);

  const [step, setStep] = useState<'recognition' | 'declarative' | 'confidence'>('recognition');
  const [scores, setScores] = useState({
    recognition_score: 0.5,
    declarative_score: 0.5,
    confidence_bias: 2.5,
  });
  const [loading, setLoading] = useState(false);

  const handleNext = async () => {
    if (step === 'recognition') {
      setStep('declarative');
    } else if (step === 'declarative') {
      setStep('confidence');
    } else {
      // Submit
      setLoading(true);
      try {
        const res = await skillApi.submitBaseline({
          skill_id: skillId!,
          recognition_score: scores.recognition_score,
          declarative_score: scores.declarative_score,
          confidence_bias: scores.confidence_bias,
        });
        setBaseline(res.data);
        navigate('/roadmap/generate');
      } catch (error) {
        console.error('Failed to submit baseline:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const steps = {
    recognition: {
      title: 'Recognition Score',
      description: 'How well do you recognize this skill in real-world contexts?',
      max: 1,
      step: 0.1,
    },
    declarative: {
      title: 'Declarative Score',
      description: 'How much can you explain the theory and concepts?',
      max: 1,
      step: 0.1,
    },
    confidence: {
      title: 'Confidence Bias',
      description: 'How confident are you in your current abilities? (1-5 scale)',
      max: 5,
      step: 0.5,
    },
  };

  const currentStep = steps[step];
  const scoreKey = {
    recognition: 'recognition_score',
    declarative: 'declarative_score',
    confidence: 'confidence_bias',
  }[step] as keyof typeof scores;

  return (
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{currentStep.title}</CardTitle>
          <p className="text-sm text-muted-foreground">{currentStep.description}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <div className="mb-4 text-3xl font-bold text-center">
              {scores[scoreKey].toFixed(1)} / {currentStep.max}
            </div>
            <Input
              type="range"
              value={scores[scoreKey]}
              onChange={(e) =>
                setScores({ ...scores, [scoreKey]: parseFloat(e.target.value) })
              }
              min={0}
              max={currentStep.max}
              step={currentStep.step}
              className="w-full"
            />
          </div>

          <div className="flex gap-4">
            <Button
              variant="outline"
              onClick={() => {
                if (step === 'recognition') navigate('/skill/select');
                else if (step === 'declarative') setStep('recognition');
                else setStep('declarative');
              }}
            >
              Back
            </Button>
            <Button
              className="flex-1"
              onClick={handleNext}
              disabled={loading}
            >
              {step === 'confidence' ? 'Complete Grounding' : 'Next'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}