"""
Internationalization (i18n) examples for codeforms.

Demonstrates how to switch locales, register custom translations,
and observe how validation messages change based on the active locale.
"""

from codeforms import (
    Form,
    TextField,
    EmailField,
    NumberField,
    SelectField,
    SelectOption,
    validate_form_data,
    set_locale,
    get_locale,
    get_available_locales,
    register_locale,
    t,
)


def create_sample_form() -> Form:
    """A simple form used across all i18n examples."""
    return Form(
        name="contact",
        fields=[
            TextField(name="name", label="Name", required=True, minlength=3),
            EmailField(name="email", label="Email", required=True),
            NumberField(name="age", label="Age", min_value=18, max_value=120),
            SelectField(
                name="country",
                label="Country",
                options=[
                    SelectOption(value="us", label="United States"),
                    SelectOption(value="ar", label="Argentina"),
                    SelectOption(value="de", label="Germany"),
                ],
            ),
        ],
    )


def example_default_locale():
    """Messages default to English."""
    print("=== Default locale (English) ===")
    print(f"Current locale: {get_locale()}")

    form = create_sample_form()

    # Missing required fields
    result = validate_form_data(form, {})
    print(f"Validation message: {result['message']}")
    print(f"Error: {result['errors'][0]['message']}")

    # Invalid email
    result = validate_form_data(form, {"name": "Alice", "email": "bad"})
    print(f"Email error: {result['errors'][0]['message']}")

    # Number out of range
    result = validate_form_data(form, {"name": "Alice", "email": "a@b.com", "age": 10})
    print(f"Age error: {result['errors'][0]['message']}")
    print()


def example_spanish_locale():
    """Switch to Spanish and see translated messages."""
    print("=== Spanish locale ===")
    set_locale("es")
    print(f"Current locale: {get_locale()}")

    form = create_sample_form()

    result = validate_form_data(form, {})
    print(f"Validation message: {result['message']}")
    print(f"Error: {result['errors'][0]['message']}")

    result = validate_form_data(form, {"name": "Ana", "email": "bad"})
    print(f"Email error: {result['errors'][0]['message']}")

    result = validate_form_data(form, {"name": "Ana", "email": "a@b.com", "age": 10})
    print(f"Age error: {result['errors'][0]['message']}")

    set_locale("en")  # Restore default
    print()


def example_register_custom_locale():
    """Register a new locale (Portuguese) and use it."""
    print("=== Custom locale (Portuguese) ===")

    register_locale("pt", {
        "field.required": "Este campo é obrigatório",
        "field.required_named": "O campo {name} é obrigatório",
        "email.invalid": "E-mail inválido",
        "number.min_value": "O valor deve ser maior ou igual a {min}",
        "number.max_value": "O valor deve ser menor ou igual a {max}",
        "form.validation_success": "Dados validados com sucesso",
        "form.data_validation_error": "Erro na validação dos dados",
    })

    set_locale("pt")
    print(f"Available locales: {get_available_locales()}")
    print(f"Current locale: {get_locale()}")

    form = create_sample_form()

    result = validate_form_data(form, {})
    print(f"Validation message: {result['message']}")
    print(f"Error: {result['errors'][0]['message']}")

    result = validate_form_data(form, {"name": "João", "email": "bad"})
    print(f"Email error: {result['errors'][0]['message']}")

    # Key not in 'pt' catalog → falls back to English
    result = validate_form_data(form, {
        "name": "João", "email": "a@b.com", "country": "invalid",
    })
    print(f"Select error (fallback to English): {result['errors'][0]['message']}")

    set_locale("en")  # Restore default
    print()


def example_translation_function():
    """Use the t() function directly for custom messages."""
    print("=== Using t() directly ===")

    set_locale("en")
    print(t("field.required"))
    print(t("field.required_named", name="email"))
    print(t("text.minlength", min=3))

    set_locale("es")
    print(t("field.required"))
    print(t("field.required_named", name="email"))
    print(t("text.minlength", min=3))

    set_locale("en")  # Restore default
    print()


def example_field_level_validation():
    """TextField.validate_value() also uses locale-aware messages."""
    print("=== Field-level validation ===")

    field = TextField(name="username", label="Username", required=True, minlength=5)

    set_locale("en")
    ok, msg = field.validate_value(None)
    print(f"[en] Required: {msg}")
    ok, msg = field.validate_value("ab")
    print(f"[en] Minlength: {msg}")

    set_locale("es")
    ok, msg = field.validate_value(None)
    print(f"[es] Required: {msg}")
    ok, msg = field.validate_value("ab")
    print(f"[es] Minlength: {msg}")

    set_locale("en")  # Restore default
    print()


if __name__ == "__main__":
    example_default_locale()
    example_spanish_locale()
    example_register_custom_locale()
    example_translation_function()
    example_field_level_validation()
