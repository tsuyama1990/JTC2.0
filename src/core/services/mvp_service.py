import logging

from src.core.config import get_settings
from src.domain_models.experiment_plan import ExperimentPlan
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.sitemap_and_story import SitemapAndStory

logger = logging.getLogger(__name__)

class MVPService:
    def generate_mvp_definition(
        self, plan: ExperimentPlan, sitemap_and_story: SitemapAndStory
    ) -> MVP | None:
        """
        Extracts MVP generation logic.
        """
        try:
            feature_name = sitemap_and_story.core_story.i_want_to
            feature_name = feature_name if len(feature_name) <= 50 else feature_name[:47] + "..."
            feature_name = feature_name if len(feature_name) >= 3 else feature_name + " feature"

            description = plan.riskiest_assumption
            min_len = get_settings().validation.min_content_length
            if len(description) < min_len:
                description = description.ljust(min_len, ".")

            mvp = MVP(
                type=MVPType.SINGLE_FEATURE,
                core_features=[
                    Feature(
                        name=feature_name,
                        description=description,
                        priority=Priority.MUST_HAVE,
                    )
                ],
                success_criteria=plan.pivot_condition,
            )
        except Exception:
            logger.exception("Failed to generate MVP definition.")
            return None
        else:
            return mvp
