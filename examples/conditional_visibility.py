"""
Ejemplo de visibilidad condicional con visible_when.

Demuestra cómo ocultar/mostrar campos según el valor de otros campos,
y la diferencia entre validación legacy y dinámica.
"""

from codeforms import (
    Form,
    SelectField,
    SelectOption,
    TextField,
    VisibilityRule,
    validate_form_data,
    validate_form_data_dynamic,
)


def create_address_form() -> Form:
    """Crea un formulario de dirección con campos condicionales."""
    return Form(
        name="address_form",
        fields=[
            SelectField(
                name="country",
                label="Country",
                required=True,
                options=[
                    SelectOption(value="US", label="United States"),
                    SelectOption(value="AR", label="Argentina"),
                    SelectOption(value="UK", label="United Kingdom"),
                ],
            ),
            # Solo visible cuando country == "US"
            TextField(
                name="state",
                label="State",
                required=True,
                visible_when=[
                    VisibilityRule(field="country", operator="equals", value="US"),
                ],
            ),
            # Solo visible cuando country == "AR"
            TextField(
                name="province",
                label="Province",
                required=True,
                visible_when=[
                    VisibilityRule(field="country", operator="equals", value="AR"),
                ],
            ),
            # Solo visible cuando country == "UK"
            TextField(
                name="county",
                label="County",
                required=True,
                visible_when=[
                    VisibilityRule(field="country", operator="equals", value="UK"),
                ],
            ),
            # Siempre visible
            TextField(
                name="city",
                label="City",
                required=True,
            ),
        ],
    )


if __name__ == "__main__":
    form = create_address_form()
    data_us = {"country": "US", "state": "California", "city": "Los Angeles"}
    data_ar = {"country": "AR", "province": "Buenos Aires", "city": "CABA"}

    # --- Legacy validation: ignores visible_when ---
    print("=== Legacy validate_form_data (ignores visible_when) ===")
    result = validate_form_data(form, data_us)
    print(f"US data: success={result['success']}")
    if not result["success"]:
        print(f"  Errors: {result['errors']}")
        print(
            "  (Province and County are required but missing — legacy doesn't know they're hidden)"
        )

    # --- Dynamic validation: respects visible_when ---
    print("\n=== Dynamic validate_form_data_dynamic (respects visible_when) ===")
    result = validate_form_data_dynamic(form, data_us, respect_visibility=True)
    print(f"US data: success={result['success']}")
    if result["success"]:
        print(f"  Validated data: {result['data']}")
        print("  (Province and County are hidden, so not validated)")

    result = validate_form_data_dynamic(form, data_ar, respect_visibility=True)
    print(f"AR data: success={result['success']}")
    if result["success"]:
        print(f"  Validated data: {result['data']}")

    # --- Visible fields helper ---
    print("\n=== get_visible_fields ===")
    visible = form.get_visible_fields(data_us)
    print(f"Visible fields for US: {[f.name for f in visible]}")

    visible = form.get_visible_fields(data_ar)
    print(f"Visible fields for AR: {[f.name for f in visible]}")
