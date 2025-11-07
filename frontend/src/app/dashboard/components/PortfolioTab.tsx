'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { api, fetcher } from '@/lib/api';
import { useStore } from '@/lib/store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, Database, TrendingUp, Plus, Trash2, Edit2, Shield, AlertCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { toast } from 'sonner';
import { normalizeHoldings, safeToFixed, safeCurrency, safePercent, NormalizedHolding } from '@/lib/normalizeHoldings';
import MarketAlerts from './MarketAlerts';

interface PortfolioTabProps {
  wallet: string;
  onAnalyze?: (wallet: string) => Promise<void>;
}

const COLORS = ['#8b5cf6', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b'];

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PortfolioTab({ wallet, onAnalyze }: PortfolioTabProps) {
  // Get mode state from store
  const { mode, walletAddress, isDemoMode } = useStore();
  
  // Compute editable state
  const isWalletConnected = Boolean(walletAddress);
  const demoMode = isDemoMode();
  const isEditable = demoMode && !isWalletConnected;
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingDemo, setIsLoadingDemo] = useState(false);
  const [risk, setRisk] = useState<string>('medium');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingHolding, setEditingHolding] = useState<number | null>(null);
  const [editAmount, setEditAmount] = useState<string>('');
  const [newHolding, setNewHolding] = useState({
    protocol_name: '',
    symbol: '',
    amount: 0
  });
  
  const { data: portfolio, error, mutate } = useSWR(
    wallet ? `/api/portfolio?wallet=${wallet}` : null,
    fetcher,
    { refreshInterval: 30000 }
  );

  // Update risk state when portfolio loads
  useEffect(() => {
    if (portfolio?.risk_preference) {
      setRisk(portfolio.risk_preference);
    }
  }, [portfolio]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await api.portfolio.refresh(wallet);
      await mutate();
      toast.success('Portfolio refreshed successfully!');
    } catch (error) {
      toast.error('Failed to refresh portfolio');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleLoadDemo = async () => {
    setIsLoadingDemo(true);
    try {
      await api.portfolio.demo();
      await mutate();
      toast.success('Demo portfolio loaded!');
    } catch (error) {
      toast.error('Failed to load demo data');
    } finally {
      setIsLoadingDemo(false);
    }
  };

  const updateRisk = async (newRisk: string) => {
    try {
      const response = await fetch(`${API_URL}/api/portfolio/risk/${wallet}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ risk_preference: newRisk }),
      });
      
      if (response.ok) {
        setRisk(newRisk);
        await mutate();
        toast.success(`💾 Risk profile updated to ${newRisk}`);
        
        // Trigger AI re-analysis
        if (onAnalyze) {
          await onAnalyze(wallet);
        }
      } else {
        toast.error('Failed to update risk profile');
      }
    } catch (error) {
      console.error('Error updating risk:', error);
      toast.error('Failed to update risk profile');
    }
  };

  const handleUpdateAmount = async (holdingId: number, newAmount: number) => {
    try {
      const response = await fetch(`${API_URL}/api/portfolio/demo/holdings/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holding_id: holdingId, amount: newAmount }),
      });
      
      if (response.ok) {
        await mutate();
        setEditingHolding(null);
        toast.success('💾 Holding updated');
        
        // Trigger AI re-analysis
        if (onAnalyze) {
          await onAnalyze(wallet);
        }
      } else {
        toast.error('Failed to update holding');
      }
    } catch (error) {
      console.error('Error updating holding:', error);
      toast.error('Failed to update holding');
    }
  };

  const handleRemove = async (holdingId: number) => {
    if (!confirm('Remove this holding?')) return;
    
    try {
      const response = await fetch(`${API_URL}/api/portfolio/demo/holdings/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holding_id: holdingId }),
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Remove response:', result);
        
        // Refresh portfolio data
        await mutate();
        
        toast.success('🗑️ Holding removed');
        
        // Trigger AI re-analysis
        if (onAnalyze) {
          await onAnalyze(wallet);
        }
      } else {
        const errorData = await response.json();
        console.error('❌ Remove failed:', errorData);
        toast.error(errorData.error?.message || errorData.message || 'Failed to remove holding');
      }
    } catch (error) {
      console.error('❌ Error removing holding:', error);
      toast.error('Failed to remove holding');
    }
  };


  const handleAddHolding = async () => {
    if (!newHolding.protocol_name || !newHolding.symbol || !newHolding.amount || newHolding.amount <= 0) {
      toast.error('Please fill in all fields with valid values');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/portfolio/demo/holdings/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet,
          protocol_name: newHolding.protocol_name,
          symbol: newHolding.symbol.toUpperCase(),
          amount: parseFloat(newHolding.amount.toString()),
        }),
      });
      
      if (response.ok) {
        await mutate();
        setShowAddModal(false);
        setNewHolding({ 
          protocol_name: '', 
          symbol: '', 
          amount: 0
        });
        toast.success('✅ Holding added successfully');
        
        // Trigger AI re-analysis
        if (onAnalyze) {
          await onAnalyze(wallet);
        }
      } else {
        const errorData = await response.json();
        toast.error(errorData.detail?.message || 'Failed to add holding');
      }
    } catch (error) {
      console.error('Error adding holding:', error);
      toast.error('Failed to add holding');
    }
  };

  const startEdit = (holding: NormalizedHolding) => {
    setEditingHolding(holding.id);
    setEditAmount(holding.amount.toString());
  };

  const cancelEdit = () => {
    setEditingHolding(null);
    setEditAmount('');
  };

  const saveEdit = async (holdingId: number) => {
    const amount = parseFloat(editAmount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    await handleUpdateAmount(holdingId, amount);
  };

  if (error) {
    return (
      <Card className="bg-red-500/10 backdrop-blur-lg border-red-500/50">
        <CardContent className="p-6">
          <p className="text-red-300">Failed to load portfolio. Please try again.</p>
        </CardContent>
      </Card>
    );
  }

  if (!portfolio) {
    return (
      <Card className="bg-white/10 backdrop-blur-lg border-white/20">
        <CardContent className="p-12 text-center">
          <div className="animate-pulse">
            <div className="w-16 h-16 bg-purple-500/20 rounded-full mx-auto mb-4"></div>
            <p className="text-blue-200">Loading portfolio...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Normalize holdings to ensure consistent field names
  const normalizedHoldings = normalizeHoldings(portfolio?.holdings || []);

  const chartData = normalizedHoldings.map((holding, index) => ({
    name: holding.protocol_name,
    value: holding.value_usd,
    color: COLORS[index % COLORS.length],
  }));

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return '🛡️';
      case 'high': return '🚀';
      default: return '⚖️';
    }
  };

  return (
    <div className="space-y-6">
      {/* Read-Only Warning for Wallet Mode */}
      {isWalletConnected && !demoMode && (
        <Card className="bg-amber-500/10 backdrop-blur-lg border-amber-500/30">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400" />
            <p className="text-amber-200 text-sm font-medium">
              ⚠️ Real wallet detected — holdings are read-only. Switch to Demo Mode to edit portfolio.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Demo Mode Indicator */}
      {demoMode && !isWalletConnected && (
        <Card className="bg-cyan-500/10 backdrop-blur-lg border-cyan-500/30">
          <CardContent className="p-4 flex items-center gap-3">
            <Shield className="w-5 h-5 text-cyan-400" />
            <p className="text-cyan-200 text-sm font-medium">
              ✨ Demo Mode Active — You can freely edit holdings and test features
            </p>
          </CardContent>
        </Card>
      )}

      {/* Portfolio Summary */}
      <Card className="bg-slate-800/30 backdrop-blur-lg border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <CardTitle className="text-2xl text-white">Portfolio Overview</CardTitle>
              <CardDescription className="text-slate-400">
                Wallet: {wallet.slice(0, 6)}...{wallet.slice(-4)}
              </CardDescription>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                onClick={handleRefresh}
                disabled={isRefreshing}
                variant="outline"
                className="bg-cyan-500/10 border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                onClick={handleLoadDemo}
                disabled={isLoadingDemo}
                variant="outline"
                className="bg-purple-500/10 border-purple-500/30 text-purple-400 hover:bg-purple-500/20"
              >
                <Database className="w-4 h-4 mr-2" />
                Load Demo
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-8">
            {/* Stats */}
            <div className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-lg border border-cyan-500/20">
                <div className="text-sm text-slate-400 mb-1">Total Value</div>
                <div className="text-3xl font-bold text-white">
                  {formatCurrency(portfolio.total_value_usd || 0)}
                </div>
              </div>
              
              <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/50">
                <div className="text-sm text-slate-400 mb-1">Holdings</div>
                <div className="text-xl font-semibold text-white">
                  {normalizedHoldings.length} Protocols
                </div>
              </div>
              
              {/* Risk Profile Selector */}
              {isEditable && (
                <div className="p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/30">
                  <div className="text-sm text-slate-400 mb-2 font-medium">Risk Preference</div>
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-purple-400" />
                    <select
                      className="bg-slate-900/80 text-white px-4 py-2.5 rounded-lg border border-purple-500/30 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all flex-1 font-medium cursor-pointer hover:bg-slate-800/80"
                      value={risk}
                      onChange={(e) => updateRisk(e.target.value)}
                    >
                      <option value="low" className="bg-slate-900">{getRiskIcon('low')} Low Risk</option>
                      <option value="medium" className="bg-slate-900">{getRiskIcon('medium')} Medium Risk</option>
                      <option value="high" className="bg-slate-900">{getRiskIcon('high')} High Risk</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Chart */}
            <div>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-slate-900/95 p-3 rounded-lg border border-slate-700">
                              <p className="text-white font-semibold">{payload[0].name}</p>
                              <p className="text-cyan-400">{formatCurrency(payload[0].value as number)}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-slate-400">
                  No holdings to display
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Editable Holdings Table */}
      <Card className="bg-slate-800/30 backdrop-blur-lg border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-xl text-white">
                  {isEditable ? 'Demo Portfolio Editor' : 'Holdings'}
                </CardTitle>
                {demoMode && !isWalletConnected && (
                  <span className="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-400 rounded-lg font-medium">
                    Demo Portfolio
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-sm text-slate-400">Total Portfolio Value:</span>
                <span className="text-2xl font-bold text-cyan-400">
                  {safeCurrency(portfolio?.total_value_usd || 0)}
                </span>
              </div>
            </div>
            {isEditable ? (
              <Button
                onClick={() => setShowAddModal(true)}
                className="bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Holding
              </Button>
            ) : !demoMode && (
              <p className="text-slate-500 text-sm italic">
                Switch to Demo Mode to manage holdings
              </p>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {normalizedHoldings.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left py-3 px-4 text-slate-400 font-semibold text-xs uppercase">Protocol</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-semibold text-xs uppercase">Token</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-semibold text-xs uppercase">Quantity</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-semibold text-xs uppercase">Value (USD)</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-semibold text-xs uppercase">APY</th>
                    {isEditable && (
                      <th className="text-center py-3 px-4 text-slate-400 font-semibold text-xs uppercase">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {normalizedHoldings.map((holding) => (
                    <tr key={holding.id} className="border-b border-slate-700/30 hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 text-white font-medium">{holding.protocol_name}</td>
                      <td className="py-3 px-4 text-cyan-400 font-medium">{holding.token_symbol}</td>
                      <td className="py-3 px-4 text-right">
                        {isEditable && editingHolding === holding.id ? (
                          <div className="flex items-center justify-end gap-2">
                            <input
                              type="number"
                              step="0.01"
                              value={editAmount}
                              onChange={(e) => setEditAmount(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') saveEdit(holding.id);
                                if (e.key === 'Escape') cancelEdit();
                              }}
                              className="bg-slate-900 text-white w-32 px-2 py-1 text-center rounded border border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                              autoFocus
                            />
                            <button
                              onClick={() => saveEdit(holding.id)}
                              className="text-green-400 hover:text-green-300"
                              title="Save"
                            >
                              ✓
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="text-red-400 hover:text-red-300"
                              title="Cancel"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => isEditable && startEdit(holding)}
                            className={`text-white ${isEditable ? 'hover:text-cyan-400 cursor-pointer' : ''} transition-colors`}
                            disabled={!isEditable}
                          >
                            {safeToFixed(holding.amount, 6)}
                            {isEditable && <Edit2 className="w-3 h-3 inline ml-1 opacity-50" />}
                          </button>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right text-white font-semibold">
                        {safeCurrency(holding.value_usd)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="inline-flex items-center gap-1 text-green-400">
                          <TrendingUp className="w-3 h-3" />
                          {safePercent(holding.apy)}
                        </span>
                      </td>
                      {isEditable && (
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => handleRemove(holding.id)}
                            className="p-2 hover:bg-red-500/10 rounded-lg transition-colors group"
                            title="Remove holding"
                          >
                            <Trash2 className="w-4 h-4 text-slate-400 group-hover:text-red-400" />
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <Database className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 mb-4">No holdings found</p>
              <Button onClick={handleLoadDemo} disabled={isLoadingDemo}>
                <Database className="w-4 h-4 mr-2" />
                Load Demo Data
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Holding Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 max-w-lg w-full shadow-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-4">Add New Holding</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-2 font-medium">Protocol</label>
                <select
                  value={newHolding.protocol_name}
                  onChange={(e) => {
                    const protocol = e.target.value;
                    // Auto-set default token symbol based on protocol
                    const defaultSymbols: Record<string, string> = {
                      'Aave': 'AAVE',
                      'Lido': 'stETH',
                      'Compound': 'COMP',
                      'Curve': 'CRV',
                      'Uniswap': 'UNI',
                      'Yearn': 'YFI',
                      'MakerDAO': 'DAI',
                      'Balancer': 'BAL',
                      'Sushiswap': 'SUSHI',
                      'PancakeSwap': 'CAKE',
                      'RocketPool': 'rETH',
                      'Frax': 'FRAX',
                      'Convex': 'CVX',
                      'dYdX': 'DYDX',
                      'GMX': 'GMX',
                      'Ethena': 'USDe',
                      'Synthetix': 'SNX',
                      'Morpho': 'MORPHO',
                      'Stargate': 'STG',
                      'Venus': 'XVS'
                    };
                    setNewHolding({ 
                      ...newHolding, 
                      protocol_name: protocol,
                      symbol: defaultSymbols[protocol] || ''
                    });
                  }}
                  className="w-full bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-700 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                >
                  <option value="">Select Protocol (Top 20)</option>
                  <option value="Aave">Aave (AAVE)</option>
                  <option value="Lido">Lido (stETH)</option>
                  <option value="Compound">Compound (COMP)</option>
                  <option value="Curve">Curve (CRV)</option>
                  <option value="Uniswap">Uniswap (UNI)</option>
                  <option value="Yearn">Yearn (YFI)</option>
                  <option value="MakerDAO">MakerDAO (DAI)</option>
                  <option value="Balancer">Balancer (BAL)</option>
                  <option value="Sushiswap">Sushiswap (SUSHI)</option>
                  <option value="PancakeSwap">PancakeSwap (CAKE)</option>
                  <option value="RocketPool">RocketPool (rETH)</option>
                  <option value="Frax">Frax (FRAX)</option>
                  <option value="Convex">Convex (CVX)</option>
                  <option value="dYdX">dYdX (DYDX)</option>
                  <option value="GMX">GMX (GMX)</option>
                  <option value="Ethena">Ethena (USDe)</option>
                  <option value="Synthetix">Synthetix (SNX)</option>
                  <option value="Morpho">Morpho (MORPHO)</option>
                  <option value="Stargate">Stargate (STG)</option>
                  <option value="Venus">Venus (XVS)</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  Token symbol will be auto-selected based on protocol
                </p>
              </div>
              
              <div>
                <label className="block text-sm text-slate-300 mb-2 font-medium">Amount (Token Quantity)</label>
                <input
                  type="number"
                  step="0.000001"
                  value={newHolding.amount || ''}
                  onChange={(e) => setNewHolding({ 
                    ...newHolding, 
                    amount: parseFloat(e.target.value) || 0 
                  })}
                  placeholder="10.5"
                  className="w-full bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-700 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Enter the token quantity (backend will fetch live price and APY)
                </p>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <Button
                onClick={() => {
                  setShowAddModal(false);
                  setNewHolding({ 
                    protocol_name: '', 
                    symbol: '', 
                    amount: 0
                  });
                }}
                variant="outline"
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddHolding}
                disabled={!newHolding.protocol_name || !newHolding.symbol || !newHolding.amount || newHolding.amount <= 0}
                className="flex-1 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-700 disabled:text-slate-500 text-white"
              >
                Add Holding
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Market Alerts Feed */}
      <MarketAlerts />
    </div>
  );
}
