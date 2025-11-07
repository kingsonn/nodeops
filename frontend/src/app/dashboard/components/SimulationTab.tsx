'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { Simulation } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, TrendingUp, DollarSign, ArrowRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatPercent, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

interface SimulationTabProps {
  wallet: string;
}

export default function SimulationTab({ wallet }: SimulationTabProps) {
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const handleSimulate = async () => {
    setIsSimulating(true);
    try {
      const result = await api.ai.simulate(wallet);
      
      // Check if response was filtered by safety filters
      if ((result as any).note === "AI response was filtered for safety") {
        toast.warning('⚠️ AI simulation was restricted by safety filters — showing placeholder results.');
        setSimulation(result);
      } else {
        setSimulation(result);
        toast.success(`Simulation complete — +${result.apy_increase.toFixed(2)}% APY expected`);
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(`❌ Failed to run simulation — ${errorMsg}`);
      console.error('Simulation Error:', error);
    } finally {
      setIsSimulating(false);
    }
  };

  const chartData = simulation
    ? [
        {
          name: 'Before',
          APY: simulation.before_total_apy,
        },
        {
          name: 'After',
          APY: simulation.after_total_apy,
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 backdrop-blur-lg border-blue-500/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl text-white flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-blue-400" />
                Rebalancing Simulation
              </CardTitle>
              <CardDescription className="text-blue-300">
                Test strategies with zero risk
              </CardDescription>
            </div>
            <Button
              onClick={handleSimulate}
              disabled={isSimulating}
              className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
            >
              <Play className={`w-4 h-4 mr-2 ${isSimulating ? 'animate-spin' : ''}`} />
              {isSimulating ? 'Simulating...' : 'Run Simulation'}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Simulation Results */}
      {simulation ? (
        <>
          {/* Safety Filter Warning */}
          {(simulation as any).note === "AI response was filtered for safety" && (
            <Card className="bg-yellow-500/10 backdrop-blur-lg border-yellow-500/30">
              <CardContent className="p-6">
                <div className="flex items-start gap-3">
                  <div className="text-2xl">⚠️</div>
                  <div>
                    <h3 className="text-lg font-bold text-yellow-300 mb-2">
                      AI Response Filtered by Safety Filters
                    </h3>
                    <p className="text-yellow-200 mb-2">
                      Gemini&apos;s safety filters restricted the AI response. This can happen when:
                    </p>
                    <ul className="list-disc list-inside text-yellow-200 text-sm space-y-1 mb-3">
                      <li>Portfolio data contains sensitive information</li>
                      <li>Analysis involves financial transactions</li>
                      <li>Content is flagged as potentially harmful</li>
                    </ul>
                    <p className="text-yellow-200 text-sm">
                      <strong>Suggestion:</strong> Try running the analysis again or adjust your portfolio data.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Summary Cards */}
          <div className="grid md:grid-cols-3 gap-4">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardContent className="p-6">
                <div className="text-sm text-blue-300 mb-2">Before APY</div>
                <div className="text-3xl font-bold text-white">
                  {formatPercent(simulation.before_total_apy)}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-lg border-green-500/30">
              <CardContent className="p-6">
                <div className="text-sm text-green-300 mb-2">After APY</div>
                <div className="text-3xl font-bold text-white flex items-center gap-2">
                  <TrendingUp className="w-6 h-6" />
                  {formatPercent(simulation.after_total_apy)}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-lg border-purple-500/30">
              <CardContent className="p-6">
                <div className="text-sm text-purple-300 mb-2">Expected Gain (Annual)</div>
                <div className="text-3xl font-bold text-white flex items-center gap-2">
                  <DollarSign className="w-6 h-6" />
                  {formatCurrency(simulation.expected_gain_usd)}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* APY Comparison Chart */}
          <Card className="bg-white/10 backdrop-blur-lg border-white/20">
            <CardHeader>
              <CardTitle className="text-xl text-white">APY Comparison</CardTitle>
              <CardDescription className="text-blue-300">
                Before vs After Rebalancing
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                  <XAxis dataKey="name" stroke="#93c5fd" />
                  <YAxis stroke="#93c5fd" />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-black/90 p-3 rounded-lg border border-white/20">
                            <p className="text-white font-semibold">{payload[0].payload.name}</p>
                            <p className="text-blue-300">APY: {formatPercent(payload[0].value as number)}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend />
                  <Bar dataKey="APY" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Simulated Changes */}
          {simulation.simulated_changes && simulation.simulated_changes.length > 0 && (
            <Card className="bg-white/10 backdrop-blur-lg border-white/20">
              <CardHeader>
                <CardTitle className="text-xl text-white">Simulated Changes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="text-left py-3 px-4 text-blue-300 font-semibold">From</th>
                        <th className="text-center py-3 px-4 text-blue-300 font-semibold"></th>
                        <th className="text-left py-3 px-4 text-blue-300 font-semibold">To</th>
                        <th className="text-right py-3 px-4 text-blue-300 font-semibold">% Move</th>
                        <th className="text-left py-3 px-4 text-blue-300 font-semibold">Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {simulation.simulated_changes.map((change, index) => (
                        <tr key={index} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-3 px-4 text-white font-medium">{change.from}</td>
                          <td className="py-3 px-4 text-center">
                            <ArrowRight className="w-4 h-4 text-blue-400 mx-auto" />
                          </td>
                          <td className="py-3 px-4 text-white font-medium">{change.to}</td>
                          <td className="py-3 px-4 text-right text-purple-400 font-semibold">
                            {change.percent}%
                          </td>
                          <td className="py-3 px-4 text-blue-200">{change.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Explanation */}
          <Card className="bg-white/10 backdrop-blur-lg border-white/20">
            <CardHeader>
              <CardTitle className="text-xl text-white">Detailed Explanation</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-blue-200 leading-relaxed">{simulation.explanation}</p>
              
              <div className="mt-4 p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                <div className="flex items-center gap-2 text-sm text-blue-300">
                  <TrendingUp className="w-4 h-4" />
                  <span>
                    Confidence: <strong className="text-white">{(simulation.confidence * 100).toFixed(0)}%</strong>
                  </span>
                </div>
              </div>

              <div className="mt-4 p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
                <p className="text-sm text-yellow-300">
                  ⚠️ This is a simulation only. No real transactions will be executed.
                </p>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card className="bg-white/10 backdrop-blur-lg border-white/20">
          <CardContent className="p-12 text-center">
            <TrendingUp className="w-16 h-16 text-blue-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Simulation Yet</h3>
            <p className="text-blue-300 mb-6">
              Run a simulation to see how rebalancing would affect your portfolio
            </p>
            <Button onClick={handleSimulate} disabled={isSimulating}>
              <Play className="w-4 h-4 mr-2" />
              Run Simulation
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
