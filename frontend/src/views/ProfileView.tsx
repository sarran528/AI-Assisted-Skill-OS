import { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useProfileStore } from '../store/profileStore';
import { profileApi } from '../api/profileApi';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

export function ProfileView() {
  const user = useAuthStore((state) => state.user);
  const profile = useProfileStore((state) => state.profile);
  const parameters = useProfileStore((state) => state.parameters);
  const setProfile = useProfileStore((state) => state.setProfile);
  const setParameters = useProfileStore((state) => state.setParameters);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user?.id) return;
    if (profile) return;

    setLoading(true);
    Promise.all([
      profileApi.getProfile(user.id),
      profileApi.getParameters(user.id),
    ])
      .then(([profileRes, paramsRes]) => {
        setProfile(profileRes.data);
        setParameters(paramsRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user?.id, profile, setProfile, setParameters]);

  if (loading) return <div className="p-8">Loading profile...</div>;
  if (!profile) return <div className="p-8">No profile data available</div>;

  return (
    <div className="space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold">Cognitive Profile</h1>
        <p className="text-muted-foreground">Version {profile.version}</p>
      </div>

      {/* Profile Dimensions */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cognitive Capacity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{(profile.cognitive_capacity * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Attention Stability</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{(profile.attention_stability * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Learning Tolerance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{(profile.learning_tolerance * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Motor Baseline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{(profile.motor_baseline * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Stress Resilience</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{(profile.stress_resilience * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Time Constraint</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{(profile.time_constraint * 100).toFixed(1)}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Learning Parameters */}
      {parameters && (
        <Card>
          <CardHeader>
            <CardTitle>Learning Parameters ({Object.keys(parameters).length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {Object.entries(parameters).map(([key, value]) => (
                <div key={key}>
                  <p className="text-sm font-medium text-muted-foreground">{key}</p>
                  <p className="text-lg font-bold">{typeof value === 'number' ? value.toFixed(2) : value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
