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

    def __init__(self, pdf_generator: IPDFGenerator | None = None) -> None:
        # Max workers scales with CPU count to avoid thread starvation under load
        max_workers = (os.cpu_count() or 1) * 2 + 1
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.settings = get_settings()

        # Abstract PDF library dependency
        if pdf_generator is None:
            from fpdf import FPDF

            self.pdf_generator: IPDFGenerator = FPDF()  # type: ignore
        else:
            self.pdf_generator = pdf_generator

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal.
        """
        try:
            p = Path(path).resolve(strict=True)
            base_dir = Path.cwd().resolve(strict=True)
            if not p.is_relative_to(base_dir):
                msg = f"Path traversal detected: {path}"
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

    def _save_text_sync(self, content: str, path: Path) -> None:  # noqa: C901
        """
        Synchronous implementation of save text.
        Includes simple retry logic for robustness and uses atomic file writes.
        """
        import os
        import uuid

        attempts = 3
        def _raise_symlink_error(m: str) -> None:
            raise ConfigurationError(m)

        for attempt in range(attempts):
            temp_dir = None
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                parent_dir = path.parent.resolve(strict=True)

                if parent_dir.is_symlink() or (path.exists() and path.is_symlink()):
                    _raise_symlink_error(f"Symlink detected in path: {path}")

                # Create a temporary directory securely
                temp_dir = parent_dir / f".tmp_{uuid.uuid4().hex}"
                temp_dir.mkdir(mode=0o700)
                temp_path = temp_dir / f"tmp_{uuid.uuid4().hex}.txt"

                with temp_path.open("w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())

                # Verify final path is still safe
                base_dir = Path.cwd().resolve(strict=True)
                if not temp_path.parent.resolve(strict=True).is_relative_to(base_dir):
                    _raise_symlink_error("Path traversal detected during write")

                if path.is_symlink():
                    _raise_symlink_error(f"Target path is a symlink: {path}")

                temp_path.replace(path)
            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                return
            except OSError as e:
                if attempt < attempts - 1 and "symlink" not in str(e):
                    logger.warning(f"OS error writing to {path}, retrying...")
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
                return
            except (ValueError, TypeError, RuntimeError, ConfigurationError):
                logger.exception(f"Unexpected data or security error writing to {path}")
                return
            else:
                logger.info(f"File saved successfully to {path}")
                return
            finally:
                if temp_dir and temp_dir.exists():
                    for file_obj in temp_dir.iterdir():
                        file_obj.unlink()
                    temp_dir.rmdir()

    def _sanitize_md(self, text: str) -> str:
        """
        Sanitizes user input for Markdown generation.
        Escapes HTML and Markdown control characters to prevent injection.
        """
        import re
        if not text:
            return ""

        # Escape HTML entities
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Escape all Markdown control characters
        markdown_chars = r'\`*_{}[]()#+-.!|'
        for char in markdown_chars:
            escaped = escaped.replace(char, f'\\{char}')

        # Remove or escape HTML tags
        return re.sub(r'<[^>]+>', '', escaped)

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
                "- Acceptance Criteria:"
            ]
            for ac in spec.core_user_story.acceptance_criteria:
                content.append(f"  - {self._validate_and_sanitize_content(ac)}")

            content.extend([
                "\n# 📊 Data Schema & Flow\n",
                "Validation Rules:",
                f"{self._validate_and_sanitize_content(spec.validation_rules)}\n",
                "🔄 State Machine (Mermaid)\n",
                "```mermaid",
                self._validate_and_sanitize_content(spec.mermaid_flowchart.replace("```mermaid", "").replace("```", "").strip()),
                "```\n",
                "🖥️ UI Structure & States",
                f"Success State: {self._validate_and_sanitize_content(spec.state_machine.success)}",
                f"Loading State: {self._validate_and_sanitize_content(spec.state_machine.loading)}",
                f"Empty State: {self._validate_and_sanitize_content(spec.state_machine.empty)}",
                f"Error State: {self._validate_and_sanitize_content(spec.state_machine.error)}"
            ])

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
                "## 📈 AARRR Metrics Framework\n"
            ]
            for metric in plan.aarrr_metrics:
                content.append(f"### {self._validate_and_sanitize_content(metric.metric_name)}")
                content.append(f"- **Target:** {self._validate_and_sanitize_content(metric.target_value)}")
                content.append(f"- **Method:** {self._validate_and_sanitize_content(metric.measurement_method)}\n")

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
        if not isinstance(value, str):
            msg = "Expected string value"
            raise TypeError(msg)
        if len(value) > max_length:
            msg = f"String exceeds maximum length of {max_length}"
            raise ValueError(msg)

        # Remove control characters
        value = "".join(c for c in value if c.isprintable() or c in "\n\t\r")
        # Check for suspicious patterns
        if re.search(r"[<>\\/]", value):
            msg = "String contains suspicious characters"
            raise ValueError(msg)
        return value

    def _sanitize_for_pdf(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        # Remove any control characters
        text = "".join(c for c in text if c.isprintable())
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
        goals = ", ".join(self._sanitize_for_pdf(self._validate_string(g, 200)) for g in persona.goals)
        frustrations = ", ".join(self._sanitize_for_pdf(self._validate_string(f, 200)) for f in persona.frustrations)

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
        jobs = ", ".join(self._sanitize_for_pdf(self._validate_string(j, 200)) for j in vpc.customer_profile.customer_jobs)
        pains = ", ".join(self._sanitize_for_pdf(self._validate_string(p, 200)) for p in vpc.customer_profile.pains)
        gains = ", ".join(self._sanitize_for_pdf(self._validate_string(g, 200)) for g in vpc.customer_profile.gains)
        pdf.multi_cell(w=0, h=10, text=f"Jobs: {jobs}")
        pdf.multi_cell(w=0, h=10, text=f"Pains: {pains}")
        pdf.multi_cell(w=0, h=10, text=f"Gains: {gains}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Value Map:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        products = ", ".join(self._sanitize_for_pdf(self._validate_string(p, 200)) for p in vpc.value_map.products_and_services)
        pain_relievers = ", ".join(self._sanitize_for_pdf(self._validate_string(p, 200)) for p in vpc.value_map.pain_relievers)
        gain_creators = ", ".join(self._sanitize_for_pdf(self._validate_string(g, 200)) for g in vpc.value_map.gain_creators)
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
