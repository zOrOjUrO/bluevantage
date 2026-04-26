import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export function useZones(selectedPort = null) {
  return useQuery({
    queryKey: ['zones', selectedPort],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/zones`, {
        params: selectedPort ? { port: selectedPort } : undefined
      });
      return res.data.zones;
    }
  });
}
