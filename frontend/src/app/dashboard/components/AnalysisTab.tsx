'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { AIAnalysis } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sparkles, TrendingUp, ArrowRight, Play, FileDown } from 'lucide-react';
import { formatPercent, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

interface AnalysisTabProps {
  wallet: string;
}

export default function AnalysisTab({ wallet }: AnalysisTabProps) {
  const [analysis, setAnalysis] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    toast.info('🤖 Analyzing your portfolio with Groq LLaMA — this may take a moment…', {
      duration: 5000,
    });
    
    try {
      const result = await api.ai.analyze(wallet);
      console.log('[AnalysisTab] AI Analysis Result:', result);
      setAnalysis(result);
      toast.success('✅ AI analysis + simulation complete!');
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(`❌ AI analysis failed — ${errorMsg}`);
      console.error('AI Analysis Error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      await api.ai.execute(wallet, 1);
      toast.success('Execution request submitted (simulation only)');
    } catch (error) {
      toast.error('Failed to execute');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDownloadReport = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const reportUrl = `${apiUrl}/api/report/generate?wallet=${wallet}`;
    
    toast.info('📄 Generating AI Audit Report...', { duration: 3000 });
    
    // Open in new tab to trigger download
    window.open(reportUrl, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 backdrop-blur-lg border-purple-500/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl text-white flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-purple-400" />
                AI Portfolio Analysis
              </CardTitle>
              <CardDescription className="text-blue-300">
                Powered by Groq LLaMA 3.3 70B
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                <Play className={`w-4 h-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
                {isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}
              </Button>
              {analysis && (
                <Button
                  onClick={handleDownloadReport}
                  variant="outline"
                  className="border-purple-500/50 text-purple-300 hover:bg-purple-500/20"
                >
                  <FileDown className="w-4 h-4 mr-2" />
                  Download Report (PDF)
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Analysis Results */}
      {analysis ? (
        <>
          {/* Extract ai_result and simulation from unified response */}
          {(() => {
            const ai = analysis.ai_result || analysis;
            const sim = analysis.simulation;
            const hasRecs = ai?.recommendations && ai.recommendations.length > 0;
            const hasSim = sim && typeof sim.before_total_apy === 'number';

            return (
              <>
                {/* Metadata Badge */}
                {ai.ai_model && (
                  <div className="flex items-center gap-2 text-xs text-blue-300 mb-4">
                    <Sparkles className="w-3 h-3" />
                    <span>Model: <span className="font-semibold text-white">{ai.ai_model}</span></span>
                    {ai.timestamp && (
                      <span className="text-blue-400">• {new Date(ai.timestamp).toLocaleString()}</span>
                    )}
                  </div>
                )}

                {/* Summary Card */}
                <Card className="bg-white/10 backdrop-blur-lg border-white/20">
                  <CardHeader>
                    <CardTitle className="text-xl text-white">AI Recommendation</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid md:grid-cols-3 gap-4">
                      <div className="p-4 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-lg border border-green-500/30">
                        <div className="text-sm text-green-300 mb-1">Expected Yield Increase</div>
                        <div className="text-2xl font-bold text-white flex items-center gap-2">
                          <TrendingUp className="w-5 h-5" />
                          {ai.estimated_yield_improvement || 
                           (typeof ai.expected_yield_increase === 'number' 
                             ? `+${ai.expected_yield_increase.toFixed(2)}%` 
                             : (hasSim && typeof sim.apy_increase === 'number' 
                                 ? `+${sim.apy_increase.toFixed(2)}%` 
                                 : 'N/A'))}
                        </div>
                      </div>
                      
                      <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                        <div className="text-sm text-blue-300 mb-1">Confidence</div>
                        <div className="text-2xl font-bold text-white">
                          {typeof ai.confidence === 'number' ? `${(ai.confidence * 100).toFixed(0)}%` : 'N/A'}
                        </div>
                      </div>
                      
                      <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                        <div className="text-sm text-blue-300 mb-1">Action</div>
                        <div className="text-2xl font-bold text-white capitalize">
                          Rebalance
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-white/5 rounded-lg border border-white/10">
                      <div className="text-sm text-blue-300 mb-2">Explanation</div>
                      <p className="text-white leading-relaxed">{ai.explanation || 'No explanation available'}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Recommended Allocations Card */}
                {ai.recommended_allocations && Object.keys(ai.recommended_allocations).length > 0 && (
                  <Card className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 backdrop-blur-lg border-green-500/30">
                    <CardHeader>
                      <CardTitle className="text-xl text-white flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-green-400" />
                        Recommended Portfolio Allocation
                      </CardTitle>
                      <CardDescription className="text-green-300">
                        Suggested rebalancing to optimize yield
                        {ai.estimated_yield_improvement && (
                          <span className="ml-2 px-2 py-0.5 bg-green-500/20 rounded text-green-400 font-semibold">
                            {ai.estimated_yield_improvement} improvement
                          </span>
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(ai.recommended_allocations).map(([protocol, percentage]: [string, any]) => (
                          <div key={protocol} className="p-3 bg-white/5 rounded-lg border border-white/10">
                            <div className="text-sm text-green-300 mb-1 font-medium">{protocol}</div>
                            <div className="text-2xl font-bold text-white">{String(percentage)}</div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                    
                  </Card>
                )}

                {/* AI Reasoning Card */}
                {ai.ai_reasoning && (
            <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 backdrop-blur-lg border-purple-500/30">
              <CardHeader>
                <CardTitle className="text-xl text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  AI Strategic Insights
                </CardTitle>
                <CardDescription className="text-purple-300">
                  Groq LLaMA 3.3 70B analysis based on live DeFi data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="text-sm text-purple-300 mb-2 font-semibold">Portfolio Assessment</div>
                  <p className="text-white leading-relaxed">{ai.ai_reasoning.category_analysis}</p>
                </div>

                {ai.ai_reasoning.optimization_directions && ai.ai_reasoning.optimization_directions.length > 0 && (
                  <div>
                    <div className="text-sm text-purple-300 mb-2 font-semibold">📊 Actionable Recommendations</div>
                    <ul className="space-y-2">
                      {ai.ai_reasoning.optimization_directions.map((direction: string, index: number) => (
                        <li key={index} className="flex items-start gap-2 text-white bg-purple-500/10 p-3 rounded-lg border border-purple-500/20">
                          <span className="text-purple-400 mt-1 font-bold">{index + 1}.</span>
                          <span>{direction}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {ai.ai_reasoning.ai_reasoning && (
                  <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/30">
                    <div className="text-sm text-blue-300 mb-2 font-semibold">🧠 AI Reasoning</div>
                    <p className="text-white leading-relaxed">{ai.ai_reasoning.ai_reasoning}</p>
                  </div>
                )}

                <div>
                  <div className="text-sm text-purple-300 mb-2 font-semibold">Risk Assessment</div>
                  <p className="text-white leading-relaxed">{ai.ai_reasoning.risk_assessment}</p>
                </div>
              </CardContent>
            </Card>
          )}

                                
                

                {ai.action === 'hold' && (
            <Card className="bg-blue-500/10 backdrop-blur-lg border-blue-500/30">
              <CardContent className="p-6 text-center">
                <p className="text-blue-300">
                  ✓ Your portfolio is already optimally balanced. No rebalancing needed.
                </p>
              </CardContent>
            </Card>
          )}
              </>
            );
          })()}
        </>
      ) : isAnalyzing ? (
        <Card className="bg-white/10 backdrop-blur-lg border-white/20">
          <CardContent className="p-12 text-center">
            <div className="animate-pulse">
              <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4 animate-spin" />
              <h3 className="text-xl font-bold text-white mb-2">🤖 AI Analysis in Progress</h3>
              <p className="text-blue-300 mb-4">
                Groq LLaMA 3.3 70B is analyzing your portfolio...
              </p>
              <p className="text-sm text-blue-400">
                This may take 30-60 seconds for authentic AI reasoning
              </p>
              <div className="mt-6 flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="bg-white/10 backdrop-blur-lg border-white/20">
          <CardContent className="p-12 text-center">
            <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white mb-2">No Analysis Yet</h3>
            <p className="text-blue-300 mb-6">
              Click &quot;Run AI Analysis&quot; to get AI-powered rebalancing recommendations
            </p>
            <Button onClick={handleAnalyze} disabled={isAnalyzing}>
              <Play className="w-4 h-4 mr-2" />
              Run AI Analysis
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
