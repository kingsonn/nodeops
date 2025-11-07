'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import useSWR from 'swr';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Alert {
  protocol: string;
  change: number;
  type: 'APY' | 'TVL';
  message: string;
  ai_reaction: string;
  severity: 'high' | 'medium' | 'low';
  current_apy: number;
  tvl: number;
  timestamp: string;
}

interface AlertsResponse {
  alerts: Alert[];
  count: number;
  last_updated: string;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function MarketAlerts() {
  const { data, error } = useSWR<AlertsResponse>(
    `${API_URL}/api/alerts`,
    fetcher,
    {
      refreshInterval: 120000, // Refresh every 2 minutes
      revalidateOnFocus: false,
      revalidateOnReconnect: true
    }
  );

  const [visibleAlerts, setVisibleAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    if (data?.alerts) {
      setVisibleAlerts(data.alerts);
    }
  }, [data]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'border-red-500/30 bg-red-500/5';
      case 'medium':
        return 'border-yellow-500/30 bg-yellow-500/5';
      default:
        return 'border-blue-500/30 bg-blue-500/5';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      case 'medium':
        return <Activity className="w-4 h-4 text-yellow-400" />;
      default:
        return <Activity className="w-4 h-4 text-blue-400" />;
    }
  };

  const getChangeIcon = (change: number) => {
    return change > 0 ? (
      <TrendingUp className="w-3 h-3 text-green-400" />
    ) : (
      <TrendingDown className="w-3 h-3 text-red-400" />
    );
  };

  const getChangeColor = (change: number) => {
    return change > 0 ? 'text-green-400' : 'text-red-400';
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return 'Just now';
    }
  };

  if (error) {
    return (
      <Card className="bg-slate-900/60 backdrop-blur-lg border-slate-800">
        <CardContent className="p-4">
          <p className="text-sm text-red-400">Failed to load market alerts</p>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="bg-slate-900/60 backdrop-blur-lg border-slate-800">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center text-sm text-slate-300">
            <Bell className="w-4 h-4 mr-2 animate-pulse" />
            Loading Market Alerts...
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-slate-900/80 via-indigo-900/20 to-slate-900/80 backdrop-blur-lg border-slate-700/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center text-base text-slate-200">
            <Bell className="w-5 h-5 mr-2 text-indigo-400" />
            AI Market Alerts
            {data.count > 0 && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-indigo-500/20 text-indigo-300 rounded-full">
                {data.count} active
              </span>
            )}
          </CardTitle>
          {data.last_updated && (
            <span className="text-xs text-slate-500">
              Updated {formatTimestamp(data.last_updated)}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent pr-2">
          <AnimatePresence mode="popLayout">
            {visibleAlerts.map((alert, index) => (
              <motion.div
                key={`${alert.protocol}-${alert.timestamp}-${index}`}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={`rounded-lg border p-3 ${getSeverityColor(alert.severity)} hover:bg-white/5 transition-colors`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1">
                    {getSeverityIcon(alert.severity)}
                    <span className="text-sm font-semibold text-slate-100">
                      {alert.protocol}
                    </span>
                    <span className={`flex items-center gap-1 text-xs font-medium ${getChangeColor(alert.change)}`}>
                      {getChangeIcon(alert.change)}
                      {Math.abs(alert.change)}%
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wide">
                    {alert.type}
                  </span>
                </div>

                {/* Message */}
                <p className="text-xs text-slate-300 mb-2">
                  {alert.message}
                </p>

                {/* AI Reaction */}
                <div className="flex items-start gap-2 p-2 bg-indigo-500/5 rounded border border-indigo-500/20">
                  <span className="text-xs text-indigo-400 font-medium flex-shrink-0">
                    AI:
                  </span>
                  <p className="text-xs text-indigo-200 italic leading-relaxed">
                    {alert.ai_reaction}
                  </p>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-700/50">
                  <div className="flex items-center gap-3 text-[10px] text-slate-500">
                    <span>APY: {alert.current_apy.toFixed(2)}%</span>
                    <span>•</span>
                    <span>TVL: ${(alert.tvl / 1000000).toFixed(1)}M</span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {formatTimestamp(alert.timestamp)}
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {visibleAlerts.length === 0 && (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No active alerts</p>
              <p className="text-xs text-slate-500 mt-1">
                Market conditions are stable
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
