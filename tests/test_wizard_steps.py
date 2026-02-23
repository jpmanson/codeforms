"""Tests for multi-step forms (wizard) with FormStep."""

from __future__ import annotations

import json

import pytest

from codeforms import (
    EmailField,
    FieldGroup,
    Form,
    FormStep,
    SelectField,
    SelectOption,
    TextField,
    VisibilityRule,
)
from codeforms.registry import resolve_content_item

# ---------------------------------------------------------------------------
# FormStep model
# ---------------------------------------------------------------------------


class TestFormStepModel:
    def test_basic_creation(self):
        step = FormStep(
            title="Personal Info",
            content=[
                TextField(name="name", label="Name", required=True),
                EmailField(name="email", label="Email"),
            ],
        )
        assert step.type == "step"
        assert step.title == "Personal Info"
        assert len(step.content) == 2

    def test_fields_property_flattens(self):
        step = FormStep(
            title="Step",
            content=[
                TextField(name="a", label="A"),
                FieldGroup(
                    title="Group",
                    fields=[
                        TextField(name="b", label="B"),
                        TextField(name="c", label="C"),
                    ],
                ),
            ],
        )
        assert len(step.fields) == 3
        assert [f.name for f in step.fields] == ["a", "b", "c"]

    def test_default_values(self):
        step = FormStep(title="S", content=[])
        assert step.type == "step"
        assert step.validation_mode == "on_next"
        assert step.skippable is False
        assert step.description is None

    def test_serialization_roundtrip(self):
        step = FormStep(
            title="Step 1",
            description="First step",
            content=[
                TextField(name="x", label="X"),
            ],
            validation_mode="on_submit",
            skippable=True,
        )
        json_str = step.model_dump_json()
        data = json.loads(json_str)
        assert data["type"] == "step"
        assert data["title"] == "Step 1"
        assert data["validation_mode"] == "on_submit"
        assert data["skippable"] is True


# ---------------------------------------------------------------------------
# Resolver discrimination (RISK-1)
# ---------------------------------------------------------------------------


class TestResolverDiscrimination:
    def test_type_step_resolves_to_formstep(self):
        item = {
            "type": "step",
            "title": "Step 1",
            "content": [
                {"field_type": "text", "name": "x", "label": "X"},
            ],
        }
        result = resolve_content_item(item)
        assert isinstance(result, FormStep)
        assert result.title == "Step 1"
        assert len(result.fields) == 1

    def test_no_type_with_title_resolves_to_fieldgroup(self):
        """Legacy payloads without 'type' still resolve to FieldGroup."""
        item = {
            "title": "Group",
            "fields": [
                {"field_type": "text", "name": "x", "label": "X"},
            ],
        }
        result = resolve_content_item(item)
        assert isinstance(result, FieldGroup)

    def test_type_step_takes_priority_over_title_heuristic(self):
        """A dict with both 'type'='step' and 'title' → FormStep, not FieldGroup."""
        item = {
            "type": "step",
            "title": "Ambiguous",
            "content": [
                {"field_type": "text", "name": "x", "label": "X"},
            ],
        }
        result = resolve_content_item(item)
        assert isinstance(result, FormStep)

    def test_unknown_type_falls_through_to_fieldgroup(self):
        """An unknown type value falls through to FieldGroup heuristic."""
        item = {
            "type": "unknown_future_type",
            "title": "Group",
            "fields": [
                {"field_type": "text", "name": "x", "label": "X"},
            ],
        }
        result = resolve_content_item(item)
        assert isinstance(result, FieldGroup)


# ---------------------------------------------------------------------------
# Form with steps
# ---------------------------------------------------------------------------


class TestFormWithSteps:
    def _make_wizard_form(self):
        return Form(
            name="wizard",
            content=[
                FormStep(
                    title="Personal",
                    content=[
                        TextField(name="name", label="Name", required=True),
                        EmailField(name="email", label="Email", required=True),
                    ],
                ),
                FormStep(
                    title="Preferences",
                    content=[
                        SelectField(
                            name="plan",
                            label="Plan",
                            required=True,
                            options=[
                                SelectOption(value="free", label="Free"),
                                SelectOption(value="pro", label="Pro"),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_get_steps(self):
        form = self._make_wizard_form()
        steps = form.get_steps()
        assert len(steps) == 2
        assert steps[0].title == "Personal"
        assert steps[1].title == "Preferences"

    def test_get_steps_empty_for_non_wizard(self):
        form = Form(name="simple", fields=[TextField(name="x", label="X")])
        assert form.get_steps() == []

    def test_fields_flattens_all_steps(self):
        form = self._make_wizard_form()
        assert len(form.fields) == 3
        assert [f.name for f in form.fields] == ["name", "email", "plan"]

    def test_validate_step_valid(self):
        form = self._make_wizard_form()
        result = form.validate_step(0, {"name": "John", "email": "j@x.com"})
        assert result["success"] is True

    def test_validate_step_invalid(self):
        form = self._make_wizard_form()
        result = form.validate_step(0, {"name": "John"})  # missing email
        assert result["success"] is False
        assert any(e["field"] == "email" for e in result["errors"])

    def test_validate_step_invalid_index(self):
        form = self._make_wizard_form()
        with pytest.raises(ValueError, match="step index"):
            form.validate_step(5, {})

    def test_validate_step_non_wizard_raises(self):
        form = Form(name="simple", fields=[TextField(name="x", label="X")])
        with pytest.raises(ValueError, match="wizard"):
            form.validate_step(0, {})

    def test_validate_all_steps_success(self):
        form = self._make_wizard_form()
        result = form.validate_all_steps(
            {
                "name": "John",
                "email": "j@x.com",
                "plan": "pro",
            }
        )
        assert result["success"] is True
        assert result["data"]["name"] == "John"
        assert result["data"]["plan"] == "pro"

    def test_validate_all_steps_partial_failure(self):
        form = self._make_wizard_form()
        result = form.validate_all_steps(
            {
                "name": "John",
                "email": "j@x.com",
                # missing plan
            }
        )
        assert result["success"] is False
        assert result["step_errors"] is not None
        assert 1 in result["step_errors"]

    def test_json_roundtrip_wizard(self):
        form = self._make_wizard_form()
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)
        assert len(restored.get_steps()) == 2
        assert len(restored.fields) == 3
        assert isinstance(restored.content[0], FormStep)

    def test_form_loads_wizard_from_dict(self):
        payload = {
            "name": "wizard",
            "content": [
                {
                    "type": "step",
                    "title": "Step 1",
                    "content": [
                        {"field_type": "text", "name": "a", "label": "A"},
                    ],
                },
                {
                    "type": "step",
                    "title": "Step 2",
                    "content": [
                        {"field_type": "email", "name": "b", "label": "B"},
                    ],
                },
            ],
        }
        form = Form.model_validate(payload)
        assert len(form.get_steps()) == 2
        assert isinstance(form.content[0], FormStep)
        assert isinstance(form.fields[0], TextField)
        assert isinstance(form.fields[1], EmailField)


# ---------------------------------------------------------------------------
# Step with visibility
# ---------------------------------------------------------------------------


class TestStepWithVisibility:
    def test_step_fields_with_visibility(self):
        form = Form(
            name="test",
            content=[
                FormStep(
                    title="Step 1",
                    content=[
                        TextField(name="type", label="Type", required=True),
                        TextField(
                            name="detail",
                            label="Detail",
                            required=True,
                            visible_when=[
                                VisibilityRule(
                                    field="type", operator="equals", value="other"
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        # With visibility: detail is hidden when type != "other"
        result = form.validate_step(
            0,
            {"type": "standard"},
            respect_visibility=True,
        )
        assert result["success"] is True

        # Without visibility: detail is required and missing
        result = form.validate_step(
            0,
            {"type": "standard"},
            respect_visibility=False,
        )
        assert result["success"] is False


# ---------------------------------------------------------------------------
# HTML export for wizard
# ---------------------------------------------------------------------------


class TestWizardExport:
    def test_wizard_form_has_data_wizard(self):
        form = Form(
            name="wizard",
            content=[
                FormStep(
                    title="S1",
                    content=[TextField(name="x", label="X")],
                ),
            ],
        )
        export = form.export("html")
        html = export["output"]
        assert 'data-wizard="true"' in html
        assert "form-wizard" in html

    def test_step_renders_as_section(self):
        form = Form(
            name="wizard",
            content=[
                FormStep(
                    title="Step 1",
                    content=[TextField(name="x", label="X")],
                ),
            ],
        )
        export = form.export("html")
        html = export["output"]
        assert "<section " in html
        assert 'data-step="true"' in html
        assert "Step 1" in html
        # NOT fieldset
        assert "<fieldset" not in html

    def test_non_wizard_no_section(self):
        form = Form(
            name="simple",
            fields=[TextField(name="x", label="X")],
        )
        export = form.export("html")
        html = export["output"]
        assert "<section" not in html

    def test_step_with_description(self):
        form = Form(
            name="wizard",
            content=[
                FormStep(
                    title="S1",
                    description="Fill in your details",
                    content=[TextField(name="x", label="X")],
                ),
            ],
        )
        export = form.export("html")
        html = export["output"]
        assert "Fill in your details" in html

    def test_step_bootstrap5_classes(self):
        form = Form(
            name="wizard",
            content=[
                FormStep(
                    title="S1",
                    content=[TextField(name="x", label="X")],
                ),
            ],
        )
        export = form.export("html_bootstrap5")
        html = export["output"]
        assert "form-step mb-4" in html
        assert "needs-validation" in html
