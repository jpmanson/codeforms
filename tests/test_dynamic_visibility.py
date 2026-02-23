"""Tests for conditional field visibility (visible_when)."""

from __future__ import annotations

import json

from codeforms import (
    Form,
    SelectField,
    SelectOption,
    TextField,
    VisibilityRule,
    evaluate_visibility,
    validate_form_data,
    validate_form_data_dynamic,
)

# ---------------------------------------------------------------------------
# evaluate_visibility
# ---------------------------------------------------------------------------


class TestEvaluateVisibility:
    def test_no_rules_always_visible(self):
        field = TextField(name="x", label="X")
        assert evaluate_visibility(field, {}) is True

    def test_equals_match(self):
        field = TextField(
            name="state",
            label="State",
            visible_when=[
                VisibilityRule(field="country", operator="equals", value="US")
            ],
        )
        assert evaluate_visibility(field, {"country": "US"}) is True
        assert evaluate_visibility(field, {"country": "AR"}) is False

    def test_not_equals(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[
                VisibilityRule(field="type", operator="not_equals", value="hidden")
            ],
        )
        assert evaluate_visibility(field, {"type": "visible"}) is True
        assert evaluate_visibility(field, {"type": "hidden"}) is False

    def test_in_operator(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[
                VisibilityRule(field="country", operator="in", value=["US", "CA", "MX"])
            ],
        )
        assert evaluate_visibility(field, {"country": "US"}) is True
        assert evaluate_visibility(field, {"country": "BR"}) is False

    def test_not_in_operator(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[
                VisibilityRule(field="country", operator="not_in", value=["CN", "RU"])
            ],
        )
        assert evaluate_visibility(field, {"country": "US"}) is True
        assert evaluate_visibility(field, {"country": "CN"}) is False

    def test_gt_operator(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[VisibilityRule(field="age", operator="gt", value=18)],
        )
        assert evaluate_visibility(field, {"age": 21}) is True
        assert evaluate_visibility(field, {"age": 18}) is False
        assert evaluate_visibility(field, {"age": None}) is False

    def test_lt_operator(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[VisibilityRule(field="age", operator="lt", value=65)],
        )
        assert evaluate_visibility(field, {"age": 30}) is True
        assert evaluate_visibility(field, {"age": 65}) is False

    def test_is_empty(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[VisibilityRule(field="other", operator="is_empty")],
        )
        assert evaluate_visibility(field, {"other": None}) is True
        assert evaluate_visibility(field, {"other": ""}) is True
        assert evaluate_visibility(field, {}) is True
        assert evaluate_visibility(field, {"other": "value"}) is False

    def test_is_not_empty(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[VisibilityRule(field="other", operator="is_not_empty")],
        )
        assert evaluate_visibility(field, {"other": "value"}) is True
        assert evaluate_visibility(field, {"other": None}) is False
        assert evaluate_visibility(field, {"other": ""}) is False

    def test_multiple_rules_and_logic(self):
        """Multiple rules = AND logic (all must be true)."""
        field = TextField(
            name="x",
            label="X",
            visible_when=[
                VisibilityRule(field="country", operator="equals", value="US"),
                VisibilityRule(field="age", operator="gt", value=18),
            ],
        )
        assert evaluate_visibility(field, {"country": "US", "age": 21}) is True
        assert evaluate_visibility(field, {"country": "US", "age": 16}) is False
        assert evaluate_visibility(field, {"country": "AR", "age": 21}) is False

    def test_missing_field_in_data(self):
        field = TextField(
            name="x",
            label="X",
            visible_when=[
                VisibilityRule(field="missing", operator="equals", value="yes")
            ],
        )
        # missing field → data.get returns None → None != "yes" → False
        assert evaluate_visibility(field, {}) is False


# ---------------------------------------------------------------------------
# validate_form_data_dynamic
# ---------------------------------------------------------------------------


class TestValidateFormDataDynamic:
    def _make_form(self):
        return Form(
            name="test",
            fields=[
                SelectField(
                    name="country",
                    label="Country",
                    required=True,
                    options=[
                        SelectOption(value="US", label="US"),
                        SelectOption(value="AR", label="AR"),
                    ],
                ),
                TextField(
                    name="state",
                    label="State",
                    required=True,
                    visible_when=[
                        VisibilityRule(field="country", operator="equals", value="US"),
                    ],
                ),
                TextField(
                    name="province",
                    label="Province",
                    required=True,
                    visible_when=[
                        VisibilityRule(field="country", operator="equals", value="AR"),
                    ],
                ),
            ],
        )

    def test_hidden_required_field_skipped(self):
        """When country=US, state is visible and province is hidden."""
        form = self._make_form()
        result = validate_form_data_dynamic(
            form,
            {"country": "US", "state": "NY"},
            respect_visibility=True,
        )
        assert result["success"] is True
        assert "province" not in result["data"]
        assert result["data"]["state"] == "NY"

    def test_hidden_required_field_fails_without_respect(self):
        """Without respect_visibility, hidden required field still fails."""
        form = self._make_form()
        result = validate_form_data_dynamic(
            form,
            {"country": "US", "state": "NY"},
            respect_visibility=False,
        )
        assert result["success"] is False
        assert any(e["field"] == "province" for e in result["errors"])

    def test_all_visible_fields_validated(self):
        form = self._make_form()
        result = validate_form_data_dynamic(
            form,
            {"country": "AR", "province": "Buenos Aires"},
            respect_visibility=True,
        )
        assert result["success"] is True
        assert result["data"]["province"] == "Buenos Aires"

    def test_legacy_validate_form_data_not_affected(self):
        """validate_form_data ignores visible_when completely."""
        form = self._make_form()
        result = validate_form_data(
            form,
            {"country": "US", "state": "NY"},
        )
        # Should fail because province is required but missing
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Serialization of visible_when
# ---------------------------------------------------------------------------


class TestVisibilityRuleSerialization:
    def test_visible_when_serializes_to_json(self):
        field = TextField(
            name="state",
            label="State",
            visible_when=[
                VisibilityRule(field="country", operator="equals", value="US"),
            ],
        )
        data = json.loads(field.model_dump_json())
        assert data["visible_when"][0]["field"] == "country"
        assert data["visible_when"][0]["operator"] == "equals"
        assert data["visible_when"][0]["value"] == "US"

    def test_visible_when_roundtrip_in_form(self):
        form = Form(
            name="test",
            fields=[
                TextField(name="a", label="A"),
                TextField(
                    name="b",
                    label="B",
                    visible_when=[
                        VisibilityRule(field="a", operator="is_not_empty"),
                    ],
                ),
            ],
        )
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)
        assert restored.fields[1].visible_when is not None
        assert len(restored.fields[1].visible_when) == 1
        assert restored.fields[1].visible_when[0].operator == "is_not_empty"

    def test_field_without_visible_when_serializes_null(self):
        field = TextField(name="x", label="X")
        data = json.loads(field.model_dump_json(exclude_none=True))
        assert "visible_when" not in data
