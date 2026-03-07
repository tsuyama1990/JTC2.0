import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.constants import ERR_LLM_RESPONSE_TOO_LARGE
from src.core.llm import get_llm
from src.core.metrics import calculate_ltv, calculate_payback_period, calculate_roi
from src.core.services.file_service import FileService
from src.domain_models.metrics import FinancialEstimates, Financials, Metrics, RingiSho
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GovernanceAgent(BaseAgent):
    """
    Agent responsible for Governance and Ringi-sho generation.
    """

    def __init__(self, file_service: FileService | None = None) -> None:
        self.file_service = file_service or FileService()

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
        query = settings.governance.search_query_template.format(industry=industry)
        search_result = search.safe_search(query)

        # Limit search result size to prevent Context Window overflow
        # Explicit truncation as per audit requirement
        limit = settings.governance.max_search_result_size
        if len(search_result) > limit:
            logger.warning(f"Search result truncated to {limit} characters.")
            search_result = search_result[:limit]

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
        self._save_to_file(ringi_sho)

        # 6. Update State
        updated_metrics = state.metrics_data.model_copy() if state.metrics_data else Metrics()
        updated_metrics.financials = financials

        return {"ringi_sho": ringi_sho, "metrics_data": updated_metrics}

    def _get_industry_context(self, state: GlobalState) -> str:
        import re

        industry = state.topic
        if state.selected_idea:
            industry = f"{state.selected_idea.customer_segments} related to {state.topic}"

        # Security: Whitelist characters to prevent injection attacks (alphanumeric and spaces only)
        # As per audit requirement to remove dangerous chars like . and ,
        sanitized = re.sub(r"[^a-zA-Z0-9\s]", "", industry)
        return sanitized.strip()

    def _estimate_financials(self, industry: str, search_result: str) -> Financials:
        settings = get_settings()

        prompt = (
            f"Context: Startup idea in {industry}.\n"
            f"Search Data: {search_result}\n\n"
            "Task: Estimate conservative financial metrics for a Seed stage startup.\n"
            "Return ONLY a JSON object with keys: 'cac' (float), 'arpu' (float), 'churn_rate' (float between 0.0 and 1.0).\n"
            "Do not include markdown formatting or explanations."
        )

        try:
            estimates = self._safe_llm_call(prompt, FinancialEstimates)
            cac, arpu, churn = estimates.cac, estimates.arpu, estimates.churn_rate
        except Exception:
            logger.exception("Financial estimation failed. Using defaults.")
            cac = settings.governance.default_cac
            arpu = settings.governance.default_arpu
            churn = settings.governance.default_churn

        ltv = calculate_ltv(arpu, churn)
        payback = calculate_payback_period(cac, arpu)
        roi = calculate_roi(ltv, cac)

        return Financials(cac=cac, ltv=ltv, payback_months=payback, roi=roi)

    def _generate_ringi_sho(
        self, state: GlobalState, financials: Financials, status: str
    ) -> RingiSho:
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
            # We use a temporary Pydantic model for parsing the specific Ringi-Sho structure expected from LLM
            # Since RingiSho model requires 'financial_projection', we parse a partial model first
            class PartialRingi(BaseModel):
                title: str
                executive_summary: str
                risks: list[str]

            partial = self._safe_llm_call(prompt, PartialRingi)

            return RingiSho(
                title=partial.title,
                executive_summary=partial.executive_summary,
                financial_projection=financials,
                risks=partial.risks,
                approval_status=status,
            )
        except Exception:
            logger.exception("Ringi-Sho generation failed. Using fallback.")
            return RingiSho(
                title=f"Proposal for {idea_title}",
                executive_summary="Auto-generated summary failed.",
                financial_projection=financials,
                risks=["Generation Error"],
                approval_status=status,
            )

    def _safe_llm_call(self, prompt: str, model_class: type[T]) -> T:
        """
        Execute LLM call safely with streaming size validation and Pydantic parsing.

        Args:
            prompt: Input prompt.
            model_class: Pydantic model to validate response against.

        Returns:
            Validated Pydantic model instance.

        Raises:
            ValueError: If response is too large.
            JSONDecodeError: If parsing fails.
            ValidationError: If schema validation fails.
        """
        settings = get_settings()
        llm = get_llm()

        content = ""
        max_bytes = settings.governance.max_llm_response_size

        # Memory Safety: Stream and check incremental size
        # Note: llm.stream() returns an iterator of chunks (AIMessageChunk)
        for chunk in llm.stream(prompt):
            chunk_content = str(chunk.content)
            content += chunk_content
            if len(content.encode("utf-8")) > max_bytes:
                logger.error(ERR_LLM_RESPONSE_TOO_LARGE)
                raise ValueError(ERR_LLM_RESPONSE_TOO_LARGE)

        data_dict = self._parse_json(content)
        return model_class.model_validate(data_dict)

    def _parse_json(self, text: str) -> dict[str, Any]:
        """
        Helper to parse JSON from LLM response.
        Uses regex to extract JSON block for robustness.

        Raises:
            JSONDecodeError: If parsing fails.
        """
        import re

        # Try finding JSON block first
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # Fallback: Try finding any code block
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)

        # Strip whitespace
        text = text.strip()
        return json.loads(text)  # type: ignore

    def _save_to_file(self, ringi: RingiSho) -> None:
        """
        Save Ringi-Sho to file using FileService.
        """
        settings = get_settings()

        # Optimize string construction
        lines = [
            f"# {ringi.title}",
            "",
            f"**Status:** {ringi.approval_status}",
            "",
            "## Executive Summary",
            f"{ringi.executive_summary}",
            "",
            "## Financial Projections",
            f"- **ROI:** {ringi.financial_projection.roi:.2f}x",
            f"- **LTV:** ${ringi.financial_projection.ltv:.2f}",
            f"- **CAC:** ${ringi.financial_projection.cac:.2f}",
            f"- **Payback:** {ringi.financial_projection.payback_months:.1f} months",
            "",
            "## Risks",
        ]
        lines.extend([f"- {risk}" for risk in ringi.risks])

        content = "\n".join(lines)

        self.file_service.save_text_async(content, settings.governance.output_path)
