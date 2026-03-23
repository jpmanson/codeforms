import json
import re
from typing import Any, Type

from codeforms.fields import *
from codeforms.fields import FieldGroup, FormStep
from codeforms.i18n import t


class Form(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    content: List[Any]
    css_classes: Optional[str] = None
    version: int = 1
    schema_version: Optional[int] = None  # Para compatibilidad entre versiones (RISK-5)
    attributes: Dict[str, str] = Field(default_factory=dict)
    action: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def convert_fields_to_content(cls, data: Any) -> Any:
        """
        Validador para mantener retrocompatibilidad y resolver items del contenido.
        Convierte automáticamente 'fields' a 'content' si está presente, y resuelve
        cada item usando el registro de tipos de campo.
        """
        if isinstance(data, dict):
            # Si tiene 'fields' pero no 'content', convertir
            if "fields" in data and "content" not in data:
                data = data.copy()
                data["content"] = data.pop("fields")
            # Si tiene ambos, 'content' tiene prioridad
            elif "fields" in data and "content" in data:
                data = data.copy()
                data.pop("fields")  # Remover 'fields' redundante

            # Resolver cada item del contenido usando el registry
            if "content" in data:
                from codeforms.registry import resolve_content_item

                data = data.copy() if data is not data else data
                data["content"] = [
                    resolve_content_item(item) for item in data["content"]
                ]
        return data

    @property
    def fields(self) -> List[FormFieldBase]:
        """
        Devuelve una lista plana de todos los campos del formulario,
        independientemente de si están en un grupo o no.
        Mantiene retrocompatibilidad con el código existente.
        """
        all_fields = []
        for item in self.content:
            if isinstance(item, FormStep) or isinstance(
                item, FieldGroup
            ):  # Es un FormStep (wizard)
                all_fields.extend(item.fields)
            else:  # Es un campo individual
                all_fields.append(item)
        return all_fields

    @staticmethod
    def loads(form: Union[str, dict, bytearray]):
        if isinstance(form, (str, bytearray)):
            return Form.model_validate_json(form)
        else:
            return Form.model_validate(form)

    @classmethod
    def create_from_fields(cls, name: str, fields: List, **kwargs) -> "Form":
        """
        Método de conveniencia para crear un formulario usando la estructura anterior
        donde se pasaba directamente una lista de campos.
        Mantiene retrocompatibilidad.
        """
        return cls(name=name, content=fields, **kwargs)

    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        return json.loads(self.model_dump_json(exclude_none=exclude_none))

    @model_validator(mode="after")
    def validate_field_names(self) -> "Form":
        """Valida que todos los nombres de campos sean únicos en todo el formulario"""
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError(t("form.unique_field_names"))
        return self

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida todos los campos del formulario y retorna el resultado"""
        errors = []
        validated_data = {}

        for field in self.fields:
            field_value = data.get(field.name)

            # Validar campo requerido
            if field.required and field_value is None:
                errors.append(
                    {
                        "field": field.name,
                        "message": t("field.required_named", name=field.name),
                    }
                )
                continue

            # Validar según el tipo de campo
            if isinstance(field, TextField):
                is_valid, error_msg = field.validate_value(field_value)
                if not is_valid:
                    errors.append({"field": field.name, "message": error_msg})
            elif isinstance(field, EmailField):
                if not re.match(r"[^@]+@[^@]+\.[^@]+", field_value):
                    errors.append({"field": field.name, "message": t("email.invalid")})
            elif isinstance(field, NumberField):
                try:
                    num_value = float(field_value)
                    if field.min_value is not None and num_value < field.min_value:
                        errors.append(
                            {
                                "field": field.name,
                                "message": t("number.min_value", min=field.min_value),
                            }
                        )
                    if field.max_value is not None and num_value > field.max_value:
                        errors.append(
                            {
                                "field": field.name,
                                "message": t("number.max_value", max=field.max_value),
                            }
                        )
                except (ValueError, TypeError):
                    errors.append({"field": field.name, "message": t("number.invalid")})
            elif isinstance(field, DateField):
                try:
                    date_value = date.fromisoformat(field_value)
                    if field.min_date is not None and date_value < field.min_date:
                        errors.append(
                            {
                                "field": field.name,
                                "message": t("date.min_date", min=field.min_date),
                            }
                        )
                    if field.max_date is not None and date_value > field.max_date:
                        errors.append(
                            {
                                "field": field.name,
                                "message": t("date.max_date", max=field.max_date),
                            }
                        )
                except (ValueError, TypeError):
                    errors.append(
                        {"field": field.name, "message": t("date.invalid_format")}
                    )
            elif isinstance(field, SelectField):
                valid_options = [opt.value for opt in field.options]
                if field.multiple:
                    if not isinstance(field_value, list) or not all(
                        v in valid_options for v in field_value
                    ):
                        errors.append(
                            {
                                "field": field.name,
                                "message": t("select.invalid_options"),
                            }
                        )
                elif field_value not in valid_options:
                    errors.append(
                        {"field": field.name, "message": t("select.invalid_option")}
                    )
            elif isinstance(field, RadioField):
                if field_value not in [opt.value for opt in field.options]:
                    errors.append(
                        {"field": field.name, "message": t("radio.invalid_option")}
                    )
            elif isinstance(field, CheckboxField):
                if not isinstance(field_value, bool):
                    errors.append(
                        {"field": field.name, "message": t("checkbox.must_be_boolean")}
                    )
            elif isinstance(field, CheckboxGroupField):
                if not isinstance(field_value, list) or not all(
                    v in [opt.value for opt in field.options] for v in field_value
                ):
                    errors.append(
                        {
                            "field": field.name,
                            "message": t("checkbox_group.invalid_options"),
                        }
                    )
            elif isinstance(field, ListField):
                value, field_errors = _validate_list_field_value(field, field_value)
                if field_errors:
                    errors.extend(field_errors)
                else:
                    validated_data[field.name] = value
            elif isinstance(field, ObjectListField):
                value, field_errors = _validate_object_list_field_value(
                    field, field_value
                )
                if field_errors:
                    errors.extend(field_errors)
                else:
                    validated_data[field.name] = value

            if not errors and field.name not in validated_data:
                validated_data[field.name] = field_value

        return {
            "success": len(errors) == 0,
            "data": validated_data if not errors else None,
            "errors": errors,
            "message": t("form.validation_success")
            if not errors
            else t("form.validation_error"),
        }

    def export(self, output_format: str = "html", **kwargs) -> dict:
        from codeforms.export import ExportFormat

        export_result = {"format": output_format}
        if output_format in [format.value for format in ExportFormat]:
            from codeforms.export import exporter

            export_result = exporter(self, output_format=output_format, **kwargs)

        elif output_format == "dict":
            export_result["output"] = self.to_dict()

        elif output_format == "json":
            export_result["output"] = self.model_dump_json()

        else:
            raise ValueError(f"Unsupported export format: {output_format}")

        return export_result

    def to_json(self) -> str:
        return self.export(output_format="json").get("output")

    def set_default_values(self, data: Dict[str, Any]) -> "Form":
        """Establece los valores por defecto para los campos del formulario"""
        for field in self.fields:
            field.default_value = data.get(field.name)
        return self

    def get_steps(self) -> List[FormStep]:
        """Retorna la lista de FormSteps en el formulario.
        Lista vacía si no es wizard."""
        return [item for item in self.content if isinstance(item, FormStep)]

    def get_visible_fields(self, data: Dict[str, Any]) -> List[FormFieldBase]:
        """Retorna solo los campos visibles según las reglas visible_when."""
        return [f for f in self.fields if evaluate_visibility(f, data)]

    def validate_step(
        self, step_index: int, data: Dict[str, Any], respect_visibility: bool = True
    ) -> Dict[str, Any]:
        """Valida un paso específico del wizard.

        Args:
            step_index: Índice del paso (0-based).
            data: Datos del formulario completo.
            respect_visibility: Si se respeta visible_when.

        Returns:
            Dict con success, data, errors, message.

        Raises:
            ValueError: Si step_index es inválido o no es wizard.
        """
        steps = self.get_steps()
        if not steps:
            raise ValueError(t("wizard.not_a_wizard_form"))
        if not (0 <= step_index < len(steps)):
            raise ValueError(
                t("wizard.invalid_step_index", index=step_index, max=len(steps) - 1)
            )
        return validate_form_data_dynamic(
            self, data, respect_visibility=respect_visibility, current_step=step_index
        )

    def validate_all_steps(
        self, data: Dict[str, Any], respect_visibility: bool = True
    ) -> Dict[str, Any]:
        """Valida todos los pasos del wizard secuencialmente.

        Returns:
            Dict con success, data, errors, step_errors, message.
        """
        steps = self.get_steps()
        if not steps:
            return validate_form_data_dynamic(self, data, respect_visibility)

        all_errors = []
        step_errors = {}
        all_validated_data = {}

        for idx in range(len(steps)):
            result = self.validate_step(idx, data, respect_visibility)
            if not result["success"]:
                step_errors[idx] = result.get("errors", [])
                all_errors.extend(result.get("errors", []))
            elif result.get("data"):
                all_validated_data.update(result["data"])

        success = len(all_errors) == 0
        return {
            "success": success,
            "data": all_validated_data if success else None,
            "errors": all_errors if all_errors else [],
            "step_errors": step_errors if step_errors else None,
            "message": t("form.validation_success")
            if success
            else t("wizard.validation_failed"),
        }


# Modelo para los datos recibidos
class FormDataModel(BaseModel):
    def __init__(self, form: Form):
        """
        Crea dinámicamente un modelo basado en la estructura del formulario
        """
        fields = {}
        for field in form.fields:
            # Definir el tipo y validaciones basadas en el campo del formulario
            if isinstance(field, EmailField):
                fields[field.name] = (EmailStr, ... if field.required else None)
            elif isinstance(field, CheckboxGroupField):
                fields[field.name] = (List[str], [] if not field.required else ...)
            elif isinstance(field, CheckboxField):
                fields[field.name] = (bool, ... if field.required else False)
            elif isinstance(field, NumberField):
                fields[field.name] = (float, ... if field.required else None)
            elif isinstance(field, DateField):
                fields[field.name] = (date, ... if field.required else None)
            elif isinstance(field, ListField):
                fields[field.name] = (List[Any], ... if field.required else [])
            elif isinstance(field, ObjectListField):
                fields[field.name] = (List[Dict[str, Any]], ... if field.required else [])
            else:
                fields[field.name] = (str, ... if field.required else None)

        # Crear el modelo dinámicamente
        self.__class__ = type(
            "DynamicFormData",
            (BaseModel,),
            {
                "__annotations__": fields,
                "model_config": {
                    "extra": "forbid"  # No permitir campos extra
                },
            },
        )
        super().__init__()


class FormDataValidator:
    @staticmethod
    def create_model(form: Form) -> Type[BaseModel]:
        fields = {}
        annotations = {}
        validations = {}

        for field in form.fields:
            # Configurar el tipo y las validaciones según el tipo de campo
            if isinstance(field, SelectField):
                valid_values = field.get_valid_values()
                if field.multiple:
                    field_type = List[str]

                    # Crear validador para la lista de valores
                    def create_validator(
                        valid_values=valid_values,
                        min_selected=field.min_selected,
                        max_selected=field.max_selected,
                    ):
                        def validate_select_values(v: List[str]) -> List[str]:
                            if not v and field.required:
                                raise ValueError(t("field.required"))

                            # Validar que todos los valores sean válidos
                            invalid_values = set(v) - valid_values
                            if invalid_values:
                                raise ValueError(
                                    t(
                                        "select.invalid_values",
                                        values=", ".join(invalid_values),
                                    )
                                )

                            # Validar cantidad mínima de selecciones
                            if min_selected is not None and len(v) < min_selected:
                                raise ValueError(
                                    t("select.min_selected", min=min_selected)
                                )

                            # Validar cantidad máxima de selecciones
                            if max_selected is not None and len(v) > max_selected:
                                raise ValueError(
                                    t("select.max_selected", max=max_selected)
                                )

                            return v

                        return validate_select_values

                    validations[field.name] = field_validator(field.name)(
                        create_validator()
                    )
                else:
                    field_type = str

                    # Crear validador para valor único
                    def create_validator(valid_values=valid_values):
                        def validate_select_value(v: str) -> str:
                            if not v and field.required:
                                raise ValueError(t("field.required"))
                            if v not in valid_values:
                                raise ValueError(
                                    t(
                                        "select.invalid_value_must_be_one_of",
                                        valid=", ".join(valid_values),
                                    )
                                )
                            return v

                        return validate_select_value

                    validations[field.name] = field_validator(field.name)(
                        create_validator()
                    )
            elif isinstance(field, EmailField):
                field_type = EmailStr
            elif isinstance(field, CheckboxGroupField):
                field_type = List[str]
            elif isinstance(field, CheckboxField):
                field_type = bool
            elif isinstance(field, NumberField):
                field_type = float
            elif isinstance(field, DateField):
                field_type = date
            elif isinstance(field, ListField):
                field_type = List[Any]
            elif isinstance(field, ObjectListField):
                field_type = List[Dict[str, Any]]
            else:
                field_type = str

            # Definir el campo con sus validaciones
            if field.required:
                fields[field.name] = Field(..., description=field.help_text)
            else:
                default_value = None
                if field_type in (List[str], List[Any], List[Dict[str, Any]]):
                    default_value = []
                fields[field.name] = Field(
                    default=default_value, description=field.help_text
                )

            annotations[field.name] = field_type

        # Crear el modelo dinámicamente
        model_name = f"Dynamic{form.name.title()}Data"
        model = type(
            model_name,
            (BaseModel,),
            {
                "__annotations__": annotations,
                **fields,
                **validations,
                "model_config": ConfigDict(
                    arbitrary_types_allowed=True, extra="forbid"
                ),
            },
        )

        return model


def _make_error(field_name: str, message: str) -> dict:
    return {"field": field_name, "message": message}


def _validate_primitive_list_item(item_type: str, value: Any) -> tuple[Any, Optional[str]]:
    if item_type == "number":
        try:
            return float(value), None
        except (TypeError, ValueError):
            return None, t("number.invalid")

    if item_type == "email":
        if not re.match(r"[^@]+@[^@]+\.[^@]+", str(value)):
            return None, t("email.invalid")
        return str(value), None

    if item_type == "url":
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            return None, t("url.invalid_scheme")
        return value, None

    if item_type == "date":
        try:
            return date.fromisoformat(str(value)).isoformat(), None
        except (TypeError, ValueError):
            return None, t("date.invalid_format")

    if not isinstance(value, str):
        value = str(value)
    return value, None


def _validate_list_field_value(field: ListField, field_value: Any, field_path: Optional[str] = None) -> tuple[Any, List[dict]]:
    field_name = field_path or field.name
    if isinstance(field_value, str):
        field_value = [field_value]

    if not isinstance(field_value, list):
        return None, [_make_error(field_name, t("select.value_must_be_list"))]

    if field.min_items is not None and len(field_value) < field.min_items:
        return None, [_make_error(field_name, f"Expected at least {field.min_items} items")]

    if field.max_items is not None and len(field_value) > field.max_items:
        return None, [_make_error(field_name, f"Expected at most {field.max_items} items")]

    validated_items = []
    errors = []
    for index, item in enumerate(field_value):
        validated_item, error_message = _validate_primitive_list_item(field.item_type, item)
        if error_message:
            errors.append(_make_error(f"{field_name}[{index}]", error_message))
        else:
            validated_items.append(validated_item)

    return (validated_items if not errors else None), errors


def _validate_object_list_field_value(field: ObjectListField, field_value: Any, field_path: Optional[str] = None) -> tuple[Any, List[dict]]:
    field_name = field_path or field.name
    if not isinstance(field_value, list):
        return None, [_make_error(field_name, t("select.value_must_be_list"))]

    if field.min_items is not None and len(field_value) < field.min_items:
        return None, [_make_error(field_name, f"Expected at least {field.min_items} items")]

    if field.max_items is not None and len(field_value) > field.max_items:
        return None, [_make_error(field_name, f"Expected at most {field.max_items} items")]

    allowed_fields = {subfield.name for subfield in field.fields}
    validated_items = []
    errors = []

    for index, item in enumerate(field_value):
        item_path = f"{field_name}[{index}]"
        if not isinstance(item, dict):
            errors.append(_make_error(item_path, "Each item must be an object"))
            continue

        extra_fields = sorted(set(item.keys()) - allowed_fields)
        if extra_fields:
            errors.append(_make_error(item_path, f"Unknown fields: {', '.join(extra_fields)}"))

        validated_item = {}
        item_errors = []
        for subfield in field.fields:
            subvalue = item.get(subfield.name)
            validated_value, suberrors = _validate_field_value(
                subfield,
                subvalue,
                item,
                field_path=f"{item_path}.{subfield.name}",
            )
            if suberrors:
                item_errors.extend(suberrors)
            elif validated_value is not None:
                validated_item[subfield.name] = validated_value

        if item_errors:
            errors.extend(item_errors)
        else:
            validated_items.append(validated_item)

    return (validated_items if not errors else None), errors


def validate_form_data(form: Form, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validated_data = {}
        for field in form.fields:
            field_value = data.get(field.name)
            value, errors = _validate_field_value(field, field_value, data)
            if errors:
                return {
                    "success": False,
                    "errors": errors,
                    "message": t("form.data_validation_error"),
                }
            if value is not None:
                validated_data[field.name] = value

        return {
            "success": True,
            "data": validated_data,
            "message": t("form.validation_success"),
        }

    except Exception as e:
        return {
            "success": False,
            "errors": [{"field": "unknown", "message": str(e)}],
            "message": t("form.data_validation_error"),
        }


def evaluate_visibility(field: FormFieldBase, data: Dict[str, Any]) -> bool:
    """Evalúa si un campo es visible basado en sus reglas visible_when.

    Sin reglas (visible_when=None) → siempre visible.
    Múltiples reglas → AND lógico (todas deben cumplirse).

    Args:
        field: Campo con posibles reglas visible_when.
        data: Datos del formulario para evaluar condiciones.

    Returns:
        True si el campo es visible, False si está oculto.
    """
    if field.visible_when is None:
        return True

    for rule in field.visible_when:
        field_value = data.get(rule.field)

        if rule.operator == "equals":
            if field_value != rule.value:
                return False
        elif rule.operator == "not_equals":
            if field_value == rule.value:
                return False
        elif rule.operator == "in":
            if field_value not in (rule.value or []):
                return False
        elif rule.operator == "not_in":
            if field_value in (rule.value or []):
                return False
        elif rule.operator == "gt":
            if not (field_value is not None and field_value > rule.value):
                return False
        elif rule.operator == "lt":
            if not (field_value is not None and field_value < rule.value):
                return False
        elif rule.operator == "is_empty":
            if field_value is not None and field_value != "" and field_value != []:
                return False
        elif rule.operator == "is_not_empty":
            if field_value is None or field_value == "" or field_value == []:
                return False

    return True


def _validate_field_value(
    field: FormFieldBase, field_value: Any, data: Dict[str, Any], field_path: Optional[str] = None
) -> tuple[Any, List[dict]]:
    """Valida un campo individual y retorna (validated_value, error_dict_or_None).

    Lógica de validación compartida entre validate_form_data y
    validate_form_data_dynamic. No modifica la función legacy.
    """
    field_name = field_path or field.name

    # Si no hay valor, usar el valor por defecto
    if field_value is None:
        field_value = field.default_value

    # Validar campo requerido
    if field.required and field_value is None:
        return None, [_make_error(field_name, t("field.required_named", name=field.name))]

    if field_value is None:
        return field_value, []

    # Select validation
    if field.field_type == FieldType.SELECT:
        valid_options = [opt.value for opt in field.options]
        if field.multiple:
            if isinstance(field_value, str):
                field_value = [field_value]
            if not isinstance(field_value, list):
                return None, [_make_error(field_name, t("select.value_must_be_list"))]
            invalid_values = [v for v in field_value if v not in valid_options]
            if invalid_values:
                return None, [_make_error(field_name, t("select.invalid_values", values=str(invalid_values)))]
        else:
            if field_value not in valid_options:
                return None, [_make_error(field_name, t(
                        "select.invalid_option_value",
                        value=field_value,
                        valid=str(valid_options),
                    ))]
        return field_value, []

    # Primitive list validation
    if field.field_type == FieldType.LIST:
        return _validate_list_field_value(field, field_value, field_name)

    # Object list validation
    if field.field_type == FieldType.OBJECT_LIST:
        return _validate_object_list_field_value(field, field_value, field_name)

    # Email validation
    if field.field_type == FieldType.EMAIL:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", str(field_value)):
            return None, [_make_error(field_name, t("email.invalid"))]
        return field_value, []

    # Checkbox group validation
    if field.field_type == FieldType.CHECKBOX and hasattr(field, "options"):
        valid_options = [opt.value for opt in field.options]
        if isinstance(field_value, str):
            field_value = [field_value]
        if not isinstance(field_value, list):
            return None, [_make_error(field_name, t("select.value_must_be_list"))]
        invalid_values = [v for v in field_value if v not in valid_options]
        if invalid_values:
            return None, [_make_error(field_name, t("select.invalid_values", values=str(invalid_values)))]
        return field_value, []

    # Single checkbox validation
    if field.field_type == FieldType.CHECKBOX and not hasattr(field, "options"):
        return bool(field_value), None

    # Radio validation
    if field.field_type == FieldType.RADIO:
        valid_options = [opt.value for opt in field.options]
        if field_value not in valid_options:
            return None, [_make_error(field_name, t("radio.invalid_option"))]
        return field_value, []

    # Number validation
    if field.field_type == FieldType.NUMBER:
        try:
            num_value = float(field_value)
            if hasattr(field, "min_value") and field.min_value is not None:
                if num_value < field.min_value:
                    return None, [_make_error(field_name, t("number.min_value", min=field.min_value))]
            if hasattr(field, "max_value") and field.max_value is not None:
                if num_value > field.max_value:
                    return None, [_make_error(field_name, t("number.max_value", max=field.max_value))]
            return num_value, None
        except (ValueError, TypeError):
            return None, [_make_error(field_name, t("number.invalid"))]

    # Text validation
    if field.field_type == FieldType.TEXT:
        if not isinstance(field_value, str):
            field_value = str(field_value)
        if hasattr(field, "minlength") and field.minlength is not None:
            if len(field_value) < field.minlength:
                return None, [_make_error(field_name, t("text.minlength", min=field.minlength))]
        if hasattr(field, "maxlength") and field.maxlength is not None:
            if len(field_value) > field.maxlength:
                return None, [_make_error(field_name, t("text.maxlength", max=field.maxlength))]
        return field_value, []

    # Default: pasar el valor sin validación adicional
    return field_value, []


def validate_form_data_dynamic(
    form: "Form",
    data: Dict[str, Any],
    respect_visibility: bool = True,
    current_step: Optional[int] = None,
) -> Dict[str, Any]:
    """Validación dinámica con soporte para visible_when y steps.

    A diferencia de validate_form_data(), esta función:
    - respect_visibility=True: Omite campos ocultos por visible_when.
    - current_step: Si se especifica, solo valida campos de ese paso.

    Las funciones legacy (validate_form_data, validate_data) NO se modifican.

    Args:
        form: Formulario a validar.
        data: Datos a validar.
        respect_visibility: Si True, no valida campos ocultos.
        current_step: Índice del paso a validar (None = todos los campos).

    Returns:
        Dict con success, data, errors, message.
    """
    try:
        validated_data = {}
        errors = []

        # Determinar qué campos validar
        if current_step is not None:
            steps = form.get_steps()
            if 0 <= current_step < len(steps):
                fields_to_validate = steps[current_step].fields
            else:
                return {
                    "success": False,
                    "errors": [
                        {
                            "field": "unknown",
                            "message": t(
                                "wizard.invalid_step_index",
                                index=current_step,
                                max=len(steps) - 1,
                            ),
                        }
                    ],
                    "message": t("form.data_validation_error"),
                }
        else:
            fields_to_validate = form.fields

        for field in fields_to_validate:
            # Evaluar visibilidad
            if respect_visibility and not evaluate_visibility(field, data):
                continue  # Campo oculto, no validar

            field_value = data.get(field.name)
            value, field_errors = _validate_field_value(field, field_value, data)

            if field_errors:
                errors.extend(field_errors)
            elif value is not None:
                validated_data[field.name] = value

        success = len(errors) == 0
        return {
            "success": success,
            "data": validated_data if success else None,
            "errors": errors if errors else [],
            "message": t("form.validation_success")
            if success
            else t("form.data_validation_error"),
        }

    except Exception as e:
        return {
            "success": False,
            "errors": [{"field": "unknown", "message": str(e)}],
            "message": t("form.data_validation_error"),
        }
