"""Tests for the custom field type registry."""

from __future__ import annotations

import json
from typing import Optional

import pytest
from pydantic import field_validator

from codeforms import (
    CheckboxField,
    CheckboxGroupField,
    FieldGroup,
    FieldType,
    Form,
    FormFieldBase,
    SelectOption,
    TextField,
    get_registered_field_types,
    register_field_type,
    validate_form_data,
)
from codeforms.registry import resolve_content_item

# ---------------------------------------------------------------------------
# Custom field types used across tests
# ---------------------------------------------------------------------------


class PhoneField(FormFieldBase):
    """Custom field with a string field_type (not in the FieldType enum)."""

    field_type: str = "phone"
    country_code: str = "+1"
    pattern: Optional[str] = r"^\+?\d[\d\-\s]{6,14}$"


class RatingField(FormFieldBase):
    """Custom field with a string field_type and extra validation."""

    field_type: str = "rating"
    min_rating: int = 1
    max_rating: int = 5

    @field_validator("default_value")
    @classmethod
    def validate_default(cls, v):
        if v is not None and not isinstance(v, int):
            raise ValueError("Default value must be an integer")
        return v


class ColorField(FormFieldBase):
    """Custom field reusing an existing FieldType (text) but as a specialization."""

    field_type: FieldType = FieldType.TEXT
    color_format: str = "hex"  # hex, rgb, hsl


# ---------------------------------------------------------------------------
# Registry API
# ---------------------------------------------------------------------------


class TestRegistryAPI:
    def test_builtin_types_are_registered(self):
        types = get_registered_field_types()
        assert "text" in types
        assert "email" in types
        assert "number" in types
        assert "select" in types
        assert "checkbox" in types
        assert "radio" in types
        assert "file" in types
        assert "hidden" in types
        assert "url" in types
        assert "textarea" in types
        assert "list" in types

    def test_checkbox_has_two_candidates(self):
        types = get_registered_field_types()
        assert len(types["checkbox"]) == 2  # CheckboxField + CheckboxGroupField

    def test_register_custom_type(self):
        register_field_type(PhoneField)
        types = get_registered_field_types()
        assert "phone" in types
        assert PhoneField in types["phone"]

    def test_register_custom_type_with_string_field_type(self):
        register_field_type(RatingField)
        types = get_registered_field_types()
        assert "rating" in types
        assert RatingField in types["rating"]

    def test_register_duplicate_is_idempotent(self):
        register_field_type(PhoneField)
        register_field_type(PhoneField)
        types = get_registered_field_types()
        assert types["phone"].count(PhoneField) == 1

    def test_register_non_subclass_raises(self):
        with pytest.raises(TypeError, match="must be a subclass"):

            class NotAField:
                pass

            register_field_type(NotAField)

    def test_get_registered_returns_copy(self):
        types1 = get_registered_field_types()
        types2 = get_registered_field_types()
        assert types1 is not types2


# ---------------------------------------------------------------------------
# resolve_content_item
# ---------------------------------------------------------------------------


class TestResolveContentItem:
    def setup_method(self):
        register_field_type(PhoneField)
        register_field_type(RatingField)

    def test_resolve_text_field_dict(self):
        item = {"field_type": "text", "name": "x", "label": "X"}
        result = resolve_content_item(item)
        assert isinstance(result, TextField)
        assert result.name == "x"

    def test_resolve_custom_field_dict(self):
        item = {
            "field_type": "phone",
            "name": "phone",
            "label": "Phone",
            "country_code": "+54",
        }
        result = resolve_content_item(item)
        assert isinstance(result, PhoneField)
        assert result.country_code == "+54"

    def test_resolve_field_group_dict(self):
        item = {
            "title": "Personal Info",
            "fields": [
                {"field_type": "text", "name": "first", "label": "First"},
                {"field_type": "text", "name": "last", "label": "Last"},
            ],
        }
        result = resolve_content_item(item)
        assert isinstance(result, FieldGroup)
        assert result.title == "Personal Info"
        assert len(result.fields) == 2

    def test_resolve_passes_through_instances(self):
        field = TextField(name="x", label="X")
        result = resolve_content_item(field)
        assert result is field

    def test_resolve_checkbox_field_no_options(self):
        item = {"field_type": "checkbox", "name": "agree", "label": "Agree"}
        result = resolve_content_item(item)
        assert isinstance(result, CheckboxField)

    def test_resolve_checkbox_group_field_with_options(self):
        item = {
            "field_type": "checkbox",
            "name": "colors",
            "label": "Colors",
            "options": [{"value": "r", "label": "Red"}],
        }
        result = resolve_content_item(item)
        assert isinstance(result, CheckboxGroupField)

    def test_resolve_unknown_type_raises(self):
        item = {"field_type": "nonexistent", "name": "x", "label": "X"}
        with pytest.raises(ValueError, match="Unknown field type"):
            resolve_content_item(item)


# ---------------------------------------------------------------------------
# Form with custom field types
# ---------------------------------------------------------------------------


class TestFormWithCustomTypes:
    def setup_method(self):
        register_field_type(PhoneField)
        register_field_type(RatingField)

    def test_form_with_custom_field_instances(self):
        form = Form(
            name="test",
            fields=[
                TextField(name="name", label="Name", required=True),
                PhoneField(name="phone", label="Phone", country_code="+54"),
            ],
        )
        assert len(form.fields) == 2
        assert isinstance(form.fields[1], PhoneField)
        assert form.fields[1].country_code == "+54"

    def test_form_with_custom_field_from_dict(self):
        form = Form.model_validate(
            {
                "name": "test",
                "content": [
                    {"field_type": "text", "name": "name", "label": "Name"},
                    {
                        "field_type": "phone",
                        "name": "phone",
                        "label": "Phone",
                        "country_code": "+54",
                    },
                ],
            }
        )
        assert len(form.fields) == 2
        assert isinstance(form.fields[1], PhoneField)
        assert form.fields[1].country_code == "+54"

    def test_form_json_roundtrip_with_custom_field(self):
        form = Form(
            name="test",
            fields=[
                TextField(name="name", label="Name"),
                PhoneField(name="phone", label="Phone", country_code="+54"),
                RatingField(name="rating", label="Rating", max_rating=10),
            ],
        )

        # Serialize
        json_str = form.model_dump_json()
        data = json.loads(json_str)

        # Verify custom fields are in the serialized data
        phone_data = data["content"][1]
        assert phone_data["field_type"] == "phone"
        assert phone_data["country_code"] == "+54"

        rating_data = data["content"][2]
        assert rating_data["field_type"] == "rating"
        assert rating_data["max_rating"] == 10

        # Deserialize
        restored = Form.model_validate_json(json_str)
        assert len(restored.fields) == 3
        assert isinstance(restored.fields[0], TextField)
        assert isinstance(restored.fields[1], PhoneField)
        assert restored.fields[1].country_code == "+54"
        assert isinstance(restored.fields[2], RatingField)
        assert restored.fields[2].max_rating == 10

    def test_form_loads_with_custom_field(self):
        json_str = json.dumps(
            {
                "name": "test",
                "content": [
                    {"field_type": "phone", "name": "phone", "label": "Phone"},
                ],
            }
        )
        form = Form.loads(json_str)
        assert isinstance(form.fields[0], PhoneField)

    def test_form_to_dict_includes_custom_fields(self):
        form = Form(
            name="test",
            fields=[PhoneField(name="phone", label="Phone", country_code="+44")],
        )
        d = form.to_dict()
        assert d["content"][0]["country_code"] == "+44"
        assert d["content"][0]["field_type"] == "phone"

    def test_form_validate_data_custom_field_passthrough(self):
        """Custom fields without specific validation fall through to default."""
        form = Form(
            name="test",
            fields=[PhoneField(name="phone", label="Phone")],
        )
        result = form.validate_data({"phone": "+1-555-1234"})
        assert result["success"] is True

    def test_validate_form_data_custom_field_passthrough(self):
        form = Form(
            name="test",
            fields=[PhoneField(name="phone", label="Phone")],
        )
        result = validate_form_data(form, {"phone": "+1-555-1234"})
        assert result["success"] is True
        assert result["data"]["phone"] == "+1-555-1234"

    def test_form_export_html_custom_field(self):
        form = Form(
            name="test",
            fields=[PhoneField(name="phone", label="Phone")],
        )
        export = form.export("html")
        html = export["output"]
        assert 'name="phone"' in html
        assert 'type="phone"' in html

    def test_form_unique_names_validated_for_custom_fields(self):
        with pytest.raises(Exception, match="unique"):
            Form(
                name="test",
                fields=[
                    PhoneField(name="dup", label="A"),
                    PhoneField(name="dup", label="B"),
                ],
            )


# ---------------------------------------------------------------------------
# FieldGroup with custom field types
# ---------------------------------------------------------------------------


class TestFieldGroupWithCustomTypes:
    def setup_method(self):
        register_field_type(PhoneField)

    def test_group_with_custom_field_instances(self):
        group = FieldGroup(
            title="Contact",
            fields=[
                TextField(name="name", label="Name"),
                PhoneField(name="phone", label="Phone"),
            ],
        )
        assert len(group.fields) == 2
        assert isinstance(group.fields[1], PhoneField)

    def test_group_from_dict_with_custom_field(self):
        group = FieldGroup.model_validate(
            {
                "title": "Contact",
                "fields": [
                    {"field_type": "text", "name": "name", "label": "Name"},
                    {"field_type": "phone", "name": "phone", "label": "Phone"},
                ],
            }
        )
        assert isinstance(group.fields[1], PhoneField)

    def test_form_with_group_containing_custom_field_json_roundtrip(self):
        register_field_type(PhoneField)
        form = Form(
            name="test",
            content=[
                FieldGroup(
                    title="Contact",
                    fields=[
                        TextField(name="name", label="Name"),
                        PhoneField(name="phone", label="Phone", country_code="+54"),
                    ],
                )
            ],
        )

        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)

        assert len(restored.content) == 1
        group = restored.content[0]
        assert isinstance(group, FieldGroup)
        assert isinstance(group.fields[1], PhoneField)
        assert group.fields[1].country_code == "+54"


# ---------------------------------------------------------------------------
# field_type_value property
# ---------------------------------------------------------------------------


class TestFieldTypeValue:
    def test_enum_field_type_value(self):
        field = TextField(name="x", label="X")
        assert field.field_type_value == "text"

    def test_str_field_type_value(self):
        register_field_type(PhoneField)
        field = PhoneField(name="x", label="X")
        assert field.field_type_value == "phone"

    def test_field_type_value_used_in_html_export(self):
        register_field_type(PhoneField)
        field = PhoneField(name="phone", label="Phone")
        html = field.export("html")
        assert 'type="phone"' in html


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_form_fields_key_still_works(self):
        form = Form(
            name="test",
            fields=[TextField(name="x", label="X")],
        )
        assert len(form.fields) == 1

    def test_form_content_key_works(self):
        form = Form(
            name="test",
            content=[TextField(name="x", label="X")],
        )
        assert len(form.fields) == 1

    def test_builtin_fields_still_work_in_json_roundtrip(self):
        form = Form(
            name="test",
            fields=[
                TextField(name="text", label="Text", minlength=3),
                CheckboxField(name="check", label="Check"),
                CheckboxGroupField(
                    name="group",
                    label="Group",
                    options=[SelectOption(value="a", label="A")],
                ),
            ],
        )
        json_str = form.model_dump_json()
        restored = Form.model_validate_json(json_str)

        assert isinstance(restored.fields[0], TextField)
        assert restored.fields[0].minlength == 3
        assert isinstance(restored.fields[1], CheckboxField)
        assert isinstance(restored.fields[2], CheckboxGroupField)
