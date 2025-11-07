"""
Report Service
Generates professional PDF audit reports for AI portfolio analysis using ReportLab
"""

from datetime import datetime
from typing import Dict, Any
import logging
from io import BytesIO
from fastapi.responses import StreamingResponse

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from backend.services.portfolio import portfolio_service
from backend.services.ai_agent import AIAgent

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating AI portfolio audit reports using ReportLab"""
    
    def __init__(self):
        logger.info("[REPORT] 📁 Report service initialized with ReportLab (cross-platform)")
    
    async def generate_analysis_report(self, wallet_address: str) -> StreamingResponse:
        """
        Generate comprehensive AI audit report PDF using ReportLab
        Includes all data from AnalysisTab: holdings, APY before/after, yield increase,
        expected gain, recommendations, AI reasoning, and confidence score.
        
        Args:
            wallet_address: Wallet address to analyze
            
        Returns:
            StreamingResponse with PDF file
        """
        try:
            logger.info(f"[REPORT] 📊 Generating audit report for wallet: {wallet_address[:10]}...")
            
            # 1️⃣ Fetch portfolio data
            logger.info("[REPORT] 🔍 Fetching portfolio data...")
            portfolio = await portfolio_service.get_user_portfolio(wallet_address)
            
            if not portfolio:
                logger.warning(f"[REPORT] ⚠️ No portfolio found for wallet: {wallet_address}")
                portfolio = {
                    "total_value": 0,
                    "holdings": [],
                    "protocols": []
                }
            
            # 2️⃣ Run AI analysis (includes simulation)
            logger.info("[REPORT] 🧠 Running AI analysis with simulation...")
            agent = AIAgent()
            ai_result = await agent.analyze_portfolio(wallet_address)
            
            # 3️⃣ Extract data from AI result (handles both unified and separate responses)
            # The AI result may contain 'ai_result' and 'simulation' keys, or be flat
            ai_data = ai_result.get("ai_result", ai_result)
            simulation = ai_result.get("simulation", {})
            
            # Extract values with safe defaults
            before_apy = simulation.get("before_total_apy", 0)
            after_apy = simulation.get("after_total_apy", 0)
            yield_increase = simulation.get("apy_increase", ai_data.get("expected_yield_increase", 0))
            expected_gain = simulation.get("expected_gain_usd", 0)
            confidence = ai_data.get("confidence", 0)
            recommendations = ai_data.get("recommendations", [])
            action = ai_data.get("action", "hold")
            
            # Extract AI reasoning fields
            ai_reasoning_obj = ai_data.get("ai_reasoning", {})
            category_analysis = ai_reasoning_obj.get("category_analysis", ai_data.get("category_analysis", ""))
            risk_assessment = ai_reasoning_obj.get("risk_assessment", ai_data.get("risk_assessment", ""))
            optimization_directions = ai_reasoning_obj.get("optimization_directions", ai_data.get("optimization_directions", []))
            ai_reasoning_text = ai_reasoning_obj.get("ai_reasoning", "")
            
            # Extract new fields
            estimated_yield_improvement = ai_data.get("estimated_yield_improvement", "")
            recommended_allocations = ai_data.get("recommended_allocations", {})
            
            # 4️⃣ Generate PDF with ReportLab
            logger.info("[REPORT] 🖨️ Generating enhanced PDF with ReportLab...")
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 0.75 * inch
            
            # Helper function to draw text with auto-pagination
            def write_line(text, size=10, bold=False, color_obj=colors.black, spacing=None, indent=0):
                nonlocal y
                if spacing is None:
                    spacing = size + 4
                
                if y < inch:  # New page if needed
                    c.showPage()
                    y = height - 0.75 * inch
                
                c.setFillColor(color_obj)
                font_name = f"Helvetica-Bold" if bold else "Helvetica"
                c.setFont(font_name, size)
                c.drawString(inch + indent, y, str(text))
                y -= spacing
            
            # Helper function to draw colored section header
            def draw_section_header(title, color_obj=colors.HexColor("#6366f1")):
                nonlocal y
                y -= 10
                if y < inch:
                    c.showPage()
                    y = height - 0.75 * inch
                
                c.setFillColor(color_obj)
                c.rect(inch - 5, y - 2, width - 2*inch + 10, 20, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(inch, y + 4, title)
                y -= 28
            
            # Helper function to draw summary box
            def draw_summary_box(label, value, box_color=colors.HexColor("#667eea")):
                nonlocal y
                y -= 5
                if y < 2*inch:
                    c.showPage()
                    y = height - 0.75 * inch
                
                # Draw colored box
                box_height = 40
                c.setFillColor(box_color)
                c.rect(inch, y - box_height + 10, 2*inch, box_height, fill=1, stroke=0)
                
                # Draw label
                c.setFillColor(colors.white)
                c.setFont("Helvetica", 9)
                c.drawString(inch + 10, y - 10, label)
                
                # Draw value
                c.setFont("Helvetica-Bold", 16)
                c.drawString(inch + 10, y - 30, value)
                
                y -= (box_height + 5)
            
            # === HEADER ===
            c.setFillColor(colors.HexColor("#667eea"))
            c.rect(0, height - 1.5*inch, width, 1.5*inch, fill=1, stroke=0)
            
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 24)
            c.drawString(inch, height - inch, "🧠 AI Portfolio Audit Report")
            
            c.setFont("Helvetica", 11)
            c.drawString(inch, height - 1.3*inch, "Comprehensive DeFi Portfolio Analysis powered by AI")
            
            y = height - 1.7 * inch
            
            # === META INFO ===
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            wallet_short = f"{wallet_address[:8]}...{wallet_address[-6:]}"
            
            write_line(f"Wallet: {wallet_short}", size=10, color_obj=colors.HexColor("#374151"))
            write_line(f"Generated: {timestamp}", size=10, color_obj=colors.HexColor("#374151"))
            write_line(f"AI Model: llama-3.3-70b-versatile", size=10, color_obj=colors.HexColor("#374151"))
            
            # === PORTFOLIO OVERVIEW ===
            draw_section_header("📊 Portfolio Overview", colors.HexColor("#6366f1"))
            
            # Get total value from portfolio or calculate from holdings
            total_value = portfolio.get("total_value_usd", portfolio.get("total_value", 0))
            if total_value == 0 and portfolio.get("holdings"):
                # Calculate from holdings if total_value is 0
                total_value = sum(h.get("value_usd", 0) for h in portfolio.get("holdings", []))
            
            write_line(f"Total Value: ${total_value:,.2f}", bold=True, size=14, color_obj=colors.HexColor("#10b981"))
            y -= 5
            
            # Holdings table
            holdings = portfolio.get("holdings", [])
            if holdings:
                write_line("Holdings:", bold=True, size=11)
                y -= 5
                
                for h in holdings[:10]:  # Limit to 10 holdings
                    protocol = h.get("protocol", "Unknown")
                    symbol = h.get("symbol", "")
                    balance = h.get("balance", 0)
                    value_usd = h.get("value_usd", 0)
                    apy = h.get("apy", 0)
                    
                    holding_text = f"• {protocol} ({symbol}): {balance:.4f} = ${value_usd:,.2f} | APY: {apy:.2f}%"
                    write_line(holding_text, size=9, indent=10)
            else:
                write_line("No holdings found for this wallet.", size=9, color_obj=colors.grey, indent=10)
            
            # === AI ANALYSIS SUMMARY (with summary boxes) ===
            draw_section_header("📈 AI Analysis Summary", colors.HexColor("#3b82f6"))
            
            # Summary boxes for key metrics
            y -= 10
            write_line("Key Performance Metrics:", bold=True, size=11)
            y -= 5
            
            # Action - Always show REBALANCE
            write_line(f"Recommended Action: REBALANCE", bold=True, size=11, indent=10, color_obj=colors.HexColor("#6366f1"))
            # Before APY
            write_line(f"Weighted APY (Before): {before_apy:.2f}%", size=10, indent=10)
            # After APY
            write_line(f"Weighted APY (After):  {after_apy:.2f}%", size=10, indent=10, color_obj=colors.HexColor("#10b981"))
            # AI Estimated Yield Improvement
            if estimated_yield_improvement:
                write_line(f"AI Estimated Improvement: {estimated_yield_improvement}", bold=True, size=11, indent=10, color_obj=colors.HexColor("#10b981"))
            # Yield increase
            write_line(f"Calculated Yield Increase: +{yield_increase:.2f}%", bold=True, size=11, indent=10, color_obj=colors.HexColor("#10b981"))
            # Expected gain
            write_line(f"Expected Annual Gain: ${expected_gain:,.2f}", bold=True, size=11, indent=10, color_obj=colors.HexColor("#10b981"))
            # Confidence
            write_line(f"AI Confidence: {confidence * 100:.0f}%", bold=True, size=11, indent=10, color_obj=colors.HexColor("#6366f1"))
            
            # === RECOMMENDED ALLOCATIONS ===
            if recommended_allocations and len(recommended_allocations) > 0:
                y -= 10
                draw_section_header("🎯 Recommended Portfolio Allocation", colors.HexColor("#10b981"))
                write_line("Suggested rebalancing to optimize yield:", size=10)
                y -= 5
                for protocol, percentage in recommended_allocations.items():
                    write_line(f"• {protocol}: {percentage}", size=10, indent=10, bold=True)
                y -= 5
            
            # === AI REASONING ===
            draw_section_header("🧠 AI Reasoning", colors.HexColor("#8b5cf6"))
            
            # Category Analysis
            if category_analysis:
                write_line("Category Analysis:", bold=True, size=10)
                # Wrap text
                words = category_analysis.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if len(test_line) > 90:
                        write_line(line.strip(), size=9, indent=10)
                        line = word + " "
                    else:
                        line = test_line
                if line:
                    write_line(line.strip(), size=9, indent=10)
                y -= 5
            
            # Optimization Directions (Actionable Insights)
            if optimization_directions and len(optimization_directions) > 0:
                y -= 5
                write_line("Actionable Recommendations:", bold=True, size=10, color_obj=colors.HexColor("#10b981"))
                for i, direction in enumerate(optimization_directions[:5], 1):
                    write_line(f"{i}. {direction}", size=9, indent=10)
                y -= 5
            
            # AI Reasoning Text
            if ai_reasoning_text:
                y -= 5
                write_line("AI Strategic Analysis:", bold=True, size=10)
                words = ai_reasoning_text.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if len(test_line) > 90:
                        write_line(line.strip(), size=9, indent=10)
                        line = word + " "
                    else:
                        line = test_line
                if line:
                    write_line(line.strip(), size=9, indent=10)
                y -= 5
            
            # Risk Assessment
            if risk_assessment:
                write_line("Risk Assessment:", bold=True, size=10)
                words = risk_assessment.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if len(test_line) > 90:
                        write_line(line.strip(), size=9, indent=10)
                        line = word + " "
                    else:
                        line = test_line
                if line:
                    write_line(line.strip(), size=9, indent=10)
            
            # === DETAILED RECOMMENDATIONS ===
            draw_section_header("💡 Detailed Rebalancing Actions", colors.HexColor("#10b981"))
            
            # Handle both list of strings and list of dicts
            if recommendations:
                for i, rec in enumerate(recommendations[:8], 1):  # Limit to 8
                    if isinstance(rec, dict):
                        from_p = rec.get("from", "Unknown")
                        to_p = rec.get("to", "Unknown")
                        percent = rec.get("percent", 0)
                        reason = rec.get("reason", "")
                        rec_text = f"{i}. Move {percent}% from {from_p} → {to_p}"
                        if reason:
                            rec_text += f" ({reason})"
                        write_line(rec_text, size=9, indent=10)
                    else:
                        write_line(f"{i}. {rec}", size=9, indent=10)
            elif optimization_directions:
                for i, direction in enumerate(optimization_directions[:8], 1):
                    write_line(f"{i}. {direction}", size=9, indent=10)
            else:
                write_line("No specific recommendations. Portfolio appears well-balanced.", size=9, indent=10, color_obj=colors.grey)
            
            # === NEXT STEPS ===
            draw_section_header("🎯 Recommended Next Steps", colors.HexColor("#6366f1"))
            
            next_steps = [
                "Review and implement suggested rebalancing strategies",
                "Monitor portfolio performance over the next 24-48 hours",
                "Re-run AI analysis weekly or when market conditions change",
                "Consider diversification opportunities in emerging protocols",
                "Set up automated alerts for significant APY changes"
            ]
            
            for step in next_steps:
                write_line(f"✓ {step}", size=9, indent=10, color_obj=colors.HexColor("#059669"))
            
            # === FOOTER ===
            y = 0.75 * inch
            c.setFillColor(colors.HexColor("#e5e7eb"))
            c.rect(0, 0, width, 0.6*inch, fill=1, stroke=0)
            
            c.setFillColor(colors.HexColor("#6366f1"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(inch, 0.4*inch, "AutoDeFi.AI")
            
            c.setFillColor(colors.HexColor("#6b7280"))
            c.setFont("Helvetica", 8)
            c.drawString(inch, 0.25*inch, f"{timestamp} | Powered by Groq LLaMA 3.3 70B")
            
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(inch, 0.12*inch, "This report is for informational purposes only. Always conduct your own research.")
            
            # Save PDF
            c.save()
            buffer.seek(0)
            
            filename = f"audit_report_{wallet_address[:8]}_{datetime.utcnow().strftime('%Y%m%d%H%M')}.pdf"
            logger.info(f"[REPORT] ✅ Enhanced report generated successfully: {filename}")
            
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Access-Control-Expose-Headers": "Content-Disposition"
                }
            )
        
        except Exception as e:
            logger.error(f"[REPORT] ❌ Failed to generate report: {e}", exc_info=True)
            raise Exception(f"Failed to generate audit report: {str(e)}")
    
    async def generate_vault_report(self, vault_id: int) -> StreamingResponse:
        """
        Generate audit report for a specific AI vault (simplified version)
        
        Args:
            vault_id: Vault ID to generate report for
            
        Returns:
            StreamingResponse with PDF file
        """
        try:
            logger.info(f"[REPORT] 📊 Generating vault report for vault #{vault_id}...")
            
            # TODO: Implement vault report with ReportLab
            # For now, return a simple placeholder
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, height - inch, f"AI Vault Report #{vault_id}")
            c.setFont("Helvetica", 12)
            c.drawString(inch, height - 1.5*inch, "Coming soon with full ReportLab implementation")
            
            c.save()
            buffer.seek(0)
            
            filename = f"vault_report_{vault_id}.pdf"
            logger.info(f"[REPORT] ✅ Vault report placeholder generated")
            
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Access-Control-Expose-Headers": "Content-Disposition"
                }
            )
        
        except Exception as e:
            logger.error(f"[REPORT] ❌ Failed to generate vault report: {e}", exc_info=True)
            raise Exception(f"Failed to generate vault report: {str(e)}")


# Singleton instance
report_service = ReportService()
