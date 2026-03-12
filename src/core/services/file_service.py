import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError
from src.core.interfaces import IPDFGenerator
from src.domain_models.agent_prompt_spec import AgentPromptSpec
from src.domain_models.alternative_analysis import AlternativeAnalysis
from src.domain_models.experiment_plan import ExperimentPlan
from src.domain_models.persona import Persona
from src.domain_models.value_proposition_canvas import ValuePropositionCanvas

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Uses ThreadPoolExecutor for non-blocking I/O in async contexts.
    """

    def __init__(self, pdf_generator: IPDFGenerator) -> None:
        # Max workers scales with CPU count to avoid thread starvation under load
        max_workers = (os.cpu_count() or 1) * 2 + 1
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.settings = get_settings()

        self.pdf_generator = pdf_generator

    def shutdown(self) -> None:
        """Shutdown the executor gracefully."""
        self._executor.shutdown(wait=True)

    def __del__(self) -> None:
        try:
            # Check if _executor still exists during interpreter shutdown
            if hasattr(self, "_executor"):
                self.shutdown()
        except Exception:
            pass

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal.
        """
        import os
        try:
            raw_path = Path(path)

            base_dir = Path.cwd().resolve(strict=True)
            # Check the output_dir using strict=False, allowing outputs to not exist yet
            output_dir = (base_dir / self.settings.canvas_output_dir).resolve(strict=False)

            # Convert input to string and use os.path.realpath for canonical resolution
            # Realpath resolves all symlinks safely without needing the file to exist.
            canonical_str = os.path.realpath(str(raw_path))
            p = Path(canonical_str)

            if not p.is_relative_to(output_dir) and not p.is_relative_to(base_dir):
                msg = f"Invalid path: Path traversal detected: {path}"
                raise ConfigurationError(msg)

        except (ValueError, RuntimeError, OSError) as e:
            msg = f"Invalid path: {e}"
            raise ConfigurationError(msg) from e
        else:
            return p

    def save_text_async(self, content: str, path: str | Path) -> None:
        """
        Save text to a file asynchronously using a thread pool.
        This prevents blocking the main event loop during file I/O.

        Args:
            content: The string content to write.
            path: The destination file path.
        """
        try:
            valid_path = self._validate_path(path)
            self._executor.submit(self._save_text_sync, content, valid_path)
        except Exception:
            logger.exception("Failed to schedule file save")

    def _save_text_sync(self, content: str, path: Path) -> None:
        """
        Synchronous implementation of save text.
        Includes simple retry logic for robustness and uses atomic file writes via a single temp file.
        """
        import os
        import uuid

        attempts = 3
        path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(attempts):
            try:
                # Create a temporary file securely in the target directory
                temp_path = path.parent / f".tmp_{uuid.uuid4().hex}.txt"

                # Write fully to temporary file (atomic write logic)
                with temp_path.open("w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())

                # Atomically replace destination with temp file
                temp_path.replace(path)
                break

            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                if 'temp_path' in locals() and temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                break
            except OSError:
                if attempt == attempts - 1:
                    logger.exception(f"Failed to write to {path} after {attempts} attempts")
                if 'temp_path' in locals() and temp_path.exists():
                    temp_path.unlink(missing_ok=True)
            except Exception:
                logger.exception("Unexpected error during file write")
                if 'temp_path' in locals() and temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                break

    def _sanitize_md(self, text: str) -> str:
        """
        Sanitizes user input for Markdown generation.
        Escapes HTML and Markdown control characters to prevent injection.
        """
        import html
        import re

        if not text:
            return ""

        # Use comprehensive HTML escaping
        escaped = html.escape(text, quote=True)

        # Escape all Markdown control characters
        markdown_chars = r"\`*_{}[]()#+-.!|"
        for char in markdown_chars:
            escaped = escaped.replace(char, f"\\{char}")

        # Remove any lingering tag-like structures
        return re.sub(r"<[^>]+>", "", escaped)

    def _validate_and_sanitize_content(self, content: str, max_length: int = 1000) -> str:
        if not isinstance(content, str):
            msg = "Content must be a string"
            raise TypeError(msg)
        if len(content) > max_length:
            msg = f"Content exceeds maximum length of {max_length}"
            raise ValueError(msg)
        return self._sanitize_md(content)

    def generate_agent_prompt_spec_md(
        self,
        spec: AgentPromptSpec,
        output_dir: str | Path,
    ) -> Path:
        """
        Generate AgentPromptSpec.md file from the AgentPromptSpec schema.
        """
        try:
            target_dir = self._validate_path(output_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            output_path = target_dir / "AgentPromptSpec.md"

            content = [
                "# 🤖 System & Context\n",
                "- Role: Expert Frontend Engineer & UI/UX Designer",
                "- Stack: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Lucide-react",
                "- Principles: One Feature One Value, Mobile First, Accessible (WCAG 2.1)",
                f"- Routing & Components: {self._validate_and_sanitize_content(spec.routing_and_constraints)}\n",
                "# 🗺️ Sitemap & Information Architecture\n",
                f"{self._validate_and_sanitize_content(spec.sitemap)}\n",
                "# 🎯 Core User Story\n",
                f"- As a: {self._validate_and_sanitize_content(spec.core_user_story.as_a)}",
                f"- I want to: {self._validate_and_sanitize_content(spec.core_user_story.i_want_to)}",
                f"- So that: {self._validate_and_sanitize_content(spec.core_user_story.so_that)}",
                f"- Target Route: {self._validate_and_sanitize_content(spec.core_user_story.target_route)}",
                "- Acceptance Criteria:",
            ]
            for ac in spec.core_user_story.acceptance_criteria:
                content.append(f"  - {self._validate_and_sanitize_content(ac)}")

            content.extend(
                [
                    "\n# 📊 Data Schema & Flow\n",
                    "Validation Rules:",
                    f"{self._validate_and_sanitize_content(spec.validation_rules)}\n",
                    "🔄 State Machine (Mermaid)\n",
                    "```mermaid",
                    self._validate_and_sanitize_content(
                        spec.mermaid_flowchart.replace("```mermaid", "").replace("```", "").strip()
                    ),
                    "```\n",
                    "🖥️ UI Structure & States",
                    f"Success State: {self._validate_and_sanitize_content(spec.state_machine.success)}",
                    f"Loading State: {self._validate_and_sanitize_content(spec.state_machine.loading)}",
                    f"Empty State: {self._validate_and_sanitize_content(spec.state_machine.empty)}",
                    f"Error State: {self._validate_and_sanitize_content(spec.state_machine.error)}",
                ]
            )

            self._save_text_sync("\n".join(content), output_path)
            logger.info(f"AgentPromptSpec MD generated successfully at {output_path}")
        except Exception:
            logger.exception("Failed to generate AgentPromptSpec MD")
            raise
        else:
            return output_path

    def generate_experiment_plan_md(
        self,
        plan: ExperimentPlan,
        output_dir: str | Path,
    ) -> Path:
        """
        Generate EXPERIMENT_PLAN.md file from the ExperimentPlan schema.
        """
        try:
            target_dir = self._validate_path(output_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            output_path = target_dir / "EXPERIMENT_PLAN.md"

            content = [
                "# 🧪 MVP Experiment Plan\n",
                f"**Riskiest Assumption:** {self._validate_and_sanitize_content(plan.riskiest_assumption)}",
                f"**Experiment Type:** {self._validate_and_sanitize_content(plan.experiment_type)}",
                f"**Acquisition Channel:** {self._validate_and_sanitize_content(plan.acquisition_channel)}",
                f"**Pivot Condition:** {self._validate_and_sanitize_content(plan.pivot_condition)}\n",
                "## 📈 AARRR Metrics Framework\n",
            ]
            for metric in plan.aarrr_metrics:
                content.append(f"### {self._validate_and_sanitize_content(metric.metric_name)}")
                content.append(
                    f"- **Target:** {self._validate_and_sanitize_content(metric.target_value)}"
                )
                content.append(
                    f"- **Method:** {self._validate_and_sanitize_content(metric.measurement_method)}\n"
                )

            self._save_text_sync("\n".join(content), output_path)
            logger.info(f"EXPERIMENT_PLAN MD generated successfully at {output_path}")
        except Exception:
            logger.exception("Failed to generate EXPERIMENT_PLAN MD")
            raise
        else:
            return output_path

    def _validate_string(self, value: str, max_length: int = 1000) -> str:
        """Validate strings before rendering into PDFs to prevent injection/formatting errors."""
        import re
        import unicodedata
        import urllib.parse

        if not isinstance(value, str):
            msg = "Expected string value"
            raise TypeError(msg)
        if len(value) > max_length:
            msg = f"String exceeds maximum length of {max_length}"
            raise ValueError(msg)

        # Decode any URL-encoded characters to prevent bypass
        decoded_value = urllib.parse.unquote(value)

        # Unicode normalization
        normalized = unicodedata.normalize("NFKC", decoded_value)

        # Remove control characters dynamically
        value = "".join(c for c in normalized if unicodedata.category(c)[0] != "C" or c in "\n\t\r")

        # Explicitly search for malicious structural PDF tags and logic controls
        if re.search(r"(/Type\b|/Action\b|/S\b|/JavaScript\b|/JS\b|<|>|\\|/)", value):
            msg = "String contains suspicious characters"
            raise ValueError(msg)

        return value

    def _sanitize_for_pdf(self, text: str) -> str:
        import unicodedata

        if not isinstance(text, str):
            return ""

        # Unicode normalization and strict dropping of unprintables/control characters
        normalized = unicodedata.normalize("NFKC", text)
        text = "".join(
            c for c in normalized if unicodedata.category(c)[0] != "C" and c.isprintable()
        )

        # Escape any special characters that could affect PDF rendering
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _render_persona_section(self, pdf: IPDFGenerator, persona: Persona) -> None:
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(w=200, h=10, text="1. Target Persona", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        name = self._sanitize_for_pdf(self._validate_string(persona.name, 100))
        occupation = self._sanitize_for_pdf(self._validate_string(persona.occupation, 100))
        demographics = self._sanitize_for_pdf(self._validate_string(persona.demographics))
        bio = self._sanitize_for_pdf(self._validate_string(persona.bio))
        goals = ", ".join(
            self._sanitize_for_pdf(self._validate_string(g, 200)) for g in persona.goals
        )
        frustrations = ", ".join(
            self._sanitize_for_pdf(self._validate_string(f, 200)) for f in persona.frustrations
        )

        pdf.multi_cell(w=0, h=10, text=f"Name: {name} | Occupation: {occupation}")
        pdf.multi_cell(w=0, h=10, text=f"Demographics: {demographics}")
        pdf.multi_cell(w=0, h=10, text=f"Bio: {bio}")
        pdf.multi_cell(w=0, h=10, text=f"Goals: {goals}")
        pdf.multi_cell(w=0, h=10, text=f"Frustrations: {frustrations}")
        pdf.ln(5)

    def _render_analysis_section(self, pdf: IPDFGenerator, analysis: AlternativeAnalysis) -> None:
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(
            w=200, h=10, text="2. Alternative Analysis", new_x="LMARGIN", new_y="NEXT", align="L"
        )
        pdf.set_font("Helvetica", size=12)
        for alt in analysis.current_alternatives:
            t_name = self._sanitize_for_pdf(self._validate_string(alt.name, 100))
            t_cost = self._sanitize_for_pdf(self._validate_string(alt.financial_cost, 200))
            t_time = self._sanitize_for_pdf(self._validate_string(alt.time_cost, 200))
            t_ux = self._sanitize_for_pdf(self._validate_string(alt.ux_friction, 200))
            pdf.multi_cell(
                w=0,
                h=10,
                text=f"- Tool: {t_name} | Cost: {t_cost} | Time: {t_time} | UX Friction: {t_ux}",
            )
        switching_cost = self._sanitize_for_pdf(self._validate_string(analysis.switching_cost))
        ten_x_value = self._sanitize_for_pdf(self._validate_string(analysis.ten_x_value))
        pdf.multi_cell(w=0, h=10, text=f"Switching Cost: {switching_cost}")
        pdf.multi_cell(w=0, h=10, text=f"10x Value: {ten_x_value}")
        pdf.ln(5)

    def _render_vpc_section(self, pdf: IPDFGenerator, vpc: ValuePropositionCanvas) -> None:
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(
            w=200,
            h=10,
            text="3. Value Proposition Canvas",
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
        )

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Customer Profile:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        jobs = ", ".join(
            self._sanitize_for_pdf(self._validate_string(j, 200))
            for j in vpc.customer_profile.customer_jobs
        )
        pains = ", ".join(
            self._sanitize_for_pdf(self._validate_string(p, 200))
            for p in vpc.customer_profile.pains
        )
        gains = ", ".join(
            self._sanitize_for_pdf(self._validate_string(g, 200))
            for g in vpc.customer_profile.gains
        )
        pdf.multi_cell(w=0, h=10, text=f"Jobs: {jobs}")
        pdf.multi_cell(w=0, h=10, text=f"Pains: {pains}")
        pdf.multi_cell(w=0, h=10, text=f"Gains: {gains}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Value Map:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        products = ", ".join(
            self._sanitize_for_pdf(self._validate_string(p, 200))
            for p in vpc.value_map.products_and_services
        )
        pain_relievers = ", ".join(
            self._sanitize_for_pdf(self._validate_string(p, 200))
            for p in vpc.value_map.pain_relievers
        )
        gain_creators = ", ".join(
            self._sanitize_for_pdf(self._validate_string(g, 200))
            for g in vpc.value_map.gain_creators
        )
        pdf.multi_cell(w=0, h=10, text=f"Products & Services: {products}")
        pdf.multi_cell(w=0, h=10, text=f"Pain Relievers: {pain_relievers}")
        pdf.multi_cell(w=0, h=10, text=f"Gain Creators: {gain_creators}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Fit Evaluation:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        fit_evaluation = self._sanitize_for_pdf(self._validate_string(vpc.fit_evaluation))
        pdf.multi_cell(w=0, h=10, text=fit_evaluation)

    def generate_vpc_pdf(
        self,
        persona: Persona,
        analysis: AlternativeAnalysis,
        vpc: ValuePropositionCanvas,
        output_dir: str | Path,
    ) -> Path:
        """
        Generate a PDF containing Persona, Alternative Analysis, and Value Proposition Canvas.
        """
        pdf = self.pdf_generator
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        self._render_persona_section(pdf, persona)
        self._render_analysis_section(pdf, analysis)
        self._render_vpc_section(pdf, vpc)

        # Resolve path safely
        try:
            target_dir = self._validate_path(output_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            output_path = target_dir / "value_proposition_canvas.pdf"

            # Use unicode encoding and fallback characters to avoid latin-1 errors
            # fpdf2 supports unicode
            pdf.output(str(output_path))
            logger.info(f"VPC PDF generated successfully at {output_path}")
        except Exception:
            logger.exception("Failed to generate VPC PDF")
            raise
        else:
            return output_path
