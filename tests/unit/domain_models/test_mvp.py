import pytest
from pydantic import ValidationError

from src.domain_models.mvp import MVPSpec


class TestMVPSpec:
    """Tests for MVPSpec domain model."""

    def test_mvp_spec_valid(self) -> None:
        """Test creating a valid MVPSpec."""
        spec = MVPSpec(
            app_name="Test App",
            core_feature="User Authentication System",
            ui_style="Minimalist",
            v0_prompt="Create a login screen.",
            components=["Login Form", "Sign Up Button"],
        )
        assert spec.app_name == "Test App"
        assert spec.core_feature == "User Authentication System"
        assert len(spec.components) == 2

    def test_mvp_spec_validation_components(self) -> None:
        """Test component name validation."""
        with pytest.raises(ValidationError) as exc:
            MVPSpec(
                app_name="Test",
                core_feature="Login",
                components=["Login <script>alert(1)</script>"],  # XSS attempt
            )
        assert "Invalid component name" in str(exc.value)

    def test_mvp_spec_validation_prompt(self) -> None:
        """Test v0_prompt validation."""
        with pytest.raises(ValidationError) as exc:
            MVPSpec(
                app_name="Test",
                core_feature="Login",
                v0_prompt="   ",  # Empty string
            )
        assert "v0_prompt must be a non-empty string" in str(exc.value)

    def test_mvp_spec_default_components(self) -> None:
        """Test default components."""
        spec = MVPSpec(app_name="Test App", core_feature="User Authentication System")
        assert len(spec.components) == 3
        assert "Hero Section" in spec.components
