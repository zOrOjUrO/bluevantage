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
    if (map.current) return; // Initialize once

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [5.2, 52.8], // Urk, Netherlands
      zoom: 8
    });

    map.current.on('load', () => {
      // Add H3 hexagon layer
      map.current.addSource('zones', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: []
        }
      });

      // Fill layer (colored by zone score)
      map.current.addLayer({
        id: 'zones-fill',
        type: 'fill',
        source: 'zones',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'zonescore'],
            0, '#ef4444',    // Red (low score)
            50, '#fbbf24',   // Yellow (medium)
            80, '#22c55e'    // Green (high score)
          ],
          'fill-opacity': 0.6
        }
      });

      // Outline layer
      map.current.addLayer({
        id: 'zones-outline',
        type: 'line',
        source: 'zones',
        paint: {
          'line-color': '#0891b2',
          'line-width': 2
        }
      });

      // MPA hatched pattern layer
      map.current.addLayer({
        id: 'mpa-zones',
        type: 'fill',
        source: 'zones',
        filter: ['==', ['get', 'ismpa'], true],
        paint: {
          'fill-color': '#dc2626',
          'fill-opacity': 0.8
        }
      });

      // Click handler
      map.current.on('click', 'zones-fill', (e) => {
        const zone = e.features[0].properties;
        setSelectedZone(JSON.parse(zone.data));
      });

      // Change cursor on hover
      map.current.on('mouseenter', 'zones-fill', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'zones-fill', () => {
        map.current.getCanvas().style.cursor = '';
      });
    });
  }, []);

  // Update zones when data loads
  useEffect(() => {
    if (!zonesData || !map.current) return;

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
          data: JSON.stringify(zone) // Store full data for click
        }
      };
    });

    map.current.getSource('zones').setData({
      type: 'FeatureCollection',
      features
    });
  }, [zonesData]);

  return (
    <div className="relative w-full h-screen">
      <div ref={mapContainer} className="w-full h-full" />
      
      {/* Port Selector */}
      <select 
        value={selectedPort} 
        onChange={(e) => setSelectedPort(e.target.value)}
        className="absolute top-4 left-4 bg-white p-2 rounded shadow-lg border border-gray-200 font-semibold text-gray-700 hover:shadow-xl transition-shadow z-10"
      >
        <option value="Urk">Urk</option>
        <option value="Scheveningen">Scheveningen</option>
        <option value="IJmuiden">IJmuiden</option>
      </select>
      
      {/* Zone Detail Card */}
      <ZoneDetailCard 
        zone={selectedZone} 
        onClose={() => setSelectedZone(null)} 
      />
    </div>
  );
}