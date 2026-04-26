import { useState, useEffect } from 'react';
import OnboardingWizard from './components/OnboardingWizard';
import ZoneMap from './components/ZoneMap';

function App() {
  const [fisherProfile, setFisherProfile] = useState(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const profileId = localStorage.getItem('fisher_profile_id');
    setShowOnboarding(!profileId);
    if (profileId) {
      setFisherProfile({ id: profileId });
    }
  }, []);

  return (
    <>
      <ZoneMap fisherProfile={fisherProfile} />
      {showOnboarding && (
        <OnboardingWizard
          onComplete={(profile) => {
            setFisherProfile(profile);
            setShowOnboarding(false);
          }}
        />
      )}
    </>
  );
}

export default App;
