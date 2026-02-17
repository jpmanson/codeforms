"""Backward compatibility tests for Phase 2 changes.

Ensures all pre-Phase-2 code paths continue to work unchanged.
"""

from __future__ import annotations

import json

import pytest

from codeforms import (
    Form,
    TextField,
    EmailField,
    NumberField,
    SelectField,
    SelectOption,
    CheckboxField,
    CheckboxGroupField,
    RadioField,
    FieldGroup,
    FormStep,
    VisibilityRule,
    validate_form_data,
    register_field_type,
    FormFieldBase,
)


# ---------------------------------------------------------------------------
# Form construction backward compat
# ---------------------------------------------------------------------------

class TestFormConstruction:
    def test_form_with_fields_key(self):
        form = Form(
            name="test",
            fields=[TextField(name="x", label="X")],
        )
        assert len(form.fields) == 1
        assert form.fields[0].name == "x"

    def test_form_with_content_key(self):
        form = Form(
            name="test",
            content=[TextField(name="x", label="X")],
        )
        assert len(form.fields) == 1

    def test_form_fields_flattens_groups(self):
        form = Form(
            name="test",
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
        assert len(form.fields) == 3
        assert [f.name for f in form.fields] == ["a", "b", "c"]

    def test_form_fields_flattens_steps(self):
        form = Form(
            name="test",
            content=[
                FormStep(
                    title="Step 1",
                    content=[
                        TextField(name="a", label="A"),
                    ],
                ),
                FormStep(
                    title="Step 2",
                    content=[
                        TextField(name="b", label="B"),
                        FieldGroup(
                            title="Inner",
                            fields=[TextField(name="c", label="C")],
                        ),
                    ],
                ),
            ],
        )
        assert len(form.fields) == 3
        assert [f.name for f in form.fields] == ["a", "b", "c"]

    def test_form_fields_mixed_content(self):
        """Bare fields + groups + steps in the same form."""
        form = Form(
            name="test",
            content=[
                TextField(name="bare", label="Bare"),
                FieldGroup(
                    title="G",
                    fields=[TextField(name="grouped", label="Grouped")],
                ),
                FormStep(
                    title="S",
                    content=[TextField(name="stepped", label="Stepped")],
                ),
            ],
        )
        assert len(form.fields) == 3


# ---------------------------------------------------------------------------
# JSON roundtrip backward compat
# ---------------------------------------------------------------------------

class TestJsonRoundtrip:
    def test_legacy_payload_loads_unchanged(self):
        """Pre-Phase-2 JSON (no visible_when, no steps) loads fine."""
        payload = {
            "name": "legacy",
            "content": [
                {"field_type": "text", "name": "x", "label": "X", "required": True},
                {"field_type": "email", "name": "e", "label": "E"},
            ],
        }
        form = Form.model_validate(payload)
        assert len(form.fields) == 2
        assert isinstance(form.fields[0], TextField)

    def test_legacy_payload_json_roundtrip(self):
        form = Form(
            name="roundtrip",
            fields=[
                TextField(name="name", label="Name", required=True),
                EmailField(name="email", label="Email"),
            ],
        )
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)
        assert restored.name == "roundtrip"
        assert len(restored.fields) == 2
        assert isinstance(restored.fields[0], TextField)
        assert isinstance(restored.fields[1], EmailField)

    def test_fieldgroup_json_roundtrip(self):
        form = Form(
            name="groups",
            content=[
                FieldGroup(
                    title="Info",
                    fields=[
                        TextField(name="a", label="A"),
                        TextField(name="b", label="B"),
                    ],
                )
            ],
        )
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)
        assert len(restored.content) == 1
        assert isinstance(restored.content[0], FieldGroup)
        assert len(restored.fields) == 2

    def test_new_fields_serialized_and_restored(self):
        """visible_when metadata survives roundtrip."""
        form = Form(
            name="dynamic",
            fields=[
                TextField(
                    name="country",
                    label="Country",
                ),
                TextField(
                    name="state",
                    label="State",
                    visible_when=[
                        VisibilityRule(field="country", operator="equals", value="US")
                    ],
                ),
            ],
        )
        json_str = form.model_dump_json()
        data = json.loads(json_str)
        # visible_when must be in the serialized data
        state_data = data["content"][1]
        assert state_data["visible_when"] is not None
        assert state_data["visible_when"][0]["field"] == "country"

        # Restore
        restored = Form.model_validate_json(json_str)
        assert restored.fields[1].visible_when is not None
        assert restored.fields[1].visible_when[0].operator == "equals"


# ---------------------------------------------------------------------------
# Validation backward compat
# ---------------------------------------------------------------------------

class TestValidationCompat:
    def test_validate_form_data_ignores_visible_when(self):
        """Legacy validate_form_data does NOT respect visible_when (RISK-3)."""
        form = Form(
            name="test",
            fields=[
                TextField(name="country", label="Country", required=True),
                TextField(
                    name="state",
                    label="State",
                    required=True,
                    visible_when=[
                        VisibilityRule(field="country", operator="equals", value="US")
                    ],
                ),
            ],
        )
        # state is hidden (country != "US") but still required by legacy validation
        result = validate_form_data(form, {"country": "AR"})
        assert result["success"] is False
        assert result["errors"][0]["field"] == "state"

    def test_validate_form_data_unchanged_for_legacy_form(self):
        form = Form(
            name="test",
            fields=[
                TextField(name="name", label="Name", required=True),
                EmailField(name="email", label="Email", required=True),
            ],
        )
        result = validate_form_data(form, {"name": "John", "email": "j@x.com"})
        assert result["success"] is True


# ---------------------------------------------------------------------------
# HTML export backward compat
# ---------------------------------------------------------------------------

class TestExportCompat:
    def test_non_step_form_html_unchanged(self):
        """Forms without steps produce the same HTML structure."""
        form = Form(
            name="test",
            fields=[TextField(name="x", label="X")],
        )
        export = form.export("html")
        html = export["output"]
        assert "<form " in html
        assert 'name="x"' in html
        # No wizard attributes
        assert "data-wizard" not in html
        assert "form-wizard" not in html

    def test_group_renders_as_fieldset(self):
        form = Form(
            name="test",
            content=[
                FieldGroup(
                    title="Section",
                    fields=[TextField(name="x", label="X")],
                )
            ],
        )
        export = form.export("html")
        html = export["output"]
        assert "<fieldset" in html
        assert "<legend" in html


# ---------------------------------------------------------------------------
# Custom field registry compat with new features
# ---------------------------------------------------------------------------

class TestCustomFieldRegistryCompat:
    def setup_method(self):
        class TagField(FormFieldBase):
            field_type: str = "tag"
            max_tags: int = 5

        register_field_type(TagField)
        self.TagField = TagField

    def test_custom_field_in_form_step(self):
        form = Form(
            name="test",
            content=[
                FormStep(
                    title="Step 1",
                    content=[
                        self.TagField(name="tags", label="Tags"),
                    ],
                )
            ],
        )
        assert len(form.fields) == 1
        assert isinstance(form.fields[0], self.TagField)

    def test_custom_field_json_roundtrip_with_step(self):
        form = Form(
            name="test",
            content=[
                FormStep(
                    title="Step 1",
                    content=[
                        self.TagField(name="tags", label="Tags", max_tags=10),
                    ],
                )
            ],
        )
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)
        assert len(restored.fields) == 1
        assert restored.fields[0].max_tags == 10
