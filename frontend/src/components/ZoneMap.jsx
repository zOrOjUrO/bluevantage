import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { cellToBoundary } from 'h3-js';
import { useZones } from '../hooks/useZones';
import ZoneDetailCard from './ZoneDetailCard';

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

export default function ZoneMap() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [selectedZone, setSelectedZone] = useState(null);
  const [selectedPort, setSelectedPort] = useState('Urk');

  // Fetch zones from your API
  const { data: zonesData } = useZones(selectedPort);

  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [5.2, 52.8],
      zoom: 8
    });

    map.current.on('load', () => {
      map.current.addSource('zones', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      map.current.addLayer({
        id: 'zones-fill',
        type: 'fill',
        source: 'zones',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'zonescore'],
            0, '#ef4444',
            50, '#fbbf24',
            80, '#22c55e'
          ],
          'fill-opacity': 0.6
        }
      });

      map.current.addLayer({
        id: 'zones-outline',
        type: 'line',
        source: 'zones',
        paint: {
          'line-color': '#0891b2',
          'line-width': 2
        }
      });

      map.current.on('click', 'zones-fill', (e) => {
        const zone = JSON.parse(e.features[0].properties.data);
        setSelectedZone(zone);
      });

      map.current.on('mouseenter', 'zones-fill', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', 'zones-fill', () => {
        map.current.getCanvas().style.cursor = '';
      });
    });
  }, []);

  useEffect(() => {
    if (!zonesData || !map.current || !map.current.isStyleLoaded()) return;

    const features = zonesData.map(zone => {
      const boundary = cellToBoundary(zone.hexid, true);
      return {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [boundary]
        },
        properties: {
          zonescore: zone.zonescore,
          ismpa: zone.ismpa,
          data: JSON.stringify(zone)
        }
      };
    });
    
    const source = map.current.getSource('zones');
    if (source) {
      source.setData({ type: 'FeatureCollection', features });
    }
  }, [zonesData]);

  return (
    <div className="relative w-full h-full min-h-[600px]">
      <div ref={mapContainer} className="absolute inset-0" />
      
      <select 
        value={selectedPort} 
        onChange={(e) => setSelectedPort(e.target.value)}
        className="absolute top-4 left-4 bg-white p-2 rounded shadow-lg border border-gray-200 font-semibold text-gray-700 z-10"
      >
        <option value="Urk">Urk</option>
        <option value="Scheveningen">Scheveningen</option>
        <option value="IJmuiden">IJmuiden</option>
      </select>

      {selectedZone && (
        <ZoneDetailCard 
          zone={selectedZone} 
          onClose={() => setSelectedZone(null)} 
        />
      )}
    </div>
  );
}
