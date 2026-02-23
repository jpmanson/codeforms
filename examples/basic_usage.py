"""
Basic usage examples for codeforms.

Demonstrates form creation, data validation, JSON serialization,
and HTML export.
"""

from codeforms import (
    CheckboxField,
    CheckboxGroupField,
    EmailField,
    Form,
    RadioField,
    SelectField,
    SelectOption,
    TextField,
    ValidationRule,
    validate_form_data,
)


def create_registration_form() -> Form:
    """Registration form with multiple field types and validation rules."""
    return Form(
        name="registration_form",
        fields=[
            TextField(
                name="username",
                label="Username",
                required=True,
                minlength=3,
                maxlength=50,
                validation_rules=[
                    ValidationRule(
                        type="regex",
                        value="^[a-zA-Z0-9_]+$",
                        message="Only letters, numbers, and underscores are allowed",
                    )
                ],
            ),
            EmailField(
                name="email",
                label="Email address",
                required=True,
                validation_rules=[
                    ValidationRule(
                        type="email",
                        value=True,
                        message="Must be a valid email address",
                    )
                ],
            ),
            CheckboxGroupField(
                name="notifications",
                label="Notifications",
                options=[
                    SelectOption(value="email", label="Email"),
                    SelectOption(value="sms", label="SMS"),
                    SelectOption(value="push", label="Push notifications"),
                ],
                help_text="Select your notification preferences",
            ),
            RadioField(
                name="plan",
                label="Subscription plan",
                options=[
                    SelectOption(value="basic", label="Basic"),
                    SelectOption(value="pro", label="Professional"),
                    SelectOption(value="enterprise", label="Enterprise"),
                ],
                required=True,
            ),
            CheckboxField(
                name="terms",
                label="I accept the terms and conditions",
                required=True,
                validation_rules=[
                    ValidationRule(
                        type="required",
                        value=True,
                        message="You must accept the terms and conditions",
                    )
                ],
            ),
        ],
    )


def create_product_form() -> Form:
    """Product form showcasing single and multi-select fields."""
    return Form(
        name="product_form",
        fields=[
            TextField(name="name", label="Product name", required=True),
            # Single select
            SelectField(
                name="category",
                label="Category",
                required=True,
                options=[
                    SelectOption(value="electronics", label="Electronics"),
                    SelectOption(value="clothing", label="Clothing"),
                    SelectOption(value="food", label="Food"),
                ],
            ),
            # Multi-select with limits
            SelectField(
                name="tags",
                label="Tags",
                multiple=True,
                min_selected=1,
                max_selected=3,
                options=[
                    SelectOption(value="new", label="New"),
                    SelectOption(value="sale", label="Sale"),
                    SelectOption(value="featured", label="Featured"),
                    SelectOption(value="limited", label="Limited edition"),
                    SelectOption(value="seasonal", label="Seasonal"),
                ],
                help_text="Select between 1 and 3 tags",
            ),
            # Multi-select without limits
            SelectField(
                name="colors",
                label="Available colors",
                multiple=True,
                options=[
                    SelectOption(value="red", label="Red"),
                    SelectOption(value="blue", label="Blue"),
                    SelectOption(value="green", label="Green"),
                    SelectOption(value="black", label="Black"),
                    SelectOption(value="white", label="White"),
                ],
            ),
        ],
    )


if __name__ == "__main__":
    # --- Product form: validation ---
    form = create_product_form()

    valid_data = {
        "name": "Product 1",
        "category": "electronics",
        "tags": ["new", "sale", "featured"],  # 3 tags (max allowed)
        "colors": ["red", "blue"],
    }

    invalid_data = {
        "name": "Product 2",
        "category": "invalid_category",  # invalid option
        "tags": ["new", "sale", "featured", "limited"],  # exceeds max of 3
        "colors": ["red", "invalid_color"],  # invalid option
    }

    print("\n=== Validating valid data ===")
    result = validate_form_data(form, valid_data)
    if result["success"]:
        print("Success:", result["message"])
        print("Validated data:", result["data"])
    else:
        print("Error:", result["message"])
        print("Errors:", result["errors"])

    print("\n=== Validating invalid data ===")
    result = validate_form_data(form, invalid_data)
    if result["success"]:
        print("Success:", result["message"])
        print("Validated data:", result["data"])
    else:
        print("Error:", result["message"])
        print("Errors:", result["errors"])

    # --- JSON serialization roundtrip ---
    print("\n=== JSON roundtrip ===")
    form_json = form.model_dump_json()
    print(form_json)

    form_imported = Form.loads(form_json)
    print(form_imported)

    result = validate_form_data(form_imported, valid_data)
    if result["success"]:
        print("Success:", result["message"])
        print("Validated data:", result["data"])
    else:
        print("Error:", result["message"])
        print("Errors:", result["errors"])

    # --- Contact form: default values and HTML export ---
    print("\n=== Contact form with HTML export ===")
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

    # Export as Bootstrap 4 HTML
    print(contact_form.export(output_format="html_bootstrap4", id="my_form"))

    # Validate data
    test_data = {"name": "John Doe", "email": "john@example.com"}
    result = contact_form.validate_data(test_data)
    print(result)
