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

Requires Python 3.9+.

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
| `json_schema` | [JSON Schema](http://json-schema.org/draft-07/schema#) (draft-07) |
| `json` | JSON representation of the form |
| `dict` | Python dictionary representation |

HTML export can also generate a `<script>` block for basic client-side validation.

### JSON Schema Export

Generate a standard [JSON Schema (draft-07)](http://json-schema.org/draft-07/schema#) from any form. The resulting schema is compatible with tools like [React JSON Schema Form](https://github.com/rjsf-team/react-jsonschema-form), [Angular Formly](https://formly.dev/), and any JSON Schema validator.

```python
import json
from codeforms import (
    Form, TextField, EmailField, NumberField, SelectField, SelectOption,
    CheckboxField, form_to_json_schema,
)

form = Form(
    name="registration",
    fields=[
        TextField(name="name", label="Full Name", required=True, minlength=2, maxlength=100),
        EmailField(name="email", label="Email", required=True),
        NumberField(name="age", label="Age", min_value=18, max_value=120),
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
    ],
)

# Option 1: Direct function call
schema = form_to_json_schema(form)
print(json.dumps(schema, indent=2))

# Option 2: Via form.export()
result = form.export("json_schema")
schema = result["output"]
```

Output:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "registration",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 2,
      "maxLength": 100,
      "title": "Full Name"
    },
    "email": {
      "type": "string",
      "format": "email",
      "title": "Email"
    },
    "age": {
      "type": "number",
      "minimum": 18,
      "maximum": 120,
      "title": "Age"
    },
    "country": {
      "type": "string",
      "enum": ["us", "uk"],
      "title": "Country"
    },
    "terms": {
      "type": "boolean",
      "title": "Accept Terms"
    }
  },
  "required": ["name", "email", "country", "terms"],
  "additionalProperties": false
}
```

#### Field Type Mapping

| codeforms Field | JSON Schema Type | Extra Keywords |
|---|---|---|
| `TextField` | `string` | `minLength`, `maxLength`, `pattern` |
| `EmailField` | `string` (`format: "email"`) | — |
| `NumberField` | `number` | `minimum`, `maximum`, `multipleOf` |
| `DateField` | `string` (`format: "date"`) | — |
| `SelectField` | `string` + `enum` | — |
| `SelectField` (`multiple=True`) | `array` of `enum` strings | `minItems`, `maxItems`, `uniqueItems` |
| `RadioField` | `string` + `enum` | — |
| `CheckboxField` | `boolean` | — |
| `CheckboxGroupField` | `array` of `enum` strings | `uniqueItems` |
| `FileField` | `string` (`contentEncoding: "base64"`) | — |
| `FileField` (`multiple=True`) | `array` of base64 strings | — |
| `HiddenField` | `string` | — |
| `UrlField` | `string` (`format: "uri"`) | `minLength`, `maxLength` |
| `TextareaField` | `string` | `minLength`, `maxLength` |
| `ListField` | `array` | `minItems`, `maxItems` |

Field annotations like `label`, `help_text`, `default_value`, and `readonly` map to the JSON Schema keywords `title`, `description`, `default`, and `readOnly` respectively.

Fields inside `FieldGroup` and `FormStep` containers are flattened into the top-level `properties` automatically.

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

## Dynamic Forms

### Conditional Visibility

Fields can be shown or hidden based on the value of other fields using `visible_when`. This is metadata that your frontend can use for dynamic UI, and the backend can respect during validation.

```python
from codeforms import Form, TextField, SelectField, SelectOption, VisibilityRule

form = Form(
    name="address",
    fields=[
        SelectField(
            name="country",
            label="Country",
            required=True,
            options=[
                SelectOption(value="US", label="United States"),
                SelectOption(value="AR", label="Argentina"),
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
```

Supported operators: `equals`, `not_equals`, `in`, `not_in`, `gt`, `lt`, `is_empty`, `is_not_empty`.

#### Dynamic Validation

Use `validate_form_data_dynamic()` to validate only the fields that are currently visible:

```python
from codeforms import validate_form_data_dynamic

result = validate_form_data_dynamic(
    form,
    {"country": "US", "state": "California"},
    respect_visibility=True,
)
print(result["success"])  # True — "province" is hidden, so not required
```

The legacy `validate_form_data()` function is unchanged and always validates all fields regardless of visibility.

#### Checking Visible Fields

```python
visible = form.get_visible_fields({"country": "US"})
print([f.name for f in visible])  # ["country", "state"]
```

See [`examples/conditional_visibility.py`](examples/conditional_visibility.py) for a full working example.

### Dependent Options

Use `DependentOptionsConfig` to define option sets that change based on another field's value:

```python
from codeforms import SelectField, SelectOption, DependentOptionsConfig

city_field = SelectField(
    name="city",
    label="City",
    options=[  # all possible options (for static HTML rendering)
        SelectOption(value="nyc", label="New York City"),
        SelectOption(value="bsas", label="Buenos Aires"),
    ],
    dependent_options=DependentOptionsConfig(
        depends_on="country",
        options_map={
            "US": [SelectOption(value="nyc", label="New York City")],
            "AR": [SelectOption(value="bsas", label="Buenos Aires")],
        },
    ),
)
```

The `dependent_options` metadata serializes to JSON for your frontend to consume. See [`examples/dependent_options.py`](examples/dependent_options.py).

## Multi-Step Wizard Forms

Use `FormStep` to split a form into multiple steps. Each step contains its own fields and can be validated independently.

```python
from codeforms import Form, FormStep, TextField, EmailField, CheckboxField

form = Form(
    name="registration",
    content=[
        FormStep(
            title="Personal Information",
            description="Tell us about yourself",
            content=[
                TextField(name="name", label="Name", required=True),
                EmailField(name="email", label="Email", required=True),
            ],
        ),
        FormStep(
            title="Confirmation",
            content=[
                CheckboxField(name="terms", label="I accept the terms", required=True),
            ],
            validation_mode="on_submit",
        ),
    ],
)
```

### Step Validation

```python
# Validate a single step
result = form.validate_step(0, {"name": "John", "email": "john@example.com"})
print(result["success"])  # True

# Validate all steps at once
result = form.validate_all_steps({
    "name": "John",
    "email": "john@example.com",
    "terms": True,
})
print(result["success"])  # True
```

### Wizard Helpers

```python
steps = form.get_steps()       # List[FormStep]
fields = form.fields           # Flat list of all fields across all steps
```

### HTML Export

Wizard forms export with `data-wizard="true"` on the `<form>` tag. Each step renders as a `<section data-step="true">` (not `<fieldset>`), so you can wire up your own step navigation in JavaScript.

See [`examples/wizard_form.py`](examples/wizard_form.py) for a full working example.

## Custom Field Types

You can create your own field types by subclassing `FormFieldBase` and registering them with `register_field_type()`. Custom fields integrate seamlessly with forms, JSON serialization, validation, and HTML export.

### Defining a Custom Field

```python
from codeforms import FormFieldBase, register_field_type

class PhoneField(FormFieldBase):
    field_type: str = "phone"       # unique string identifier
    country_code: str = "+1"

class RatingField(FormFieldBase):
    field_type: str = "rating"
    min_rating: int = 1
    max_rating: int = 5

register_field_type(PhoneField)
register_field_type(RatingField)
```

### Using Custom Fields in Forms

```python
from codeforms import Form, TextField

form = Form(
    name="feedback",
    fields=[
        TextField(name="name", label="Name", required=True),
        PhoneField(name="phone", label="Phone", country_code="+54"),
        RatingField(name="score", label="Score", max_rating=10),
    ],
)
```

### JSON Roundtrip

Custom fields serialize and deserialize automatically (as long as the field type is registered before deserialization):

```python
import json

json_str = form.to_json()
restored = Form.loads(json_str)

assert isinstance(restored.fields[1], PhoneField)
assert restored.fields[1].country_code == "+54"
```

### Listing Registered Types

```python
from codeforms import get_registered_field_types

for name, classes in sorted(get_registered_field_types().items()):
    print(f"{name}: {[c.__name__ for c in classes]}")
```

See [`examples/custom_fields.py`](examples/custom_fields.py) for a full working example.

## License

MIT
