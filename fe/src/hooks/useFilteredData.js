import { useMemo } from 'react';
import { filterIncidents } from '../utils/incidentFilters';

export function useFilteredData(incidents, filters, bounds) {
  return useMemo(() => filterIncidents(incidents, filters, bounds), [incidents, filters, bounds]);
}
