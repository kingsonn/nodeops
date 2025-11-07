'use client';

import { useEffect } from 'react';
import { useAccount, useConnect, useDisconnect } from 'wagmi';
import { useStore } from '@/lib/store';
import { useHydrated } from '@/lib/hooks/useHydrated';
import { Button } from '@/components/ui/button';
import { Wallet, LogOut, Sparkles, RefreshCw } from 'lucide-react';
import { shortenAddress } from '@/lib/utils';
import { toast } from 'sonner';
import { isMetaMaskAvailable } from '@/lib/wallet';
import { api } from '@/lib/api';
import { 
  getTokenBalances, 
  getNetworkInfo, 
  getCachedBalances, 
  cacheBalances,
  clearBalanceCache,
  MAINNET_TOKENS 
} from '@/lib/balanceFetcher';

export default function WalletConnect() {
  const hydrated = useHydrated();
  const { 
    walletAddress,
    mode,
    isLoadingBalances,
    setWalletAddress,
    clearWallet,
    setMode,
    setTokenBalances,
    setNetwork,
    setLoadingBalances,
    getActiveWallet,
    isDemoMode,
  } = useStore();
  
  // Wagmi hooks
  const { address, isConnected: wagmiConnected } = useAccount();
  const { connect, connectors, isPending } = useConnect();
  const { disconnect, disconnectAsync } = useDisconnect();

  // Sync wagmi state with Zustand store
  useEffect(() => {
    if (wagmiConnected && address && !isDemoMode()) {
      if (walletAddress !== address) {
        setWalletAddress(address);
        toast.success(`✅ Connected to MetaMask`);
        
        // Auto-sync with Supabase
        syncWalletWithBackend(address);
        
        // Fetch on-chain balances
        fetchBalances(address);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wagmiConnected, address, walletAddress, setWalletAddress]);

  // Sync wallet with backend (create user if needed)
  const syncWalletWithBackend = async (walletAddress: string) => {
    try {
      console.log(`👛 New wallet connected: ${walletAddress}`);
      
      // Call demo endpoint to ensure user exists
      await api.portfolio.loadDemo(walletAddress);
      
      console.log(`🗂 User auto-created/verified in Supabase`);
    } catch (error) {
      console.error('Failed to sync wallet with backend:', error);
    }
  };

  // Fetch on-chain balances
  const fetchBalances = async (walletAddress: string) => {
    try {
      // Check cache first
      const cached = getCachedBalances(walletAddress);
      if (cached) {
        console.log('📦 Using cached balances');
        setTokenBalances(cached);
        
        // Still fetch network info
        const networkInfo = await getNetworkInfo();
        if (networkInfo) {
          setNetwork(networkInfo);
        }
        return;
      }

      setLoadingBalances(true);
      toast.info('🔄 Fetching on-chain balances...');
      
      // Fetch network info and balances in parallel
      const [networkInfo, balances] = await Promise.all([
        getNetworkInfo(),
        getTokenBalances(walletAddress, MAINNET_TOKENS),
      ]);
      
      if (networkInfo) {
        setNetwork(networkInfo);
        console.log(`🌐 Connected to ${networkInfo.name}`);
      }
      
      setTokenBalances(balances);
      cacheBalances(walletAddress, balances);
      
      const totalTokens = Object.keys(balances).length;
      toast.success(`✅ Fetched ${totalTokens} token balances`);
      
      console.log('💰 Token balances:', balances);
    } catch (error) {
      console.error('Failed to fetch balances:', error);
      toast.error('Failed to fetch on-chain balances');
    } finally {
      setLoadingBalances(false);
    }
  };

  // Refresh balances manually
  const handleRefreshBalances = async () => {
    const wallet = getActiveWallet();
    if (!wallet || isDemoMode()) return;
    
    clearBalanceCache();
    await fetchBalances(wallet);
  };

  const handleConnectMetaMask = async () => {
    if (!isMetaMaskAvailable()) {
      toast.warning('🦊 MetaMask not detected. Install MetaMask to use Wallet Mode.');
      setMode('demo');
      return;
    }

    try {
      // Find injected connector (MetaMask)
      const injectedConnector = connectors.find(c => c.id === 'injected' || c.type === 'injected');
      if (injectedConnector) {
        connect({ connector: injectedConnector });
        // Mode will be set to 'wallet' in the useEffect when address is received
      } else {
        // Fallback: use first available connector
        if (connectors.length > 0) {
          connect({ connector: connectors[0] });
        } else {
          throw new Error('No connectors available');
        }
      }
    } catch (error) {
      console.error('MetaMask connection error:', error);
      toast.error('Failed to connect MetaMask');
      // Fallback to demo mode on error
      setMode('demo');
    }
  };

  const handleDisconnect = async () => {
    try {
      // Use disconnectAsync for proper async handling
      if (!isDemoMode() && wagmiConnected) {
        await disconnectAsync();
      }
    } catch (error) {
      console.warn('Disconnect error:', error);
    } finally {
      // Always clear state, even if disconnect fails
      clearBalanceCache();
      clearWallet();
      toast.info('\ud83d\udd0c Disconnected - Switched to Demo Mode');
    }
  };

  const handleDemoMode = () => {
    if (mode === 'wallet') {
      // Disconnect wallet first if connected
      if (wagmiConnected) {
        handleDisconnect();
      } else {
        clearWallet();
      }
    }
    setMode('demo');
    toast.success('🧪 Demo Mode activated');
  };

  // Show loading shimmer during hydration
  if (!hydrated) {
    return (
      <div className="animate-pulse px-4 py-2 bg-white/5 rounded-lg">
        <div className="h-4 w-32 bg-white/10 rounded"></div>
      </div>
    );
  }

  const wallet = getActiveWallet();
  const storeConnected = mode === 'wallet' ? !!walletAddress : true;
  
  if (storeConnected && wallet) {
    return (
      <div className="flex items-center gap-3">
        {isDemoMode() && (
          <div className="px-3 py-1 bg-yellow-500/20 rounded-lg border border-yellow-500/50">
            <div className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-yellow-400" />
              <span className="text-yellow-300 text-xs font-semibold">Demo</span>
            </div>
          </div>
        )}
        <div className="px-4 py-2 bg-white/10 backdrop-blur-lg rounded-lg border border-white/20">
          <div className="flex items-center gap-2">
            <Wallet className="w-4 h-4 text-purple-400" />
            <span className="text-white font-mono text-sm">{shortenAddress(wallet)}</span>
          </div>
        </div>
        {!isDemoMode && (
          <Button
            onClick={handleRefreshBalances}
            variant="outline"
            size="sm"
            disabled={isLoadingBalances}
            className="bg-blue-500/20 border-blue-500/50 text-blue-300 hover:bg-blue-500/30"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingBalances ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        )}
        <Button
          onClick={handleDisconnect}
          variant="outline"
          size="sm"
          className="bg-red-500/20 border-red-500/50 text-red-300 hover:bg-red-500/30"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Disconnect
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Button
        onClick={handleConnectMetaMask}
        disabled={isPending}
        className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
      >
        <Wallet className="w-4 h-4 mr-2" />
        {isPending ? 'Connecting...' : 'Connect MetaMask'}
      </Button>
      <Button
        onClick={handleDemoMode}
        variant="outline"
        size="sm"
        className="bg-yellow-500/20 border-yellow-500/50 text-yellow-300 hover:bg-yellow-500/30"
      >
        <Sparkles className="w-4 h-4 mr-2" />
        Demo Mode
      </Button>
    </div>
  );
}
