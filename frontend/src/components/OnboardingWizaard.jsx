import { useState } from 'react';
import { supabase } from '../lib/supabase';

export default function OnboardingWizard({ onComplete }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    home_port_id: null,
    vessel_type: '',
    target_species: [],
    telegram_enabled: false
  });

  const ports = [
    { id: 1, name: 'Urk' },
    { id: 2, name: 'Scheveningen' },
    { id: 3, name: 'IJmuiden' },
    { id: 4, name: 'Den Helder' },
    { id: 5, name: 'Stellendam' }
  ];

  const speciesOptions = ['Plaice', 'Sole', 'Cod', 'Herring', 'Mackerel'];

  const handleSubmit = async () => {
    if (!supabase) {
      alert('Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env');
      return;
    }

    const { data, error } = await supabase
      .from('fisher_profiles')
      .insert([formData])
      .select();

    if (error) {
      alert('Error creating profile: ' + error.message);
    } else {
      localStorage.setItem('fisher_profile_id', data[0].id);
      onComplete(data[0]);
    }
  };

  if (step === 1) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold mb-4">Welcome to BlueVantage</h2>
          <p className="text-gray-600 mb-6">Let's set up your fishing profile</p>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Your Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full border rounded p-2"
                placeholder="Jan Visser"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full border rounded p-2"
                placeholder="jan@example.com"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Telegram Chat ID</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full border rounded p-2"
                placeholder="123456789 (or @username)"
              />
            </div>
          </div>
          
          <button
            onClick={() => setStep(2)}
            className="w-full bg-cyan-500 text-white py-3 rounded mt-6 font-semibold"
          >
            Next →
          </button>
        </div>
      </div>
    );
  }

  if (step === 2) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold mb-4">Vessel Details</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Home Port</label>
              <select
                value={formData.home_port_id || ''}
                onChange={(e) => setFormData({...formData, home_port_id: parseInt(e.target.value)})}
                className="w-full border rounded p-2"
              >
                <option value="">Select port...</option>
                {ports.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Vessel Type</label>
              <select
                value={formData.vessel_type}
                onChange={(e) => setFormData({...formData, vessel_type: e.target.value})}
                className="w-full border rounded p-2"
              >
                <option value="">Select type...</option>
                <option value="beam_trawl">Beam Trawl</option>
                <option value="otter_trawl">Otter Trawl</option>
                <option value="gillnet">Gillnet</option>
              </select>
            </div>
          </div>
          
          <div className="flex gap-2 mt-6">
            <button
              onClick={() => setStep(1)}
              className="flex-1 border border-gray-300 py-3 rounded font-semibold"
            >
              ← Back
            </button>
            <button
              onClick={() => setStep(3)}
              className="flex-1 bg-cyan-500 text-white py-3 rounded font-semibold"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold mb-4">Target Species</h2>
          <p className="text-sm text-gray-600 mb-4">Select your primary catch targets</p>
          
          <div className="space-y-2 mb-6">
            {speciesOptions.map(species => (
              <label key={species} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.target_species.includes(species.toLowerCase())}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData({
                        ...formData,
                        target_species: [...formData.target_species, species.toLowerCase()]
                      });
                    } else {
                      setFormData({
                        ...formData,
                        target_species: formData.target_species.filter(s => s !== species.toLowerCase())
                      });
                    }
                  }}
                  className="w-4 h-4"
                />
                <span>{species}</span>
              </label>
            ))}
          </div>
          
          <label className="flex items-center gap-2 p-3 bg-green-50 rounded mb-6">
            <input
              type="checkbox"
              checked={formData.telegram_enabled}
              onChange={(e) => setFormData({...formData, telegram_enabled: e.target.checked})}
              className="w-4 h-4"
            />
            <span className="text-sm">📱 Enable daily Telegram zone updates</span>
          </label>
          
          <div className="flex gap-2">
            <button
              onClick={() => setStep(2)}
              className="flex-1 border border-gray-300 py-3 rounded font-semibold"
            >
              ← Back
            </button>
            <button
              onClick={handleSubmit}
              className="flex-1 bg-gradient-to-r from-cyan-500 to-blue-600 text-white py-3 rounded font-semibold"
            >
              Complete Setup ✓
            </button>
          </div>
        </div>
      </div>
    );
  }
}
