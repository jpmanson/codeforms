"""
Custom field types example for codeforms.

Demonstrates how to create and register custom field types,
use them in forms, and perform JSON roundtrip serialization.
"""

import json
from typing import Optional

from pydantic import field_validator

from codeforms import (
    Form,
    FormFieldBase,
    FieldGroup,
    TextField,
    EmailField,
    register_field_type,
    get_registered_field_types,
)


# ---------------------------------------------------------------------------
# 1. Define custom field types
# ---------------------------------------------------------------------------

class PhoneField(FormFieldBase):
    """A phone number field with an optional country code."""
    field_type: str = "phone"
    country_code: str = "+1"
    placeholder: Optional[str] = "e.g. +1-555-0100"


class RatingField(FormFieldBase):
    """A numeric rating field with configurable range."""
    field_type: str = "rating"
    min_rating: int = 1
    max_rating: int = 5

    @field_validator("max_rating")
    @classmethod
    def max_above_min(cls, v, info):
        min_r = info.data.get("min_rating", 1)
        if v <= min_r:
            raise ValueError("max_rating must be greater than min_rating")
        return v


class ColorField(FormFieldBase):
    """A colour picker field."""
    field_type: str = "color"
    color_format: str = "hex"  # hex | rgb | hsl


# ---------------------------------------------------------------------------
# 2. Register them
# ---------------------------------------------------------------------------

register_field_type(PhoneField)
register_field_type(RatingField)
register_field_type(ColorField)


def show_registered_types():
    """Print all registered field types."""
    print("=" * 60)
    print("Registered field types")
    print("=" * 60)
    for key, classes in sorted(get_registered_field_types().items()):
        names = ", ".join(c.__name__ for c in classes)
        print(f"  {key:12s} → {names}")
    print()


def create_form_with_custom_fields():
    """Build a form that mixes built-in and custom field types."""
    print("=" * 60)
    print("Form with custom fields")
    print("=" * 60)

    form = Form(
        name="event_feedback",
        content=[
            FieldGroup(
                title="Contact",
                fields=[
                    TextField(name="name", label="Full name", required=True),
                    EmailField(name="email", label="Email"),
                    PhoneField(name="phone", label="Phone", country_code="+54"),
                ],
            ),
            FieldGroup(
                title="Feedback",
                fields=[
                    RatingField(
                        name="overall_rating",
                        label="Overall rating",
                        max_rating=10,
                    ),
                    ColorField(
                        name="fav_color",
                        label="Favourite colour",
                        color_format="rgb",
                    ),
                ],
            ),
        ],
    )

    print(f"Form: {form.name}")
    print(f"Total fields: {len(form.fields)}")
    for f in form.fields:
        print(f"  - {f.name} ({f.field_type_value})")
    print()
    return form


def json_roundtrip(form: Form):
    """Serialize a form to JSON and back, preserving custom field data."""
    print("=" * 60)
    print("JSON roundtrip")
    print("=" * 60)

    json_str = form.to_json()
    print("Serialized JSON (pretty):")
    print(json.dumps(json.loads(json_str), indent=2))
    print()

    restored = Form.loads(json_str)
    print("Restored form fields:")
    for f in restored.fields:
        extra = ""
        if isinstance(f, PhoneField):
            extra = f" (country_code={f.country_code})"
        elif isinstance(f, RatingField):
            extra = f" (max_rating={f.max_rating})"
        elif isinstance(f, ColorField):
            extra = f" (color_format={f.color_format})"
        print(f"  - {f.name}: {type(f).__name__}{extra}")
    print()


def validate_custom_form(form: Form):
    """Validate user data against a form with custom fields."""
    print("=" * 60)
    print("Data validation")
    print("=" * 60)

    data = {
        "name": "Juan",
        "email": "juan@example.com",
        "phone": "+54-11-5555-0100",
        "overall_rating": "8",
        "fav_color": "#3498db",
    }
    result = form.validate_data(data)
    print(f"Input:   {data}")
    print(f"Result:  success={result['success']}")
    if result.get("errors"):
        print(f"Errors:  {result['errors']}")
    print()


def export_html(form: Form):
    """Export the form to plain HTML."""
    print("=" * 60)
    print("HTML export")
    print("=" * 60)
    export = form.export("html")
    print(export["output"][:500], "...")
    print()


# ---------------------------------------------------------------------------
# Run all examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    show_registered_types()
    form = create_form_with_custom_fields()
    json_roundtrip(form)
    validate_custom_form(form)
    export_html(form)
