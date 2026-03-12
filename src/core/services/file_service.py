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
        def _raise_path_error(m: str) -> None:
            raise ConfigurationError(m)

        try:
            p = Path(path)

            if ".." in p.parts:
                _raise_path_error(f"Path traversal detected (contains '..'): {path}")

            if p.is_absolute():
                _raise_path_error(f"Absolute paths are not allowed: {path}")

            # Resolve the path strictly within the current working directory
            cwd = Path.cwd().resolve(strict=True)
            target_path = (cwd / p).resolve()

        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ConfigurationError(msg) from e

        if not target_path.is_relative_to(cwd):
            msg = f"Path traversal detected: {target_path}"
            raise ConfigurationError(msg)

        return target_path

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
        Includes simple retry logic for robustness and uses atomic file writes.
        """
        import os
        import tempfile

        attempts = 3
        def _raise_symlink_error(m: str) -> None:
            raise OSError(m)

        for attempt in range(attempts):
            try:
                # Ensure parent exists
                path.parent.mkdir(parents=True, exist_ok=True)

                if path.exists() and path.is_symlink():
                    _raise_symlink_error(f"Target path is a symlink: {path}")

                # Atomic write pattern in the exact same directory
                fd, temp_path_str = tempfile.mkstemp(dir=path.parent, prefix="tmp_", suffix=".txt")
                temp_path = Path(temp_path_str)
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(content)
                        f.flush()
                        os.fsync(f.fileno())
                    temp_path.replace(path)
                except Exception:
                    if temp_path.exists():
                        temp_path.unlink()
                    raise

                logger.info(f"File saved successfully to {path}")
                break
            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                break  # No point retrying permission error
            except OSError as e:
                if attempt < attempts - 1 and "symlink" not in str(e):
                    logger.warning(
                        f"OS error writing to {path}, retrying... ({attempt + 1}/{attempts})"
                    )
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
                break
            except (ValueError, TypeError, RuntimeError):
                logger.exception(f"Unexpected data error writing to {path}")
                break

    def _sanitize_md(self, text: str) -> str:
        """
        Sanitizes user input for Markdown generation.
        Escapes simple HTML tags to prevent execution in markdown parsers.
        """
        return text.replace("<", "&lt;").replace(">", "&gt;")

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
                f"- Routing & Components: {self._sanitize_md(spec.routing_and_constraints)}\n",
                "# 🗺️ Sitemap & Information Architecture\n",
                f"{self._sanitize_md(spec.sitemap)}\n",
                "# 🎯 Core User Story\n",
                f"- As a: {self._sanitize_md(spec.core_user_story.as_a)}",
                f"- I want to: {self._sanitize_md(spec.core_user_story.i_want_to)}",
                f"- So that: {self._sanitize_md(spec.core_user_story.so_that)}",
                f"- Target Route: {self._sanitize_md(spec.core_user_story.target_route)}",
                "- Acceptance Criteria:"
            ]
            for ac in spec.core_user_story.acceptance_criteria:
                content.append(f"  - {self._sanitize_md(ac)}")

            content.extend([
                "\n# 📊 Data Schema & Flow\n",
                "Validation Rules:",
                f"{self._sanitize_md(spec.validation_rules)}\n",
                "🔄 State Machine (Mermaid)\n",
                "```mermaid",
                self._sanitize_md(spec.mermaid_flowchart.replace("```mermaid", "").replace("```", "").strip()),
                "```\n",
                "🖥️ UI Structure & States",
                f"Success State: {self._sanitize_md(spec.state_machine.success)}",
                f"Loading State: {self._sanitize_md(spec.state_machine.loading)}",
                f"Empty State: {self._sanitize_md(spec.state_machine.empty)}",
                f"Error State: {self._sanitize_md(spec.state_machine.error)}"
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
                f"**Riskiest Assumption:** {self._sanitize_md(plan.riskiest_assumption)}",
                f"**Experiment Type:** {self._sanitize_md(plan.experiment_type)}",
                f"**Acquisition Channel:** {self._sanitize_md(plan.acquisition_channel)}",
                f"**Pivot Condition:** {self._sanitize_md(plan.pivot_condition)}\n",
                "## 📈 AARRR Metrics Framework\n"
            ]
            for metric in plan.aarrr_metrics:
                content.append(f"### {self._sanitize_md(metric.metric_name)}")
                content.append(f"- **Target:** {self._sanitize_md(metric.target_value)}")
                content.append(f"- **Method:** {self._sanitize_md(metric.measurement_method)}\n")

            self._save_text_sync("\n".join(content), output_path)
            logger.info(f"EXPERIMENT_PLAN MD generated successfully at {output_path}")
        except Exception:
            logger.exception("Failed to generate EXPERIMENT_PLAN MD")
            raise
        else:
            return output_path

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

        # 1. Persona Section
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(w=200, h=10, text="1. Target Persona", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(w=0, h=10, text=f"Name: {persona.name} | Occupation: {persona.occupation}")
        pdf.multi_cell(w=0, h=10, text=f"Demographics: {persona.demographics}")
        pdf.multi_cell(w=0, h=10, text=f"Bio: {persona.bio}")
        pdf.multi_cell(w=0, h=10, text=f"Goals: {', '.join(persona.goals)}")
        pdf.multi_cell(w=0, h=10, text=f"Frustrations: {', '.join(persona.frustrations)}")
        pdf.ln(5)

        # 2. Alternative Analysis Section
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(
            w=200, h=10, text="2. Alternative Analysis", new_x="LMARGIN", new_y="NEXT", align="L"
        )
        pdf.set_font("Helvetica", size=12)
        for alt in analysis.current_alternatives:
            pdf.multi_cell(
                w=0,
                h=10,
                text=f"- Tool: {alt.name} | Cost: {alt.financial_cost} | Time: {alt.time_cost} | UX Friction: {alt.ux_friction}",
            )
        pdf.multi_cell(w=0, h=10, text=f"Switching Cost: {analysis.switching_cost}")
        pdf.multi_cell(w=0, h=10, text=f"10x Value: {analysis.ten_x_value}")
        pdf.ln(5)

        # 3. Value Proposition Canvas Section
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
        pdf.multi_cell(w=0, h=10, text=f"Jobs: {', '.join(vpc.customer_profile.customer_jobs)}")
        pdf.multi_cell(w=0, h=10, text=f"Pains: {', '.join(vpc.customer_profile.pains)}")
        pdf.multi_cell(w=0, h=10, text=f"Gains: {', '.join(vpc.customer_profile.gains)}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Value Map:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(
            w=0, h=10, text=f"Products & Services: {', '.join(vpc.value_map.products_and_services)}"
        )
        pdf.multi_cell(w=0, h=10, text=f"Pain Relievers: {', '.join(vpc.value_map.pain_relievers)}")
        pdf.multi_cell(w=0, h=10, text=f"Gain Creators: {', '.join(vpc.value_map.gain_creators)}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Fit Evaluation:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(w=0, h=10, text=vpc.fit_evaluation)

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
