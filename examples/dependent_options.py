"""
Ejemplo de opciones dependientes con DependentOptionsConfig.

Demuestra cómo definir campos cuyos opciones cambian según el valor
de otro campo (por ejemplo, país → ciudades).
"""

from codeforms import (
    DependentOptionsConfig,
    Form,
    SelectField,
    SelectOption,
)


def create_location_form() -> Form:
    """Crea un formulario con ciudades dependientes del país seleccionado."""
    return Form(
        name="location_form",
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
            SelectField(
                name="city",
                label="City",
                required=True,
                # Opciones estáticas (todas las ciudades posibles para HTML rendering)
                options=[
                    SelectOption(value="nyc", label="New York City"),
                    SelectOption(value="la", label="Los Angeles"),
                    SelectOption(value="bsas", label="Buenos Aires"),
                    SelectOption(value="cor", label="Córdoba"),
                ],
                # Metadata de dependencia (para lógica dinámica en frontend o backend)
                dependent_options=DependentOptionsConfig(
                    depends_on="country",
                    options_map={
                        "US": [
                            SelectOption(value="nyc", label="New York City"),
                            SelectOption(value="la", label="Los Angeles"),
                        ],
                        "AR": [
                            SelectOption(value="bsas", label="Buenos Aires"),
                            SelectOption(value="cor", label="Córdoba"),
                        ],
                    },
                ),
            ),
        ],
    )


if __name__ == "__main__":
    form = create_location_form()

    # La metadata de dependencia se serializa a JSON
    import json

    data = json.loads(form.model_dump_json(exclude_none=True))
    city_field = data["content"][1]
    print("City field dependent_options:")
    print(json.dumps(city_field["dependent_options"], indent=2))

    # Las opciones específicas para cada país
    dep = form.fields[1].dependent_options
    print(f"\nOptions for US: {[o.label for o in dep.options_map['US']]}")
    print(f"Options for AR: {[o.label for o in dep.options_map['AR']]}")
