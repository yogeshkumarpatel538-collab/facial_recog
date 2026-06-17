import { createContext, useContext } from 'react';
import { useLiveCounts } from '../hooks/useLiveCounts';

const LiveCountsContext = createContext(null);

export function LiveCountsProvider({ children }) {
  const value = useLiveCounts(true);
  return <LiveCountsContext.Provider value={value}>{children}</LiveCountsContext.Provider>;
}

export function useLiveCountsContext() {
  const ctx = useContext(LiveCountsContext);
  if (!ctx) throw new Error('useLiveCountsContext must be used within LiveCountsProvider');
  return ctx;
}
