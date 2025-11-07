# 🚀 AutoDeFi.AI - AI-Powered DeFi Portfolio Strategist

[![NodeOps Hackathon](https://img.shields.io/badge/NodeOps-Proof%20of%20Build-blue)](https://nodeops.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![Groq](https://img.shields.io/badge/AI-Groq%20LLaMA%203.3-orange)](https://groq.com)

> **Built for NodeOps Proof of Build Virtual DePin Hackathon (October 2025)**  
> Empowering DeFi users with AI-driven portfolio optimization and autonomous vault management.

---

## 🏆 Hackathon Submission

### **NodeOps Proof Of Build Virtual DePin Hackathon**
**Duration:** October 1 – October 31, 2025  
**Track:** AI & DeFi  
**Goal:** Build production-ready tools that work in the real world

This project is our submission to demonstrate the power of combining **AI intelligence** with **DeFi infrastructure** on decentralized infrastructure. AutoDeFi.AI is not just a concept — it's a fully functional, deployable application ready for the NodeOps Template Marketplace.

---

## 🎯 What We Built

AutoDeFi.AI is an **AI-powered DeFi portfolio strategist** that helps users:

✅ **Analyze** their DeFi portfolios with real-time market data  
✅ **Optimize** allocations using Groq's LLaMA 3.3 70B AI model  
✅ **Simulate** rebalancing strategies before execution  
✅ **Automate** portfolio management with AI-driven vaults  
✅ **Monitor** market alerts and yield opportunities 24/7  
✅ **Export** detailed audit reports as professional PDFs  

**This is a complete, production-ready solution** — not a prototype. Every feature is live, tested, and ready to deploy.

---

## 🌟 Key Features

### 🤖 **AI-Powered Analysis**
- **Groq LLaMA 3.3 70B** integration for intelligent portfolio analysis
- Real-time recommendations with confidence scores
- Explainable AI reasoning for every decision
- Multi-protocol optimization across Aave, Lido, Compound, Curve, and more

### 💼 **Interactive Portfolio Management**
- Live token prices from CoinGecko API
- Real-time APY data from DeFiLlama
- Add, edit, and remove holdings with instant recalculation
- Demo mode for testing without wallet connection
- MetaMask integration for real wallet analysis

### 🏦 **Autonomous AI Vaults**
- Auto-generated vaults based on risk preference (Low/Medium/High)
- Automatic rebalancing every 6 hours
- AI decision logging with full transparency
- Simulate deposits before committing funds
- Subscribe to vaults for hands-free management

### 🚨 **Live Market Alerts**
- Real-time APY and TVL change detection
- AI-generated contextual reactions
- Severity-based alert system (High/Medium/Low)
- Protocol-specific opportunity notifications

### 📊 **Professional Reporting**
- Downloadable PDF audit reports
- Complete portfolio analysis with AI insights
- Recommended allocations and expected yield improvements
- Vault performance reports with historical logs

### 🎨 **Modern UI/UX**
- Beautiful, responsive design with Tailwind CSS
- Dark mode optimized
- Real-time data updates
- Interactive charts and visualizations
- Mobile-friendly interface

---

## 🏗️ Architecture

### **Tech Stack**

#### **Backend (FastAPI)**
- **Framework:** FastAPI 0.109.0
- **AI Model:** Groq LLaMA 3.3 70B Versatile
- **Database:** Supabase (PostgreSQL)
- **Caching:** Redis
- **APIs:** DeFiLlama, CoinGecko
- **PDF Generation:** ReportLab
- **Scheduling:** APScheduler (vault auto-refresh)

#### **Frontend (Next.js)**
- **Framework:** Next.js 14 with App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Icons:** Lucide React
- **Wallet:** MetaMask integration

#### **Infrastructure**
- **Containerization:** Docker multi-stage builds
- **Deployment:** NodeOps DePin infrastructure
- **Database:** Supabase (managed PostgreSQL)
- **Caching:** Redis for API response optimization

---

## 🚀 Quick Start

### **Prerequisites**
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- API Keys:
  - [Groq API Key](https://console.groq.com/keys) (required)
  - [Supabase Project](https://supabase.com/dashboard) (required)
  - [CoinGecko API Key](https://www.coingecko.com/en/api) (optional)

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/autodefi-ai.git
cd autodefi-ai
```

### **2. Set Environment Variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
COINGECKO_API_KEY=your_coingecko_key  # Optional
```

### **3. Run with Docker Compose**
```bash
# Development mode
docker-compose -f docker-compose.dev.yml up -d

# Production mode
docker-compose up -d
```

### **4. Access Application**
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 📦 Deployment to NodeOps

### **Option 1: Web UI**
1. Go to [NodeOps Template Marketplace](https://app.nodeops.io/templates)
2. Upload `nodeops-template.yaml`
3. Enter your API keys
4. Click "Deploy"

### **Option 2: CLI**
```bash
# Install NodeOps CLI
npm install -g @nodeops/cli

# Login
nodeops login

# Deploy
nodeops deploy --template autodefi-ai \
  --set GROQ_API_KEY=your_key \
  --set SUPABASE_URL=your_url \
  --set SUPABASE_KEY=your_key
```

---

## 🎮 Usage

### **Demo Mode**
1. Visit http://localhost:3000
2. Click "Try Demo Mode"
3. Explore features with sample portfolio
4. Test AI analysis, vaults, and alerts

### **Real Wallet Mode**
1. Connect MetaMask
2. Your wallet is automatically synced
3. Add your DeFi holdings manually
4. Get AI-powered recommendations
5. Simulate rebalancing strategies

### **AI Vaults**
1. Navigate to "Vaults" tab
2. Select risk preference (Low/Medium/High)
3. Click "Generate AI Vault"
4. Simulate deposit to see expected returns
5. Subscribe for automatic management

### **Market Alerts**
1. Navigate to "Alerts" tab
2. View real-time market changes
3. See AI reactions to opportunities
4. Filter by severity (High/Medium/Low)

---

## 📊 API Endpoints

### **Portfolio Management**
- `GET /api/portfolio/?wallet={address}` - Get portfolio
- `POST /api/portfolio/demo/holdings/add` - Add holding
- `POST /api/portfolio/demo/holdings/update` - Update holding
- `POST /api/portfolio/demo/holdings/remove` - Remove holding

### **AI Analysis**
- `GET /api/ai/analyze?wallet={address}` - AI portfolio analysis
- `GET /api/ai/simulate?wallet={address}` - Simulate rebalancing

### **Vaults**
- `GET /api/vaults/` - List all vaults
- `POST /api/vaults/generate` - Generate AI vault
- `POST /api/vaults/simulate` - Simulate vault deposit
- `POST /api/vaults/{id}/refresh` - Manual vault refresh

### **Alerts**
- `GET /api/alerts` - Get market alerts
- `GET /api/alerts/summary` - Alert statistics

### **Reports**
- `GET /api/report/generate?wallet={address}` - Portfolio PDF
- `GET /api/report/vault/{id}` - Vault PDF

**Full API documentation:** http://localhost:8000/docs

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.dev.yml up -d
pytest tests/integration/
```

---

## 🎨 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### AI Analysis
![AI Analysis](docs/screenshots/analysis.png)

### AI Vaults
![Vaults](docs/screenshots/vaults.png)

### Market Alerts
![Alerts](docs/screenshots/alerts.png)

---

## 🏆 Hackathon Impact

### **Real-World Value**
AutoDeFi.AI addresses critical pain points in DeFi:

1. **Information Overload** → AI-powered insights
2. **Manual Rebalancing** → Autonomous vaults
3. **Missed Opportunities** → Real-time alerts
4. **Complex Analysis** → Simple, actionable recommendations
5. **Trust Issues** → Explainable AI with audit reports

### **Production-Ready**
- ✅ Fully functional backend and frontend
- ✅ Docker containerized for easy deployment
- ✅ NodeOps template marketplace ready
- ✅ Comprehensive API documentation
- ✅ Error handling and rate limiting
- ✅ Security best practices implemented
- ✅ Scalable architecture

### **Market Potential**
- **Target Users:** DeFi investors, yield farmers, portfolio managers
- **Revenue Model:** Subscription tiers, vault management fees
- **Scalability:** Multi-chain support (future), institutional features
- **Ecosystem Integration:** NodeOps marketplace distribution

---

## 🛠️ Development

### **Project Structure**
```
autodefi-ai/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes
│   ├── services/           # Business logic
│   ├── core/               # Config & security
│   └── tasks/              # Background jobs
├── frontend/               # Next.js frontend
│   ├── src/app/           # App router pages
│   ├── src/components/    # React components
│   └── src/lib/           # Utilities
├── agent/                  # AI agent logic
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Development compose
├── nodeops-template.yaml   # NodeOps deployment
└── requirements.txt        # Python dependencies
```

### **Local Development**

#### **Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

#### **Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Security

- ✅ Environment variables for sensitive data
- ✅ Rate limiting on all endpoints
- ✅ CORS properly configured
- ✅ Input validation with Pydantic
- ✅ Non-root Docker containers
- ✅ API key rotation support
- ✅ Secure database connections

---

## 📈 Roadmap

### **Phase 1: Hackathon (October 2025)** ✅
- [x] Core AI analysis engine
- [x] Portfolio management
- [x] Autonomous vaults
- [x] Market alerts
- [x] PDF reporting
- [x] NodeOps deployment

### **Phase 2: Post-Hackathon (Q4 2025)**
- [ ] Multi-chain support (Polygon, Arbitrum, Optimism)
- [ ] On-chain transaction execution
- [ ] Social features (share strategies)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard

### **Phase 3: Production (Q1 2026)**
- [ ] Institutional features
- [ ] White-label solutions
- [ ] API marketplace
- [ ] Governance token
- [ ] DAO structure

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### **How to Contribute**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

Built with ❤️ for the NodeOps Proof of Build Hackathon

- **Developer:** [Your Name]
- **GitHub:** [@yourusername](https://github.com/yourusername)
- **Twitter:** [@yourhandle](https://twitter.com/yourhandle)

---

## 🙏 Acknowledgments

- **NodeOps** for hosting the hackathon and providing DePin infrastructure
- **Groq** for the incredible LLaMA 3.3 70B API
- **Supabase** for managed PostgreSQL and authentication
- **DeFiLlama** for comprehensive DeFi protocol data
- **CoinGecko** for real-time token pricing
- **FastAPI** and **Next.js** communities for excellent frameworks

---

## 📞 Contact & Support

- **Email:** support@autodefi.ai
- **Discord:** [Join our community](#)
- **Documentation:** [docs.autodefi.ai](#)
- **Issues:** [GitHub Issues](https://github.com/yourusername/autodefi-ai/issues)

---

## 🌐 Links

- **Live Demo:** https://autodefi.ai
- **API Docs:** https://api.autodefi.ai/docs
- **NodeOps Template:** [View on Marketplace](#)
- **Hackathon Submission:** [NodeOps Portal](#)

---

<div align="center">

### **Built for NodeOps Proof of Build Hackathon 2025**

**Making DeFi Smarter with AI** 🚀

[Demo](https://autodefi.ai) • [Docs](https://docs.autodefi.ai) • [API](https://api.autodefi.ai/docs) • [Deploy](https://app.nodeops.io)

</div>
