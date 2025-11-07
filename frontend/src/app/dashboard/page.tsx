'use client';

/**
 * Dashboard Page
 * Main dashboard with Portfolio, AI Analysis, and Simulation tabs
 */

import { useState } from 'react';
import { useStore } from '@/lib/store';
import WalletConnect from './components/WalletConnect';
import WalletOverview from './components/WalletOverview';
import ModeToggle from './components/ModeToggle';
import ModeBadge from './components/ModeBadge';
import PortfolioTab from './components/PortfolioTab';
import AnalysisTab from './components/AnalysisTab';
import VaultsTab from './components/VaultsTab';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Toaster } from 'sonner';

export default function Dashboard() {
  const { getActiveWallet, isConnected } = useStore();
  const wallet = getActiveWallet();
  const connected = isConnected();
  const [activeTab, setActiveTab] = useState('portfolio');

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-slate-900">
      <Toaster position="top-right" />
      
      {/* Header */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">AutoDeFi.AI Dashboard</h1>
              <p className="text-sm text-blue-300">AI-Powered Portfolio Management</p>
            </div>
            <div className="flex items-center gap-4">
              <ModeBadge />
              <ModeToggle />
              <WalletConnect />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        {!connected ? (
          <Card className="p-12 text-center bg-white/10 backdrop-blur-lg border-white/20">
            <h2 className="text-2xl font-bold text-white mb-4">Connect Your Wallet</h2>
            <p className="text-blue-200 mb-6">
              Connect your wallet to view your portfolio and access AI-powered insights
            </p>
            <WalletConnect />
          </Card>
        ) : (
          <div className="space-y-6">
            {/* Wallet Overview - On-Chain Balances */}
            <WalletOverview />

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="bg-white/10 backdrop-blur-lg border border-white/20">
                <TabsTrigger value="portfolio" className="data-[state=active]:bg-purple-600">
                  Portfolio
                </TabsTrigger>
                <TabsTrigger value="analysis" className="data-[state=active]:bg-purple-600">
                  AI Analysis
                </TabsTrigger>
                <TabsTrigger value="vaults" className="data-[state=active]:bg-purple-600">
                  Vaults
                </TabsTrigger>
              </TabsList>

              <TabsContent value="portfolio">
                <PortfolioTab wallet={wallet!} />
              </TabsContent>

              <TabsContent value="analysis">
                <AnalysisTab wallet={wallet!} />
              </TabsContent>

              <TabsContent value="vaults">
                <VaultsTab wallet={wallet!} />
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </div>
  );
}
