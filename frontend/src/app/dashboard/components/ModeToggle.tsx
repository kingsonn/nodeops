'use client';

/**
 * Mode Toggle Component
 * 
 * Allows users to switch between Demo Mode and Real Wallet Mode
 * Automatically opens RainbowKit modal when switching to Wallet Mode
 */

import { useEffect, useState } from 'react';
import { useConnectModal } from '@rainbow-me/rainbowkit';
import { useAccount, useDisconnect } from 'wagmi';
import { useStore } from '@/lib/store';
import { useHydrated } from '@/lib/hooks/useHydrated';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function ModeToggle() {
  const hydrated = useHydrated();
  const { openConnectModal } = useConnectModal();
  const { disconnectAsync } = useDisconnect();
  const { address, isConnected } = useAccount();
  const { mode, setMode, setWalletAddress, clearWallet } = useStore();

  // Check if MetaMask is available (client-side only)
  const [hasMetaMask, setHasMetaMask] = useState(false);
  
  useEffect(() => {
    setHasMetaMask(typeof window !== 'undefined' && !!window.ethereum);
  }, []);

  // Auto-sync wallet connection state with store
  useEffect(() => {
    if (isConnected && address) {
      setWalletAddress(address);
      setMode('wallet');
    }
  }, [isConnected, address, setWalletAddress, setMode]);

  // Show loading shimmer during hydration
  if (!hydrated) {
    return (
      <div className="animate-pulse px-4 py-2 bg-white/5 rounded-lg">
        <div className="h-4 w-24 bg-white/10 rounded"></div>
      </div>
    );
  }

  // If MetaMask not available, show disabled state
  if (!hasMetaMask) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 opacity-70">
        <span className="text-blue-300 text-sm">
          🦊 MetaMask not detected — Demo Mode only
        </span>
      </div>
    );
  }

  const handleToggle = async () => {
    if (mode === 'demo') {
      // Switching from demo to wallet
      if (!isConnected) {
        toast.info('🦊 Connecting wallet...');
        openConnectModal?.();
      } else {
        setMode('wallet');
        setWalletAddress(address!);
        toast.success('✅ Wallet mode activated');
      }
    } else {
      // Switching from wallet to demo
      try {
        await disconnectAsync();
      } catch (error) {
        console.warn('Disconnect error:', error);
      } finally {
        clearWallet();
        toast.info('🔌 Disconnected — switched to Demo Mode');
      }
    }
  };

  return (
    <Button
      onClick={handleToggle}
      variant="outline"
      size="sm"
      className={
        mode === 'demo'
          ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300 hover:bg-yellow-500/30'
          : 'bg-green-500/20 border-green-500/50 text-green-300 hover:bg-green-500/30'
      }
    >
      {mode === 'demo' ? '🦊 Switch to Wallet' : '🧪 Switch to Demo'}
    </Button>
  );
}
