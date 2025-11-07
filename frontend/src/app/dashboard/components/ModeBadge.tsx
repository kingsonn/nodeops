'use client';

/**
 * Mode Badge Component
 * Shows current mode (Demo/Wallet) with visual indicator
 */

import { useStore } from '@/lib/store';
import { useHydrated } from '@/lib/hooks/useHydrated';

export default function ModeBadge() {
  const hydrated = useHydrated();
  const { mode } = useStore();

  // Show loading shimmer during hydration
  if (!hydrated) {
    return (
      <div className="animate-pulse px-3 py-1 bg-white/5 rounded-full">
        <div className="h-4 w-32 bg-white/10 rounded"></div>
      </div>
    );
  }

  return (
    <div
      className={`text-xs px-3 py-1 rounded-full border ${
        mode === 'wallet'
          ? 'bg-green-900/40 text-green-300 border-green-500/40'
          : 'bg-blue-900/40 text-blue-300 border-blue-500/40'
      }`}
    >
      {mode === 'wallet' ? '🦊 Wallet Mode Active' : '🧪 Demo Mode Active'}
    </div>
  );
}
