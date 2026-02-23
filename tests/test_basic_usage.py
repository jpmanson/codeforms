from __future__ import annotations

import importlib.util
from pathlib import Path

from codeforms import EmailField, Form, TextField, validate_form_data


def _load_example_module():
    root = Path(__file__).resolve().parents[1]
    example_path = root / "examples" / "basic_usage.py"
    spec = importlib.util.spec_from_file_location("basic_usage_example", example_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_product_form_valid_data():
    form = _load_example_module().create_product_form()
    valid_data = {
        "name": "Product 1",
        "category": "electronics",
        "tags": ["new", "sale", "featured"],
        "colors": ["red", "blue"],
    }

    result = validate_form_data(form, valid_data)

    assert result["success"] is True
    assert result["data"] == valid_data
    assert "errors" not in result


def test_product_form_invalid_category_fails():
    form = _load_example_module().create_product_form()
    invalid_data = {
        "name": "Product 2",
        "category": "invalid_category",
        "tags": ["new", "sale"],
        "colors": ["red", "blue"],
    }

    result = validate_form_data(form, invalid_data)

    assert result["success"] is False
    assert result["errors"][0]["field"] == "category"
    assert "inv" in result["errors"][0]["message"].lower()


def test_product_form_invalid_colors_fails():
    form = _load_example_module().create_product_form()
    invalid_data = {
        "name": "Product 3",
        "category": "electronics",
        "tags": ["new"],
        "colors": ["red", "invalid_color"],
    }

    result = validate_form_data(form, invalid_data)

    assert result["success"] is False
    assert result["errors"][0]["field"] == "colors"


def test_product_form_json_roundtrip_keeps_validation():
    form = _load_example_module().create_product_form()
    form_json = form.model_dump_json()
    imported_form = Form.loads(form_json)
    valid_data = {
        "name": "Product 1",
        "category": "electronics",
        "tags": ["new", "sale", "featured"],
        "colors": ["red", "blue"],
    }

    result = validate_form_data(imported_form, valid_data)

    assert imported_form.name == "product_form"
    assert result["success"] is True
    assert result["data"] == valid_data


def test_contact_form_defaults_and_bootstrap_export():
    contact_form = Form(
        name="contact_form",
        fields=[
            TextField(
                name="name",
                label="Name",
                required=True,
                minlength=3,
                maxlength=50,
                pattern="^[a-zA-Z ]+$",
            ),
            EmailField(name="email", label="Email", required=True),
        ],
    )
    contact_form.set_default_values(
        data={"name": "John Doe", "email": "john@example.com"}
    )

    export_result = contact_form.export(output_format="html_bootstrap4", id="my_form")
    html = export_result["output"]
    validation = contact_form.validate_data(
        {"name": "John Doe", "email": "john@example.com"}
    )

    assert export_result["format"] == "html_bootstrap4"
    assert 'id="my_form"' in html
    assert 'name="name"' in html
    assert 'value="John Doe"' in html
    assert 'value="john@example.com"' in html
    assert validation["success"] is True


def test_registration_form_valid_data():
    form = _load_example_module().create_registration_form()
    valid_data = {
        "username": "user_123",
        "email": "u@example.com",
        "notifications": ["email", "push"],
        "plan": "pro",
        "terms": True,
    }

    result = validate_form_data(form, valid_data)

    assert result["success"] is True
    assert result["data"] == valid_data


def test_registration_form_missing_required_terms_fails():
    form = _load_example_module().create_registration_form()
    invalid_data = {
        "username": "user_123",
        "email": "u@example.com",
        "notifications": ["email", "push"],
        "plan": "pro",
    }

    result = validate_form_data(form, invalid_data)

    assert result["success"] is False
    assert result["errors"][0]["field"] == "terms"
