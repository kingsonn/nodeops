'use client';

/**
 * Wallet Overview Component
 * 
 * Displays on-chain token balances and network information
 * for connected MetaMask wallets
 */

import { useWalletStore } from '@/lib/store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Wallet, Network, Loader2 } from 'lucide-react';

export default function WalletOverview() {
  const { walletAddress, isDemoMode, tokenBalances, network, isLoadingBalances } = useWalletStore();

  // Don't show for demo mode or if not connected
  if (!walletAddress || isDemoMode()) {
    return null;
  }

  // Show message if not connected
  if (!network) {
    return (
      <Card className="bg-white/5 backdrop-blur-lg border-white/10">
        <CardContent className="p-6">
          <p className="text-blue-300 text-sm text-center">
            Connect wallet to view on-chain balances
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 backdrop-blur-lg border-blue-500/20">
      <CardHeader>
        <CardTitle className="text-lg text-white flex items-center gap-2">
          <Wallet className="w-5 h-5 text-blue-400" />
          On-Chain Balances
        </CardTitle>
        <CardDescription className="text-blue-300 flex items-center gap-2">
          <Network className="w-4 h-4" />
          {network.name}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoadingBalances ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
            <span className="ml-2 text-blue-300">Fetching balances...</span>
          </div>
        ) : Object.keys(tokenBalances).length === 0 ? (
          <p className="text-blue-300 text-sm text-center py-4">
            No balances available
          </p>
        ) : (
          <div className="space-y-2">
            {Object.entries(tokenBalances)
              .sort(([, a], [, b]) => b - a) // Sort by balance descending
              .map(([symbol, balance]) => (
                <div
                  key={symbol}
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">
                        {symbol.substring(0, 2)}
                      </span>
                    </div>
                    <span className="text-white font-medium">{symbol}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-mono text-sm">
                      {balance.toFixed(4)}
                    </div>
                    {balance > 0 && (
                      <div className="text-blue-300 text-xs">
                        {balance < 0.0001 ? '< 0.0001' : balance.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
          </div>
        )}

        <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
          <p className="text-xs text-blue-300">
            💡 <strong>Read-Only:</strong> These are your actual on-chain balances. No funds will be moved or approvals requested.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
