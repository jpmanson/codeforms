from __future__ import annotations

from codeforms import Form, ObjectListField, TextField, CheckboxField, validate_form_data
from codeforms.fields import FieldType
from codeforms.registry import get_registered_field_types


def build_form() -> Form:
    return Form(
        name="parallel_approvers",
        fields=[
            ObjectListField(
                name="parallel_approvals",
                label="Aprobadores",
                required=True,
                min_items=1,
                max_items=3,
                fields=[
                    TextField(name="approver_email", label="Email", required=True),
                    TextField(name="label", label="Etiqueta", required=True),
                    CheckboxField(name="required", label="Obligatorio"),
                ],
            )
        ],
    )


class TestObjectListFieldValidation:
    def test_validate_form_data_accepts_valid_object_list(self):
        form = build_form()

        result = validate_form_data(
            form,
            {
                "parallel_approvals": [
                    {
                        "approver_email": "ana@empresa.com",
                        "label": "Compras",
                        "required": True,
                    },
                    {
                        "approver_email": "luis@empresa.com",
                        "label": "Finanzas",
                    },
                ]
            },
        )

        assert result["success"] is True
        assert result["data"]["parallel_approvals"][0]["approver_email"] == "ana@empresa.com"
        assert result["data"]["parallel_approvals"][1]["label"] == "Finanzas"

    def test_form_validate_data_reports_nested_required_error(self):
        form = build_form()

        result = form.validate_data(
            {
                "parallel_approvals": [
                    {
                        "approver_email": "ana@empresa.com",
                    }
                ]
            }
        )

        assert result["success"] is False
        assert result["errors"] == [
            {
                "field": "parallel_approvals[0].label",
                "message": "The field label is required",
            }
        ]

    def test_validate_form_data_rejects_unknown_keys_in_items(self):
        form = build_form()

        result = validate_form_data(
            form,
            {
                "parallel_approvals": [
                    {
                        "approver_email": "ana@empresa.com",
                        "label": "Compras",
                        "unexpected": "value",
                    }
                ]
            },
        )

        assert result["success"] is False
        assert result["errors"] == [
            {
                "field": "parallel_approvals[0]",
                "message": "Unknown fields: unexpected",
            }
        ]

    def test_validate_form_data_enforces_min_and_max_items(self):
        form = build_form()

        too_few = validate_form_data(form, {"parallel_approvals": []})
        too_many = validate_form_data(
            form,
            {
                "parallel_approvals": [
                    {"approver_email": "a@empresa.com", "label": "A"},
                    {"approver_email": "b@empresa.com", "label": "B"},
                    {"approver_email": "c@empresa.com", "label": "C"},
                    {"approver_email": "d@empresa.com", "label": "D"},
                ]
            },
        )

        assert too_few["success"] is False
        assert too_few["errors"] == [
            {
                "field": "parallel_approvals",
                "message": "Expected at least 1 items",
            }
        ]
        assert too_many["success"] is False
        assert too_many["errors"] == [
            {
                "field": "parallel_approvals",
                "message": "Expected at most 3 items",
            }
        ]


class TestObjectListFieldSchema:
    def test_json_schema_exports_array_of_objects(self):
        form = build_form()

        schema = form.export("json_schema")["output"]
        prop = schema["properties"]["parallel_approvals"]

        assert prop["type"] == "array"
        assert prop["minItems"] == 1
        assert prop["maxItems"] == 3
        assert prop["items"]["type"] == "object"
        assert prop["items"]["additionalProperties"] is False
        assert prop["items"]["required"] == ["approver_email", "label"]
        assert prop["items"]["properties"]["approver_email"]["type"] == "string"
        assert prop["items"]["properties"]["required"]["type"] == "boolean"


class TestObjectListFieldRegistry:
    def test_builtin_registry_contains_object_list_field(self):
        registered = get_registered_field_types()

        assert FieldType.OBJECT_LIST.value in registered
        assert ObjectListField in registered[FieldType.OBJECT_LIST.value]

    def test_form_roundtrip_restores_object_list_field(self):
        form = build_form()

        restored = Form.loads(form.to_json())

        field = restored.fields[0]
        assert isinstance(field, ObjectListField)
        assert field.field_type == FieldType.OBJECT_LIST
        assert [subfield.name for subfield in field.fields] == [
            "approver_email",
            "label",
            "required",
        ]
