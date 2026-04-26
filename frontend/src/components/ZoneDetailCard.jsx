import React from 'react';

export default function ZoneDetailCard({ zone, onClose }) {
  if (!zone) return null;

  return (
    <div className="absolute top-4 right-4 w-96 bg-white rounded-xl shadow-2xl p-6 border border-gray-100 z-10">
      <button 
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-400 hover:text-gray-700 transition-colors"
        aria-label="Close details"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
      
      <div className="mb-5">
        <h2 className="text-xl font-bold text-gray-800">Zone Details</h2>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-sm text-gray-500">Suitability Score:</span>
          <span className={`font-bold ${zone.zonescore >= 80 ? 'text-green-600' : zone.zonescore >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
            {zone.zonescore} / 100
          </span>
        </div>
      </div>
      
      {/* Species Breakdown */}
      <div className="space-y-3 mb-6">
        <h3 className="font-semibold text-gray-700 text-sm uppercase tracking-wider">Species Probability</h3>
        <div className="space-y-3">
          {zone.species?.map((sp, i) => (
            <div key={i} className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-gray-700">{sp.name}</span>
                <span className="text-gray-900 font-bold">{(sp.prob * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${sp.prob > 0.7 ? 'bg-ocean-500' : sp.prob > 0.4 ? 'bg-ocean-500/70' : 'bg-ocean-500/40'}`}
                  style={{ width: `${sp.prob * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Yield Estimate & Distance */}
      <div className="grid grid-cols-2 gap-4 mb-6 bg-gray-50 p-4 rounded-xl border border-gray-100">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Est. Catch</p>
          <p className="text-lg font-bold text-gray-800">
            {zone.yieldlowkg}-{zone.yieldhighkg} <span className="text-sm font-normal text-gray-500">kg</span>
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Distance</p>
          <p className="text-lg font-bold text-gray-800">
            {zone.distancekm?.toFixed(1)} <span className="text-sm font-normal text-gray-500">km</span>
          </p>
        </div>
      </div>

      {/* Slots */}
      <div className="mb-6">
        <div className="flex justify-between items-end mb-2">
          <span className="text-sm font-medium text-gray-700">Zone Capacity</span>
          <span className="text-sm font-medium text-gray-900">{zone.slotsfilled} / {zone.slotstotal} <span className="text-gray-500 font-normal">vessels</span></span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${(zone.slotsfilled / zone.slotstotal) > 0.8 ? 'bg-red-500' : 'bg-green-500'}`}
            style={{ width: `${(zone.slotsfilled / zone.slotstotal) * 100}%` }}
          />
        </div>
      </div>

      {/* Weather */}
      <div className="flex gap-4 text-sm mb-6 text-ocean-700 bg-ocean-50 p-3.5 rounded-xl border border-ocean-500/20">
        <div className="flex items-center gap-2">
          <span className="text-lg" role="img" aria-label="wave">🌊</span> 
          <span className="font-medium">{zone.waveheightm}m waves</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-lg" role="img" aria-label="wind">💨</span> 
          <span className="font-medium">{zone.windkmh} km/h wind</span>
        </div>
      </div>

      {/* Action Button */}
      {zone.ismpa ? (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-start gap-3">
          <span className="text-xl">⚠️</span>
          <div className="text-sm">
            <strong className="block mb-1 font-semibold text-red-800">Marine Protected Area</strong>
            Fishing is strictly prohibited. Fines up to €50,000 apply.
          </div>
        </div>
      ) : (
        <button className="w-full bg-ocean-500 text-white py-3.5 px-4 rounded-xl font-bold hover:bg-ocean-700 transition-colors shadow-lg shadow-ocean-500/30 focus:outline-none focus:ring-2 focus:ring-ocean-500 focus:ring-offset-2">
          Reserve Fishing Zone
        </button>
      )}
    </div>
  );
}