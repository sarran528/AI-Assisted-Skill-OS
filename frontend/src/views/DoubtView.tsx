import { useEffect, useState } from 'react';
import { useSessionStore } from '../store/sessionStore';
import { doubtApi } from '../api/doubtApi';
import { BrutalCard as Card, CardContent, CardHeader, CardTitle } from '../components/brutal/BrutalCard';
import { BrutalButton as Button } from '../components/brutal/BrutalButton';
import { Input } from '../components/ui/Input';

export function DoubtView() {
  const session = useSessionStore((state) => state.session);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<{ explanation: string; sources_used: number } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAskDoubt = async () => {
    if (!session || !query) return;

    setLoading(true);
    try {
      const res = await doubtApi.askDoubt({
        session_id: session.session_id,
        phase: 'current', // TODO: get from session
        technique_id: 'current', // TODO: get from session
        user_query: query,
      });
      setResponse(res.data);
      setQuery('');
    } catch (error) {
      console.error('Failed to ask doubt:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!session) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>No Active Session</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Start a session to ask doubts about your learning content.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8 p-8 max-w-2xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">Ask a Doubt</h1>
        <p className="text-muted-foreground">Get AI-assisted explanations for your questions</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Question</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            textarea
            placeholder="Ask your question about the current technique..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
          />
          <Button onClick={handleAskDoubt} disabled={!query || loading} className="w-full">
            {loading ? 'Thinking...' : 'Get Explanation'}
          </Button>
        </CardContent>
      </Card>

      {response && (
        <Card>
          <CardHeader>
            <CardTitle>AI Response</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="whitespace-pre-wrap">{response.explanation}</p>
            <p className="text-sm text-muted-foreground">
              Based on {response.sources_used} source(s)
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
