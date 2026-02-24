import json
import logging
from pathlib import Path
from typing import Any

from src.agents.base import BaseAgent
from src.core.llm import get_llm
from src.core.metrics import calculate_ltv, calculate_payback_period, calculate_roi
from src.domain_models.metrics import Financials, Metrics, RingiSho
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch

logger = logging.getLogger(__name__)


class GovernanceAgent(BaseAgent):
    """
    Agent responsible for Governance and Ringi-sho generation.
    """

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run the governance check logic.
        """
        logger.info("Governance Agent: Starting analysis...")

        # 1. Context
        industry = state.topic
        if state.selected_idea:
             industry = f"{state.selected_idea.customer_segments} related to {state.topic}"

        # 2. Search Benchmarks
        logger.info(f"Searching benchmarks for: {industry}")
        search = TavilySearch()
        query = f"average CAC churn ARPU LTV for {industry} startups benchmarks"
        search_result = search.safe_search(query)

        # 3. Estimate Financials
        logger.info("Estimating financials using LLM...")
        llm = get_llm()

        prompt_financials = (
            f"Context: Startup idea in {industry}.\n"
            f"Search Data: {search_result}\n\n"
            "Task: Estimate conservative financial metrics for a Seed stage startup.\n"
            "Return ONLY a JSON object with keys: 'cac' (float), 'arpu' (float), 'churn_rate' (float between 0.0 and 1.0).\n"
            "Do not include markdown formatting or explanations."
        )

        try:
            response_fin = llm.invoke(prompt_financials)
            fin_data = self._parse_json(str(response_fin.content))

            cac = float(fin_data.get("cac", 500.0))
            arpu = float(fin_data.get("arpu", 50.0))
            churn = float(fin_data.get("churn_rate", 0.05))

        except Exception:
            logger.exception("Failed to parse financial estimates. Using defaults.")
            cac, arpu, churn = 500.0, 50.0, 0.05

        # 4. Calculate Derived Metrics
        ltv = calculate_ltv(arpu, churn)
        payback = calculate_payback_period(cac, arpu)
        roi = calculate_roi(ltv, cac)

        financials = Financials(
            cac=cac,
            ltv=ltv,
            payback_months=payback,
            roi=roi
        )

        # 5. Determine Status
        # Simple rule: ROI > 3.0 is viable
        is_viable = roi >= 3.0
        approval_status = "Approved" if is_viable else "Rejected"

        # 6. Generate Ringi-Sho Content
        logger.info(f"Generating Ringi-Sho. Status: {approval_status}")

        mvp_url = state.mvp_url or "N/A"
        idea_title = state.selected_idea.title if state.selected_idea else "Untitled Idea"

        prompt_ringi = (
            f"Generate a formal approval document (Ringi-sho) for idea: {idea_title}.\n"
            f"Financials: ROI={roi:.2f}, LTV=${ltv:.2f}, CAC=${cac:.2f}, Payback={payback:.1f} months.\n"
            f"Status: {approval_status}.\n"
            f"MVP URL: {mvp_url}\n\n"
            "Return ONLY a JSON object with keys: 'title', 'executive_summary' (text), 'risks' (list of strings).\n"
            "Do not include markdown formatting."
        )

        try:
            response_ringi = llm.invoke(prompt_ringi)
            ringi_data = self._parse_json(str(response_ringi.content))

            ringi_sho = RingiSho(
                title=ringi_data.get("title", f"Proposal for {idea_title}"),
                executive_summary=ringi_data.get("executive_summary", "Summary not generated."),
                financial_projection=financials,
                risks=ringi_data.get("risks", []),
                approval_status=approval_status
            )
        except Exception:
            logger.exception("Failed to generate Ringi-Sho content.")
            ringi_sho = RingiSho(
                title=f"Proposal for {idea_title}",
                executive_summary="Auto-generated summary failed.",
                financial_projection=financials,
                risks=["Generation Error"],
                approval_status=approval_status
            )

        # 7. Save to Disk
        self._save_to_file(ringi_sho)

        # 8. Update State
        # Update metrics_data with new financials while preserving existing data.
        updated_metrics = state.metrics_data.model_copy() if state.metrics_data else Metrics()
        updated_metrics.financials = financials

        return {
            "ringi_sho": ringi_sho,
            "metrics_data": updated_metrics
        }

    def _parse_json(self, text: str) -> dict[str, Any]:
        """Helper to parse JSON from LLM response."""
        # Strip code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text) # type: ignore

    def _save_to_file(self, ringi: RingiSho) -> None:
        """Save Ringi-Sho to RINGI_SHO.md."""
        try:
            content = (
                f"# {ringi.title}\n\n"
                f"**Status:** {ringi.approval_status}\n\n"
                f"## Executive Summary\n{ringi.executive_summary}\n\n"
                f"## Financial Projections\n"
                f"- **ROI:** {ringi.financial_projection.roi:.2f}x\n"
                f"- **LTV:** ${ringi.financial_projection.ltv:.2f}\n"
                f"- **CAC:** ${ringi.financial_projection.cac:.2f}\n"
                f"- **Payback:** {ringi.financial_projection.payback_months:.1f} months\n\n"
                f"## Risks\n"
            )
            for risk in ringi.risks:
                content += f"- {risk}\n"

            Path("RINGI_SHO.md").write_text(content, encoding="utf-8")
            logger.info("RINGI_SHO.md saved successfully.")
        except Exception:
            logger.exception("Failed to save RINGI_SHO.md")
