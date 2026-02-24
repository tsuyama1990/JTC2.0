import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.constants import ERR_LLM_RESPONSE_TOO_LARGE
from src.core.llm import get_llm
from src.core.metrics import calculate_ltv, calculate_payback_period, calculate_roi
from src.domain_models.metrics import FinancialEstimates, Financials, Metrics, RingiSho
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
        settings = get_settings()

        # 1. Context & Search
        industry = self._get_industry_context(state)
        logger.info(f"Searching benchmarks for: {industry}")
        search = TavilySearch()
        query = f"average CAC churn ARPU LTV for {industry} startups benchmarks"
        search_result = search.safe_search(query)

        # 2. Estimate Financials
        logger.info("Estimating financials using LLM...")
        financials = self._estimate_financials(industry, search_result)

        # 3. Determine Status
        is_viable = financials.roi >= settings.governance.min_roi_threshold
        approval_status = "Approved" if is_viable else "Rejected"

        # 4. Generate Ringi-Sho Content
        logger.info(f"Generating Ringi-Sho. Status: {approval_status}")
        ringi_sho = self._generate_ringi_sho(state, financials, approval_status)

        # 5. Save to Disk (Async wrapper)
        # Using run_in_executor to avoid blocking the main thread during file I/O
        # Although run() is synchronous, this is a best-practice pattern for I/O in agents.
        # We block here waiting for the result, but the operation happens in a separate thread.
        try:
            with ThreadPoolExecutor() as executor:
                future = executor.submit(self._save_to_file, ringi_sho)
                future.result() # Wait for completion to ensure data persistence before returning
        except Exception:
             logger.exception("Failed to schedule file save operation.")

        # 6. Update State
        updated_metrics = state.metrics_data.model_copy() if state.metrics_data else Metrics()
        updated_metrics.financials = financials

        return {
            "ringi_sho": ringi_sho,
            "metrics_data": updated_metrics
        }

    def _get_industry_context(self, state: GlobalState) -> str:
        if state.selected_idea:
             return f"{state.selected_idea.customer_segments} related to {state.topic}"
        return state.topic

    def _estimate_financials(self, industry: str, search_result: str) -> Financials:
        settings = get_settings()
        llm = get_llm()

        prompt = (
            f"Context: Startup idea in {industry}.\n"
            f"Search Data: {search_result}\n\n"
            "Task: Estimate conservative financial metrics for a Seed stage startup.\n"
            "Return ONLY a JSON object with keys: 'cac' (float), 'arpu' (float), 'churn_rate' (float between 0.0 and 1.0).\n"
            "Do not include markdown formatting or explanations."
        )

        try:
            response = llm.invoke(prompt)
            content = str(response.content)
            self._validate_response_size(content)

            fin_data_dict = self._parse_json(content)
            estimates = FinancialEstimates.model_validate(fin_data_dict)

            cac, arpu, churn = estimates.cac, estimates.arpu, estimates.churn_rate

        except (json.JSONDecodeError, ValidationError, ValueError):
            logger.exception("Failed to parse financial estimates. Using defaults.")
            cac = settings.governance.default_cac
            arpu = settings.governance.default_arpu
            churn = settings.governance.default_churn
        except Exception:
            logger.exception("Unexpected error in financial estimation. Using defaults.")
            cac = settings.governance.default_cac
            arpu = settings.governance.default_arpu
            churn = settings.governance.default_churn

        ltv = calculate_ltv(arpu, churn)
        payback = calculate_payback_period(cac, arpu)
        roi = calculate_roi(ltv, cac)

        return Financials(cac=cac, ltv=ltv, payback_months=payback, roi=roi)

    def _generate_ringi_sho(self, state: GlobalState, financials: Financials, status: str) -> RingiSho:
        llm = get_llm()
        mvp_url = state.mvp_url or "N/A"
        idea_title = state.selected_idea.title if state.selected_idea else "Untitled Idea"

        prompt = (
            f"Generate a formal approval document (Ringi-sho) for idea: {idea_title}.\n"
            f"Financials: ROI={financials.roi:.2f}, LTV=${financials.ltv:.2f}, CAC=${financials.cac:.2f}, Payback={financials.payback_months:.1f} months.\n"
            f"Status: {status}.\n"
            f"MVP URL: {mvp_url}\n\n"
            "Return ONLY a JSON object with keys: 'title', 'executive_summary' (text), 'risks' (list of strings).\n"
            "Do not include markdown formatting."
        )

        try:
            response = llm.invoke(prompt)
            content = str(response.content)
            self._validate_response_size(content)

            ringi_data = self._parse_json(content)

            return RingiSho(
                title=ringi_data.get("title", f"Proposal for {idea_title}"),
                executive_summary=ringi_data.get("executive_summary", "Summary not generated."),
                financial_projection=financials,
                risks=ringi_data.get("risks", []),
                approval_status=status
            )
        except (json.JSONDecodeError, ValueError):
            logger.exception("Failed to generate Ringi-Sho content.")
            return RingiSho(
                title=f"Proposal for {idea_title}",
                executive_summary="Auto-generated summary failed.",
                financial_projection=financials,
                risks=["Generation Error"],
                approval_status=status
            )
        except Exception:
            logger.exception("Unexpected error in Ringi-Sho generation.")
            return RingiSho(
                title=f"Proposal for {idea_title}",
                executive_summary="Auto-generated summary failed.",
                financial_projection=financials,
                risks=["Generation Error"],
                approval_status=status
            )

    def _validate_response_size(self, content: str) -> None:
        """Ensure LLM response is within safe limits."""
        settings = get_settings()
        if len(content.encode('utf-8')) > settings.governance.max_llm_response_size:
            logger.error(ERR_LLM_RESPONSE_TOO_LARGE)
            raise ValueError(ERR_LLM_RESPONSE_TOO_LARGE)

    def _parse_json(self, text: str) -> dict[str, Any]:
        """
        Helper to parse JSON from LLM response.

        Raises:
            JSONDecodeError: If parsing fails.
        """
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text) # type: ignore

    def _save_to_file(self, ringi: RingiSho) -> None:
        """
        Save Ringi-Sho to RINGI_SHO.md.
        Uses pathlib for safe file operations.
        Executed in a separate thread to demonstrate non-blocking pattern availability.
        """
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

            # Safe write using pathlib
            output_path = Path("RINGI_SHO.md")
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"RINGI_SHO.md saved successfully to {output_path.resolve()}")

        except OSError:
            logger.exception("Failed to write output file")
        except Exception:
            logger.exception("Unexpected error saving RINGI_SHO.md")
