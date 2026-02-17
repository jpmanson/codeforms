"""Tests for dependent field options (DependentOptionsConfig)."""

from __future__ import annotations

import json

import pytest

from codeforms import (
    Form,
    SelectField,
    SelectOption,
    DependentOptionsConfig,
    validate_form_data_dynamic,
)


# ---------------------------------------------------------------------------
# DependentOptionsConfig model
# ---------------------------------------------------------------------------

class TestDependentOptionsConfig:
    def test_basic_creation(self):
        config = DependentOptionsConfig(
            depends_on="country",
            options_map={
                "US": [SelectOption(value="NY", label="New York"),
                       SelectOption(value="CA", label="California")],
                "AR": [SelectOption(value="BA", label="Buenos Aires"),
                       SelectOption(value="CO", label="Córdoba")],
            },
        )
        assert config.depends_on == "country"
        assert len(config.options_map["US"]) == 2
        assert config.options_map["AR"][0].value == "BA"

    def test_serialization_roundtrip(self):
        config = DependentOptionsConfig(
            depends_on="country",
            options_map={
                "US": [SelectOption(value="NY", label="New York")],
            },
        )
        json_str = config.model_dump_json()
        data = json.loads(json_str)
        assert data["depends_on"] == "country"
        assert data["options_map"]["US"][0]["value"] == "NY"

        restored = DependentOptionsConfig.model_validate_json(json_str)
        assert restored.depends_on == "country"
        assert restored.options_map["US"][0].value == "NY"


# ---------------------------------------------------------------------------
# DependentOptionsConfig on fields
# ---------------------------------------------------------------------------

class TestFieldWithDependentOptions:
    def test_field_with_dependent_options(self):
        field = SelectField(
            name="city",
            label="City",
            options=[
                SelectOption(value="NY", label="New York"),
                SelectOption(value="BA", label="Buenos Aires"),
            ],
            dependent_options=DependentOptionsConfig(
                depends_on="country",
                options_map={
                    "US": [SelectOption(value="NY", label="New York")],
                    "AR": [SelectOption(value="BA", label="Buenos Aires")],
                },
            ),
        )
        assert field.dependent_options is not None
        assert field.dependent_options.depends_on == "country"

    def test_field_without_dependent_options(self):
        field = SelectField(
            name="country",
            label="Country",
            options=[SelectOption(value="US", label="US")],
        )
        assert field.dependent_options is None

    def test_dependent_options_serializes_in_form(self):
        form = Form(
            name="test",
            fields=[
                SelectField(
                    name="country",
                    label="Country",
                    options=[
                        SelectOption(value="US", label="US"),
                        SelectOption(value="AR", label="AR"),
                    ],
                ),
                SelectField(
                    name="city",
                    label="City",
                    options=[
                        SelectOption(value="NY", label="New York"),
                        SelectOption(value="BA", label="Buenos Aires"),
                    ],
                    dependent_options=DependentOptionsConfig(
                        depends_on="country",
                        options_map={
                            "US": [SelectOption(value="NY", label="New York")],
                            "AR": [SelectOption(value="BA", label="Buenos Aires")],
                        },
                    ),
                ),
            ],
        )
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)
        assert restored.fields[1].dependent_options is not None
        assert restored.fields[1].dependent_options.depends_on == "country"
