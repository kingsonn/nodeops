'use client';

/**
 * AutoDeFi.AI Landing Page
 * Production-ready landing page showcasing real product capabilities
 */

import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  Bot, 
  FileText, 
  Activity, 
  Sparkles, 
  TrendingUp, 
  Shield,
  ArrowRight,
  CheckCircle2,
  Zap,
  Database,
  Wallet,
  Brain
} from 'lucide-react';

export default function Home() {
  const handleDemoReport = () => {
    window.open('/api/report/generate?wallet=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', '_blank');
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 overflow-hidden">
      {/* Animated background gradient */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent pointer-events-none" />
      
      <div className="relative">
        {/* Navigation */}
        <nav className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-8 h-8 text-cyan-400" />
              <span className="text-2xl font-bold text-white">AutoDeFi.AI</span>
            </div>
            <Link href="/dashboard">
              <button className="px-6 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 rounded-lg font-medium transition-all">
                Launch App
              </button>
            </Link>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="container mx-auto px-4 py-20 md:py-32">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-full mb-6">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span className="text-cyan-300 text-sm font-medium">Powered by Groq LLaMA 3.3 70B</span>
              </div>
              
              <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
                DeFi made{' '}
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400">
                  intelligent
                </span>
              </h1>
              
              <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                AutoDeFi.AI analyzes your wallet, builds AI-powered vaults, and maximizes yield — all in real time.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/dashboard">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white text-lg font-bold rounded-xl shadow-2xl shadow-cyan-500/30 transition-all flex items-center gap-2 justify-center"
                  >
                    Launch Dashboard
                    <ArrowRight className="w-5 h-5" />
                  </motion.button>
                </Link>
                
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="relative"
            >
              {/* Dashboard preview mockup */}
              <div className="relative bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 shadow-2xl">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <div className="space-y-3">
                  <div className="h-8 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded animate-pulse" />
                  <div className="h-32 bg-gradient-to-br from-purple-500/10 to-cyan-500/10 rounded border border-cyan-500/20" />
                  <div className="grid grid-cols-3 gap-3">
                    <div className="h-20 bg-slate-800/50 rounded" />
                    <div className="h-20 bg-slate-800/50 rounded" />
                    <div className="h-20 bg-slate-800/50 rounded" />
                  </div>
                </div>
                {/* Floating elements */}
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  className="absolute -top-4 -right-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-bold"
                >
                  +12.5% APY
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="container mx-auto px-4 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Your AI DeFi Strategist
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Real-time portfolio intelligence, smart vaults, and autonomous optimization
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
            {[
              {
                icon: BarChart3,
                title: 'AI Portfolio Analysis',
                description: 'Connect your wallet and get a full breakdown of holdings, risk exposure, and real-time yield insights.',
                color: 'cyan'
              },
              {
                icon: Bot,
                title: 'AI Vaults (Autonomous)',
                description: 'AI builds and refreshes smart DeFi vaults every 6 hours, tuned to your risk preference.',
                color: 'purple'
              },
              {
                icon: FileText,
                title: 'Explainable Reports',
                description: 'Download professional-grade PDF audit reports with reasoning, performance, and rebalancing suggestions.',
                color: 'blue'
              },
              {
                icon: Activity,
                title: 'Live DeFi Signals',
                description: 'Stay ahead with real-time market updates — APY shifts, liquidity moves, and risk alerts powered by live DeFiLlama data.',
                color: 'green'
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -5 }}
                className="bg-slate-800/30 backdrop-blur-lg rounded-2xl p-6 border border-slate-700/50 hover:border-cyan-500/50 transition-all group"
              >
                <div className={`w-12 h-12 bg-${feature.color}-500/10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className={`w-6 h-6 text-${feature.color}-400`} />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="container mx-auto px-4 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              How It Works
            </h2>
            <p className="text-xl text-slate-400">
              Three simple steps to intelligent DeFi
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                step: '01',
                title: 'Connect Wallet',
                description: 'Securely connect MetaMask or view demo mode.',
                icon: Wallet
              },
              {
                step: '02',
                title: 'Analyze Portfolio',
                description: 'Our AI scans your holdings and compares live DeFi performance data.',
                icon: Brain
              },
              {
                step: '03',
                title: 'Get AI Insights',
                description: 'View strategies, download reports, or let vaults update automatically.',
                icon: Zap
              }
            ].map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="relative"
              >
                <div className="bg-slate-800/30 backdrop-blur-lg rounded-2xl p-8 border border-slate-700/50">
                  <div className="text-6xl font-bold text-cyan-500/20 mb-4">{step.step}</div>
                  <div className="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center mb-4">
                    <step.icon className="w-6 h-6 text-cyan-400" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">{step.title}</h3>
                  <p className="text-slate-400 leading-relaxed">{step.description}</p>
                </div>
                {index < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-cyan-500 to-transparent" />
                )}
              </motion.div>
            ))}
          </div>
        </section>

        {/* Built with Real Data */}
        <section className="container mx-auto px-4 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="bg-slate-900/30 backdrop-blur-lg rounded-3xl border border-slate-800/50 p-12"
          >
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Built with Real Data
              </h2>
              <p className="text-xl text-slate-400">
                Every decision is powered by live data, not assumptions.
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-8 max-w-5xl mx-auto items-center">
              {[
                { name: 'CoinGecko', icon: Database, color: 'yellow' },
                { name: 'DeFiLlama', icon: Activity, color: 'blue' },
                { name: 'Groq LLaMA', icon: Brain, color: 'purple' },
                { name: 'Supabase', icon: Database, color: 'green' },
                { name: 'MetaMask', icon: Wallet, color: 'orange' }
              ].map((integration, index) => (
                <motion.div
                  key={integration.name}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="flex flex-col items-center gap-3 group"
                >
                  <div className="w-16 h-16 bg-slate-800/50 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform border border-slate-700/50">
                    <integration.icon className="w-8 h-8 text-cyan-400" />
                  </div>
                  <span className="text-slate-400 text-sm font-medium">{integration.name}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* Why AutoDeFi.AI */}
        <section className="container mx-auto px-4 py-20">
          <div className="grid md:grid-cols-2 gap-12 items-center max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
            >
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                Why AutoDeFi.AI?
              </h2>
              <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                We built AutoDeFi.AI to solve one problem — DeFi complexity.
              </p>
              <p className="text-slate-400 mb-8 leading-relaxed">
                Managing a DeFi portfolio shouldn&apos;t require a PhD in finance. Our AI analyzes thousands of data points in real-time, giving you institutional-grade insights in seconds.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="space-y-4"
            >
              {[
                'AI-driven portfolio insights',
                'Automatic vault rebalancing',
                'Professional-grade reports',
                'Real data, real yield',
                'Zero execution risk',
                'Transparent AI reasoning'
              ].map((benefit, index) => (
                <motion.div
                  key={benefit}
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="flex items-center gap-3 bg-slate-800/30 backdrop-blur-lg rounded-xl p-4 border border-slate-700/50"
                >
                  <CheckCircle2 className="w-6 h-6 text-cyan-400 flex-shrink-0" />
                  <span className="text-white font-medium">{benefit}</span>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

       

        {/* Final CTA */}
        <section className="container mx-auto px-4 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 backdrop-blur-lg rounded-3xl p-12 md:p-16 border border-cyan-500/20 text-center"
          >
            <h2 className="text-4xl md:text-6xl font-bold text-white mb-6">
              Start your AI-powered DeFi journey today
            </h2>
            <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
              Join the future of intelligent DeFi portfolio management
            </p>
            <Link href="/dashboard">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-12 py-5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white text-xl font-bold rounded-xl shadow-2xl shadow-cyan-500/30 transition-all inline-flex items-center gap-3"
              >
                Launch Dashboard
                <ArrowRight className="w-6 h-6" />
              </motion.button>
            </Link>
          </motion.div>
        </section>

        {/* Footer */}
        <footer className="container mx-auto px-4 py-12 border-t border-slate-800/50">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Brain className="w-6 h-6 text-cyan-400" />
              <span className="text-white font-bold">AutoDeFi.AI</span>
              <span className="text-slate-500 text-sm">© 2025</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <span>Made with Groq + DeFiLlama + Supabase</span>
            </div>
          </div>
        </footer>

        {/* Floating Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1, duration: 0.5 }}
          className="fixed bottom-6 right-6 bg-slate-800/90 backdrop-blur-lg rounded-full px-4 py-2 border border-slate-700/50 shadow-xl hidden md:block"
        >
          <div className="flex items-center gap-2 text-sm">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-300">Powered by AI</span>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
