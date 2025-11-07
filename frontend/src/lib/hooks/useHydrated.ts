/**
 * useHydrated Hook
 * 
 * Prevents hydration mismatches by ensuring components only render
 * client-specific content after the initial mount
 */

import { useEffect, useState } from 'react';

export const useHydrated = () => {
  const [hydrated, setHydrated] = useState(false);
  
  useEffect(() => {
    setHydrated(true);
  }, []);
  
  return hydrated;
};
