/**
 * Global State Management with Zustand
 * Single source of truth for wallet and mode state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface TokenBalances {
  [symbol: string]: number;
}

export interface NetworkInfo {
  chainId: number;
  name: string;
}

export type WalletMode = 'demo' | 'wallet';

interface AppState {
  // Core state
  mode: WalletMode;
  walletAddress: string | null;
  demoWallet: string;
  
  // Additional state
  riskPreference: 'low' | 'medium' | 'high';
  tokenBalances: TokenBalances;
  network: NetworkInfo | null;
  isLoadingBalances: boolean;
  
  // Hydration state
  _hasHydrated: boolean;
  setHasHydrated: (value: boolean) => void;
  
  // Actions
  setMode: (mode: WalletMode) => void;
  setWalletAddress: (address: string | null) => void;
  clearWallet: () => void;
  setRiskPreference: (risk: 'low' | 'medium' | 'high') => void;
  setTokenBalances: (balances: TokenBalances) => void;
  setNetwork: (network: NetworkInfo | null) => void;
  setLoadingBalances: (loading: boolean) => void;
  
  // Computed getters
  getActiveWallet: () => string;
  isConnected: () => boolean;
  isDemoMode: () => boolean;
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      mode: 'demo',
      walletAddress: null,
      demoWallet: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
      riskPreference: 'medium',
      tokenBalances: {},
      network: null,
      isLoadingBalances: false,
      
      // Hydration state
      _hasHydrated: false,
      setHasHydrated: (value: boolean) => {
        set({ _hasHydrated: value });
      },
      
      // Actions
      setMode: (mode: WalletMode) => {
        set({ mode });
        // Clear balances when switching modes
        if (mode === 'demo') {
          set({ 
            tokenBalances: {},
            network: { chainId: 1, name: 'Ethereum Mainnet' },
          });
        }
      },
      
      setWalletAddress: (address: string | null) => {
        set({ walletAddress: address });
        // Auto-switch to wallet mode when address is set
        if (address) {
          set({ mode: 'wallet' });
        }
      },
      
      clearWallet: () => {
        set({ 
          mode: 'demo',
          walletAddress: null,
          tokenBalances: {},
          network: null,
          isLoadingBalances: false,
        });
      },
      
      setRiskPreference: (risk: 'low' | 'medium' | 'high') => {
        set({ riskPreference: risk });
      },
      
      setTokenBalances: (balances: TokenBalances) => {
        set({ tokenBalances: balances });
      },
      
      setNetwork: (network: NetworkInfo | null) => {
        set({ network });
      },
      
      setLoadingBalances: (loading: boolean) => {
        set({ isLoadingBalances: loading });
      },
      
      // Computed getters
      getActiveWallet: () => {
        const state = get();
        return state.mode === 'demo' ? state.demoWallet : (state.walletAddress || state.demoWallet);
      },
      
      isConnected: () => {
        const state = get();
        return state.mode === 'wallet' ? !!state.walletAddress : true;
      },
      
      isDemoMode: () => {
        return get().mode === 'demo';
      },
    }),
    {
      name: 'autodefi-state',
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

// Legacy export for backward compatibility
export const useWalletStore = useStore;
