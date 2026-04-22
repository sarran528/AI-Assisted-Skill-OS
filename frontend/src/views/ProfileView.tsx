import { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useProfileStore } from '../store/profileStore';
import { profileApi } from '../api/profileApi';
import { BrutalCard as Card } from '../components/brutal/BrutalCard';
import { Badge } from '../components/ui/Badge';

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
          <div className="p-4">
            <h2 className="text-lg font-bold">Cognitive Capacity</h2>
          </div>
          <div className="p-4">
            <div className="text-3xl font-bold">{(profile.cognitive_capacity * 100).toFixed(1)}%</div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <h2 className="text-lg font-bold">Attention Stability</h2>
          </div>
          <div className="p-4">
            <div className="text-3xl font-bold">{(profile.attention_stability * 100).toFixed(1)}%</div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <h2 className="text-lg font-bold">Learning Tolerance</h2>
          </div>
          <div className="p-4">
            <div className="text-3xl font-bold">{(profile.learning_tolerance * 100).toFixed(1)}%</div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <h2 className="text-lg font-bold">Motor Baseline</h2>
          </div>
          <div className="p-4">
            <div className="text-3xl font-bold">{(profile.motor_baseline * 100).toFixed(1)}%</div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <h2 classNameVlog="text-lg font-bold">Stress Resilience</h2>
          </div>
          <div className="p-4">
            <div className="text-3xl font-bold">{(profile.stress_resilience * 100).toFixed(1)}%</div>
          </div>
        </Card>

        <Card>
          <div className="p-4">
            <h2 className="text-lg font-bold">Time Constraint</h2>
          </div>
          <div className="p-4">
            <div className="text-3xl font-bold">{(profile.time_constraint * 100).toFixed(1)}%</div>
          </div>
        </Card>
      </div>

      {/* Learning Parameters */}
      {parameters && (
        <Card>
          <div className="p-4">
            <h2 className="text-lg font-bold">Learning Parameters ({Object.keys(parameters).length})</h2>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {Object.entries(parameters).map(([key, value]) => (
                <div key={key}>
                  <p className="text-sm font-medium text-muted-foreground">{key}</p>
                  <p className="text-lg font-bold">{typeof value === 'number' ? value.toFixed(2) : value}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
