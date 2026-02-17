# codeforms

A Python library for dynamically creating, validating, and rendering web forms using [Pydantic](https://docs.pydantic.dev/).

## Installation

```bash
pip install codeforms
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add codeforms
```

Requires Python 3.12+.

## Quick Start

### Creating a Form

Everything starts with the `Form` class. A form is defined with a name and a list of fields.

```python
from codeforms import Form, TextField, EmailField, NumberField

form = Form(
    name="UserRegistration",
    fields=[
        TextField(name="full_name", label="Full Name", required=True),
        EmailField(name="email", label="Email", required=True),
        NumberField(name="age", label="Age"),
    ]
)
```

### The `Form` Class

The `Form` class is the main container for your form structure.

- `id` — Auto-generated UUID.
- `name` — Form name (used in HTML export and validation).
- `fields` — A list of field objects (e.g. `TextField`, `EmailField`).
- `css_classes` — Optional CSS classes for the `<form>` tag.
- `version` — Form version number.
- `attributes` — Dictionary of additional HTML attributes for the `<form>` tag.

## Field Types

All fields inherit from `FormFieldBase` and share these common attributes:

- `name` — Field name (maps to `name` in HTML).
- `label` — User-visible label.
- `field_type` — Field type (`FieldType` enum).
- `required` — Whether the field is mandatory.
- `placeholder` — Placeholder text inside the field.
- `default_value` — Default value.
- `help_text` — Help text displayed below the field.
- `css_classes` — CSS classes for the field element.
- `readonly` — Whether the field is read-only.
- `attributes` — Additional HTML attributes for the `<input>` tag.

### Available Fields

- **`TextField`** — Generic text input (`<input type="text">`).
  - `minlength`, `maxlength`: Min/max text length.
  - `pattern`: Regex pattern for validation.
- **`EmailField`** — Email address (`<input type="email">`).
- **`NumberField`** — Numeric value (`<input type="number">`).
  - `min_value`, `max_value`: Allowed value range.
  - `step`: Increment step.
- **`DateField`** — Date picker (`<input type="date">`).
  - `min_date`, `max_date`: Allowed date range.
- **`SelectField`** — Dropdown select (`<select>`).
  - `options`: List of `SelectOption(value="...", label="...")`.
  - `multiple`: Enables multi-select.
  - `min_selected`, `max_selected`: Selection count limits (multi-select only).
- **`RadioField`** — Radio buttons (`<input type="radio">`).
  - `options`: List of `SelectOption`.
  - `inline`: Display options inline.
- **`CheckboxField`** — Single checkbox (`<input type="checkbox">`).
- **`CheckboxGroupField`** — Group of checkboxes.
  - `options`: List of `SelectOption`.
  - `inline`: Display options inline.
- **`FileField`** — File upload (`<input type="file">`).
  - `accept`: Accepted file types (e.g. `"image/*,.pdf"`).
  - `multiple`: Allow multiple file uploads.
- **`HiddenField`** — Hidden field (`<input type="hidden">`).

## Data Validation

codeforms offers multiple ways to validate user-submitted data, leveraging Pydantic's validation engine.

### Recommended: `FormDataValidator`

The most robust approach is `FormDataValidator.create_model`, which dynamically generates a Pydantic model from your form definition. This gives you powerful validations and detailed error messages automatically.

```python
from codeforms import Form, FormDataValidator, TextField, SelectField, SelectOption
from pydantic import ValidationError

# 1. Define your form
form = Form(
    name="MyForm",
    fields=[
        TextField(name="name", label="Name", required=True),
        SelectField(
            name="country",
            label="Country",
            options=[
                SelectOption(value="us", label="United States"),
                SelectOption(value="uk", label="United Kingdom"),
            ]
        )
    ]
)

# 2. Create the validation model
ValidationModel = FormDataValidator.create_model(form)

# 3. Validate incoming data
user_data = {"name": "John", "country": "us"}

try:
    validated = ValidationModel.model_validate(user_data)
    print("Valid!", validated)
except ValidationError as e:
    print("Validation errors:", e.errors())
```

This approach integrates seamlessly with API backends like FastAPI or Flask, since it produces standard Pydantic models.

### Other Validation Methods

Two simpler alternatives exist, though `FormDataValidator` is preferred:

1. `form.validate_data(data)` — Built-in method on the `Form` class. Less flexible; doesn't produce Pydantic models.
2. `validate_form_data(form, data)` — Standalone function with basic validation logic.

## Exporting Forms

Once your form is defined, you can export it to different formats.

```python
# Export to plain HTML
html_output = form.export('html', submit=True)
print(html_output['output'])

# Export to HTML with Bootstrap 5 classes
bootstrap_output = form.export('html_bootstrap5', submit=True)
print(bootstrap_output['output'])

# Export to JSON
json_output = form.to_json()
print(json_output)

# Export to a Python dictionary
dict_output = form.to_dict()
print(dict_output)
```

### Supported Formats

| Format | Description |
|---|---|
| `html` | Semantic HTML |
| `html_bootstrap4` | HTML with Bootstrap 4 classes |
| `html_bootstrap5` | HTML with Bootstrap 5 classes |
| `json` | JSON representation of the form |
| `dict` | Python dictionary representation |

HTML export can also generate a `<script>` block for basic client-side validation.

## Internationalization (i18n)

All validation and export messages are locale-aware. **English** (`en`) and **Spanish** (`es`) are included out of the box, and you can register any additional language at runtime via `register_locale()`.

### Switching Locales

```python
from codeforms import set_locale, get_locale, get_available_locales

print(get_locale())            # "en"
print(get_available_locales()) # ["en", "es"]

set_locale("es")
# All validation messages will now be in Spanish
```

### Registering a Custom Locale

You can add any locale at runtime. Missing keys automatically fall back to English.

```python
from codeforms import register_locale, set_locale

register_locale("pt", {
    "field.required": "Este campo é obrigatório",
    "field.required_named": "O campo {name} é obrigatório",
    "email.invalid": "E-mail inválido",
    "number.min_value": "O valor deve ser maior ou igual a {min}",
    "form.validation_success": "Dados validados com sucesso",
    "form.data_validation_error": "Erro na validação dos dados",
})

set_locale("pt")
```

### Using the Translation Function

The `t()` function translates a message key, with optional interpolation:

```python
from codeforms import t, set_locale

set_locale("en")
print(t("field.required"))                     # "This field is required"
print(t("field.required_named", name="email")) # "The field email is required"

set_locale("es")
print(t("field.required"))                     # "Este campo es requerido"
print(t("text.minlength", min=3))              # "La longitud mínima es 3"
```

### Locale-Aware Validation

All validation functions respect the active locale:

```python
from codeforms import Form, TextField, validate_form_data, set_locale

form = Form(
    name="example",
    fields=[TextField(name="name", label="Name", required=True)]
)

set_locale("en")
result = validate_form_data(form, {})
print(result["errors"][0]["message"])  # "The field name is required"

set_locale("es")
result = validate_form_data(form, {})
print(result["errors"][0]["message"])  # "El campo name es requerido"
```

See [`examples/i18n_usage.py`](examples/i18n_usage.py) for a full working example.

## License

MIT
