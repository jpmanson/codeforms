"""Tests for JSON Schema export (ExportFormat.JSON_SCHEMA)."""

from __future__ import annotations

import json

from codeforms import (
    CheckboxField,
    CheckboxGroupField,
    DateField,
    EmailField,
    ExportFormat,
    FieldGroup,
    FileField,
    Form,
    FormStep,
    HiddenField,
    ListField,
    NumberField,
    RadioField,
    SelectField,
    SelectOption,
    TextField,
    TextareaField,
    UrlField,
    form_to_json_schema,
)


# ---------------------------------------------------------------------------
# Top-level schema structure
# ---------------------------------------------------------------------------


class TestSchemaStructure:
    def test_basic_schema_structure(self):
        form = Form(
            name="test",
            fields=[TextField(name="x", label="X")],
        )
        schema = form_to_json_schema(form)

        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert schema["type"] == "object"
        assert schema["title"] == "test"
        assert "properties" in schema
        assert schema["additionalProperties"] is False

    def test_required_array_present_when_fields_required(self):
        form = Form(
            name="test",
            fields=[
                TextField(name="a", label="A", required=True),
                TextField(name="b", label="B"),
            ],
        )
        schema = form_to_json_schema(form)

        assert schema["required"] == ["a"]

    def test_required_key_absent_when_no_required_fields(self):
        form = Form(
            name="test",
            fields=[TextField(name="a", label="A")],
        )
        schema = form_to_json_schema(form)

        assert "required" not in schema

    def test_schema_is_json_serializable(self):
        form = Form(
            name="full",
            fields=[
                TextField(name="name", label="Name", required=True),
                EmailField(name="email", label="Email"),
                NumberField(name="age", label="Age", min_value=0, max_value=120),
            ],
        )
        schema = form_to_json_schema(form)
        json_str = json.dumps(schema)
        roundtrip = json.loads(json_str)

        assert roundtrip == schema


# ---------------------------------------------------------------------------
# TextField
# ---------------------------------------------------------------------------


class TestTextFieldSchema:
    def test_basic_text_field(self):
        form = Form(
            name="t",
            fields=[TextField(name="x", label="X")],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert prop["type"] == "string"
        assert prop["title"] == "X"

    def test_text_field_constraints(self):
        form = Form(
            name="t",
            fields=[
                TextField(
                    name="x",
                    label="X",
                    minlength=3,
                    maxlength=50,
                    pattern="^[a-z]+$",
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert prop["minLength"] == 3
        assert prop["maxLength"] == 50
        assert prop["pattern"] == "^[a-z]+$"

    def test_text_field_no_constraints(self):
        form = Form(
            name="t",
            fields=[TextField(name="x", label="X")],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert "minLength" not in prop
        assert "maxLength" not in prop
        assert "pattern" not in prop


# ---------------------------------------------------------------------------
# EmailField
# ---------------------------------------------------------------------------


class TestEmailFieldSchema:
    def test_email_field(self):
        form = Form(
            name="t",
            fields=[EmailField(name="email", label="Email")],
        )
        prop = form_to_json_schema(form)["properties"]["email"]

        assert prop["type"] == "string"
        assert prop["format"] == "email"


# ---------------------------------------------------------------------------
# NumberField
# ---------------------------------------------------------------------------


class TestNumberFieldSchema:
    def test_number_field_with_constraints(self):
        form = Form(
            name="t",
            fields=[
                NumberField(
                    name="n",
                    label="N",
                    min_value=0,
                    max_value=100,
                    step=0.5,
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["n"]

        assert prop["type"] == "number"
        assert prop["minimum"] == 0
        assert prop["maximum"] == 100
        assert prop["multipleOf"] == 0.5

    def test_number_field_no_constraints(self):
        form = Form(
            name="t",
            fields=[NumberField(name="n", label="N")],
        )
        prop = form_to_json_schema(form)["properties"]["n"]

        assert prop["type"] == "number"
        assert "minimum" not in prop
        assert "maximum" not in prop
        assert "multipleOf" not in prop


# ---------------------------------------------------------------------------
# DateField
# ---------------------------------------------------------------------------


class TestDateFieldSchema:
    def test_date_field(self):
        form = Form(
            name="t",
            fields=[DateField(name="d", label="D")],
        )
        prop = form_to_json_schema(form)["properties"]["d"]

        assert prop["type"] == "string"
        assert prop["format"] == "date"


# ---------------------------------------------------------------------------
# SelectField
# ---------------------------------------------------------------------------


class TestSelectFieldSchema:
    def test_single_select(self):
        form = Form(
            name="t",
            fields=[
                SelectField(
                    name="s",
                    label="S",
                    options=[
                        SelectOption(value="a", label="A"),
                        SelectOption(value="b", label="B"),
                    ],
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["s"]

        assert prop["type"] == "string"
        assert prop["enum"] == ["a", "b"]

    def test_multiple_select(self):
        form = Form(
            name="t",
            fields=[
                SelectField(
                    name="s",
                    label="S",
                    multiple=True,
                    min_selected=1,
                    max_selected=3,
                    options=[
                        SelectOption(value="x", label="X"),
                        SelectOption(value="y", label="Y"),
                        SelectOption(value="z", label="Z"),
                    ],
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["s"]

        assert prop["type"] == "array"
        assert prop["items"] == {"type": "string", "enum": ["x", "y", "z"]}
        assert prop["uniqueItems"] is True
        assert prop["minItems"] == 1
        assert prop["maxItems"] == 3


# ---------------------------------------------------------------------------
# RadioField
# ---------------------------------------------------------------------------


class TestRadioFieldSchema:
    def test_radio_field(self):
        form = Form(
            name="t",
            fields=[
                RadioField(
                    name="r",
                    label="R",
                    options=[
                        SelectOption(value="a", label="A"),
                        SelectOption(value="b", label="B"),
                    ],
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["r"]

        assert prop["type"] == "string"
        assert prop["enum"] == ["a", "b"]


# ---------------------------------------------------------------------------
# CheckboxField / CheckboxGroupField
# ---------------------------------------------------------------------------


class TestCheckboxFieldSchema:
    def test_single_checkbox(self):
        form = Form(
            name="t",
            fields=[CheckboxField(name="c", label="C")],
        )
        prop = form_to_json_schema(form)["properties"]["c"]

        assert prop["type"] == "boolean"

    def test_checkbox_group(self):
        form = Form(
            name="t",
            fields=[
                CheckboxGroupField(
                    name="cg",
                    label="CG",
                    options=[
                        SelectOption(value="a", label="A"),
                        SelectOption(value="b", label="B"),
                    ],
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["cg"]

        assert prop["type"] == "array"
        assert prop["items"] == {"type": "string", "enum": ["a", "b"]}
        assert prop["uniqueItems"] is True


# ---------------------------------------------------------------------------
# FileField
# ---------------------------------------------------------------------------


class TestFileFieldSchema:
    def test_single_file(self):
        form = Form(
            name="t",
            fields=[FileField(name="f", label="F")],
        )
        prop = form_to_json_schema(form)["properties"]["f"]

        assert prop["type"] == "string"
        assert prop["contentEncoding"] == "base64"

    def test_multiple_files(self):
        form = Form(
            name="t",
            fields=[FileField(name="f", label="F", multiple=True)],
        )
        prop = form_to_json_schema(form)["properties"]["f"]

        assert prop["type"] == "array"
        assert prop["items"] == {"type": "string", "contentEncoding": "base64"}


# ---------------------------------------------------------------------------
# HiddenField
# ---------------------------------------------------------------------------


class TestHiddenFieldSchema:
    def test_hidden_field(self):
        form = Form(
            name="t",
            fields=[HiddenField(name="h", label="H")],
        )
        prop = form_to_json_schema(form)["properties"]["h"]

        assert prop["type"] == "string"


# ---------------------------------------------------------------------------
# UrlField
# ---------------------------------------------------------------------------


class TestUrlFieldSchema:
    def test_url_field(self):
        form = Form(
            name="t",
            fields=[UrlField(name="u", label="U", minlength=10, maxlength=200)],
        )
        prop = form_to_json_schema(form)["properties"]["u"]

        assert prop["type"] == "string"
        assert prop["format"] == "uri"
        assert prop["minLength"] == 10
        assert prop["maxLength"] == 200


# ---------------------------------------------------------------------------
# TextareaField
# ---------------------------------------------------------------------------


class TestTextareaFieldSchema:
    def test_textarea_field(self):
        form = Form(
            name="t",
            fields=[
                TextareaField(name="ta", label="TA", minlength=5, maxlength=500)
            ],
        )
        prop = form_to_json_schema(form)["properties"]["ta"]

        assert prop["type"] == "string"
        assert prop["minLength"] == 5
        assert prop["maxLength"] == 500


# ---------------------------------------------------------------------------
# ListField
# ---------------------------------------------------------------------------


class TestListFieldSchema:
    def test_list_field_text(self):
        form = Form(
            name="t",
            fields=[
                ListField(
                    name="l",
                    label="L",
                    item_type="text",
                    min_items=1,
                    max_items=10,
                )
            ],
        )
        prop = form_to_json_schema(form)["properties"]["l"]

        assert prop["type"] == "array"
        assert prop["items"] == {"type": "string"}
        assert prop["minItems"] == 1
        assert prop["maxItems"] == 10

    def test_list_field_number(self):
        form = Form(
            name="t",
            fields=[ListField(name="l", label="L", item_type="number")],
        )
        prop = form_to_json_schema(form)["properties"]["l"]

        assert prop["items"] == {"type": "number"}

    def test_list_field_unknown_item_type_defaults_to_string(self):
        form = Form(
            name="t",
            fields=[ListField(name="l", label="L", item_type="custom")],
        )
        prop = form_to_json_schema(form)["properties"]["l"]

        assert prop["items"] == {"type": "string"}


# ---------------------------------------------------------------------------
# Common annotations
# ---------------------------------------------------------------------------


class TestCommonAnnotations:
    def test_label_becomes_title(self):
        form = Form(
            name="t",
            fields=[TextField(name="x", label="Full Name")],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert prop["title"] == "Full Name"

    def test_help_text_becomes_description(self):
        form = Form(
            name="t",
            fields=[
                TextField(name="x", label="X", help_text="Enter your name")
            ],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert prop["description"] == "Enter your name"

    def test_default_value(self):
        form = Form(
            name="t",
            fields=[TextField(name="x", label="X", default_value="hello")],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert prop["default"] == "hello"

    def test_readonly(self):
        form = Form(
            name="t",
            fields=[TextField(name="x", label="X", readonly=True)],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert prop["readOnly"] is True

    def test_no_optional_keys_when_not_set(self):
        form = Form(
            name="t",
            fields=[TextField(name="x", label=None)],
        )
        prop = form_to_json_schema(form)["properties"]["x"]

        assert "title" not in prop
        assert "description" not in prop
        assert "default" not in prop
        assert "readOnly" not in prop


# ---------------------------------------------------------------------------
# Integration via Form.export()
# ---------------------------------------------------------------------------


class TestExportIntegration:
    def test_export_json_schema_format(self):
        form = Form(
            name="registration",
            fields=[
                TextField(name="name", label="Name", required=True),
                EmailField(name="email", label="Email", required=True),
                NumberField(name="age", label="Age"),
            ],
        )
        result = form.export("json_schema")

        assert result["format"] == "json_schema"
        schema = result["output"]
        assert schema["title"] == "registration"
        assert "name" in schema["properties"]
        assert "email" in schema["properties"]
        assert "age" in schema["properties"]
        assert schema["required"] == ["name", "email"]

    def test_export_format_enum_value(self):
        assert ExportFormat.JSON_SCHEMA.value == "json_schema"


# ---------------------------------------------------------------------------
# FieldGroup / FormStep flattening
# ---------------------------------------------------------------------------


class TestFieldGroupAndStepFlattening:
    def test_fields_inside_group_are_included(self):
        form = Form(
            name="t",
            content=[
                FieldGroup(
                    title="Personal",
                    fields=[
                        TextField(name="first", label="First"),
                        TextField(name="last", label="Last"),
                    ],
                ),
                EmailField(name="email", label="Email"),
            ],
        )
        schema = form_to_json_schema(form)

        assert set(schema["properties"].keys()) == {"first", "last", "email"}

    def test_fields_inside_steps_are_included(self):
        form = Form(
            name="wizard",
            content=[
                FormStep(
                    title="Step 1",
                    content=[
                        TextField(name="name", label="Name", required=True),
                    ],
                ),
                FormStep(
                    title="Step 2",
                    content=[
                        EmailField(name="email", label="Email", required=True),
                    ],
                ),
            ],
        )
        schema = form_to_json_schema(form)

        assert set(schema["properties"].keys()) == {"name", "email"}
        assert schema["required"] == ["name", "email"]


# ---------------------------------------------------------------------------
# Full form roundtrip
# ---------------------------------------------------------------------------


class TestFullFormSchema:
    def test_comprehensive_form(self):
        form = Form(
            name="survey",
            fields=[
                TextField(
                    name="name",
                    label="Full Name",
                    required=True,
                    minlength=2,
                    maxlength=100,
                    help_text="Your legal name",
                ),
                EmailField(name="email", label="Email", required=True),
                NumberField(
                    name="age", label="Age", min_value=18, max_value=120
                ),
                SelectField(
                    name="country",
                    label="Country",
                    required=True,
                    options=[
                        SelectOption(value="us", label="United States"),
                        SelectOption(value="uk", label="United Kingdom"),
                    ],
                ),
                CheckboxField(name="terms", label="Accept Terms", required=True),
                RadioField(
                    name="plan",
                    label="Plan",
                    options=[
                        SelectOption(value="free", label="Free"),
                        SelectOption(value="pro", label="Pro"),
                    ],
                ),
            ],
        )
        schema = form_to_json_schema(form)

        assert schema["title"] == "survey"
        assert len(schema["properties"]) == 6
        assert schema["required"] == ["name", "email", "country", "terms"]

        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["name"]["minLength"] == 2
        assert schema["properties"]["name"]["description"] == "Your legal name"

        assert schema["properties"]["email"]["format"] == "email"
        assert schema["properties"]["age"]["minimum"] == 18
        assert schema["properties"]["country"]["enum"] == ["us", "uk"]
        assert schema["properties"]["terms"]["type"] == "boolean"
        assert schema["properties"]["plan"]["enum"] == ["free", "pro"]

        json_str = json.dumps(schema, indent=2)
        assert json.loads(json_str) == schema
