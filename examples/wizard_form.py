"""
Ejemplo de formulario multi-paso (wizard) con FormStep.

Demuestra cómo crear un formulario wizard con validación por paso
y validación global.
"""

from codeforms import (
    CheckboxField,
    EmailField,
    Form,
    FormStep,
    NumberField,
    SelectField,
    SelectOption,
    TextField,
)


def create_registration_wizard() -> Form:
    """Crea un formulario wizard de registro de usuario en 3 pasos."""
    return Form(
        name="registration_wizard",
        content=[
            # Paso 1: Información personal
            FormStep(
                title="Personal Information",
                description="Tell us about yourself",
                content=[
                    TextField(name="first_name", label="First Name", required=True),
                    TextField(name="last_name", label="Last Name", required=True),
                    EmailField(name="email", label="Email", required=True),
                ],
            ),
            # Paso 2: Preferencias
            FormStep(
                title="Preferences",
                description="Choose your plan and preferences",
                content=[
                    SelectField(
                        name="plan",
                        label="Plan",
                        required=True,
                        options=[
                            SelectOption(value="free", label="Free"),
                            SelectOption(value="pro", label="Professional"),
                            SelectOption(value="enterprise", label="Enterprise"),
                        ],
                    ),
                    NumberField(
                        name="team_size",
                        label="Team Size",
                        min_value=1,
                        max_value=1000,
                    ),
                ],
            ),
            # Paso 3: Confirmación
            FormStep(
                title="Confirmation",
                description="Review and accept the terms",
                content=[
                    CheckboxField(
                        name="terms",
                        label="I accept the terms and conditions",
                        required=True,
                    ),
                ],
                validation_mode="on_submit",
            ),
        ],
    )


if __name__ == "__main__":
    form = create_registration_wizard()

    # Verificar estructura
    print(f"Form: {form.name}")
    print(f"Steps: {len(form.get_steps())}")
    print(f"Total fields: {len(form.fields)}")

    for i, step in enumerate(form.get_steps()):
        print(f"\n  Step {i + 1}: {step.title}")
        for field in step.fields:
            print(
                f"    - {field.name} ({'required' if field.required else 'optional'})"
            )

    # Validar paso 1
    print("\n--- Validating Step 1 ---")
    result = form.validate_step(
        0,
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        },
    )
    print(f"Step 1 valid: {result['success']}")

    # Validar paso 2
    print("\n--- Validating Step 2 ---")
    result = form.validate_step(
        1,
        {
            "plan": "pro",
            "team_size": 5,
        },
    )
    print(f"Step 2 valid: {result['success']}")

    # Validar todos los pasos
    print("\n--- Validating All Steps ---")
    result = form.validate_all_steps(
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "plan": "pro",
            "team_size": 5,
            "terms": True,
        }
    )
    print(f"All steps valid: {result['success']}")

    # Exportar HTML
    print("\n--- HTML Export ---")
    export = form.export("html_bootstrap5")
    print(export["output"][:300] + "...")

    # JSON roundtrip
    print("\n--- JSON Roundtrip ---")
    json_str = form.model_dump_json()
    restored = Form.model_validate_json(json_str)
    print(f"Restored steps: {len(restored.get_steps())}")
    print(f"Restored fields: {len(restored.fields)}")
