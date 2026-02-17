import re
from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Literal, Union, Dict, Any, Type, Set
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator, model_validator
from codeforms.i18n import t


class FieldType(str, Enum):
    TEXT = "text"
    PASSWORD = "password"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime-local"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    TEXTAREA = "textarea"
    FILE = "file"
    HIDDEN = "hidden"
    URL = "url"
    LIST = "list"


class ValidationRule(BaseModel):
    type: str  # required, min, max, regex, etc.
    value: Any
    message: str


class VisibilityRule(BaseModel):
    """Regla de visibilidad condicional para un campo."""
    field: str                    # nombre del campo del que depende
    operator: str = "equals"      # equals, not_equals, in, not_in, gt, lt, is_empty, is_not_empty
    value: Any = None             # valor a comparar


class SelectOption(BaseModel):
    value: str
    label: str
    selected: bool = False


class DependentOptionsConfig(BaseModel):
    """Configuración para opciones dependientes de otro campo."""
    depends_on: str                              # nombre del campo padre
    options_map: Dict[str, List[SelectOption]]    # valor_padre → opciones disponibles


class FormFieldBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    label: Union[str, None]
    field_type: Union[FieldType, str]
    required: bool = False
    placeholder: Optional[str] = None
    default_value: Optional[Any] = None
    help_text: Optional[str] = None
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    css_classes: Optional[str] = None
    readonly: bool = False
    attributes: Dict[str, str] = Field(default_factory=dict)
    visible_when: Optional[List[VisibilityRule]] = None
    dependent_options: Optional[DependentOptionsConfig] = None

    @field_validator('attributes', mode='before')
    @classmethod
    def coerce_attributes_to_strings(cls, v: Any) -> Dict[str, str]:
        """Coerce all attribute values to strings to handle cases like data_flags=1."""
        if v is None:
            return {}
        if isinstance(v, dict):
            return {str(k): str(val) for k, val in v.items()}
        return v

    model_config = {
        "json_serializers": {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    }

    @property
    def field_type_value(self) -> str:
        """Return the field_type as a plain string, whether it is a FieldType enum or str."""
        ft = self.field_type
        return ft.value if isinstance(ft, FieldType) else ft

    def export(self, output_format: str = 'html', **kwargs) -> str:
        """Método genérico para exportar el campo en diferentes formatos"""
        from codeforms.export import field_exporter
        return field_exporter(self, output_format, kwargs=kwargs)


class CheckboxField(FormFieldBase):
    field_type: FieldType = FieldType.CHECKBOX
    checked: bool = False
    value: str = "on"  # Valor por defecto cuando está marcado

    @field_validator('default_value')
    @classmethod
    def validate_default_value(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, bool):
            raise ValueError(t("checkbox.default_must_be_boolean"))
        return v


class CheckboxGroupField(FormFieldBase):
    field_type: FieldType = FieldType.CHECKBOX
    options: List[SelectOption]
    inline: bool = False

    @field_validator('default_value')
    @classmethod
    def validate_default_value(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, list):
            raise ValueError(t("checkbox_group.default_must_be_list"))
        return v


class RadioField(FormFieldBase):
    field_type: FieldType = FieldType.RADIO
    options: List[SelectOption]
    inline: bool = False

    @field_validator('default_value')
    @classmethod
    def validate_default_value(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, str):
            raise ValueError(t("radio.default_must_be_string"))
        return v


class SelectField(FormFieldBase):
    field_type: FieldType = FieldType.SELECT
    options: List[SelectOption]
    multiple: bool = False
    min_selected: Optional[int] = None  # Mínimo de opciones a seleccionar
    max_selected: Optional[int] = None  # Máximo de opciones a seleccionar

    @field_validator('min_selected')
    @classmethod
    def validate_min_selected(cls, v: Optional[int], info: Any) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError(t("select.min_selected_negative"))
            if not info.data.get('multiple', False):
                raise ValueError(t("select.min_selected_requires_multiple"))
        return v

    @field_validator('max_selected')
    @classmethod
    def validate_max_selected(cls, v: Optional[int], info: Any) -> Optional[int]:
        if v is not None:
            if v < 1:
                raise ValueError(t("select.max_selected_min_value"))
            if not info.data.get('multiple', False):
                raise ValueError(t("select.max_selected_requires_multiple"))
            min_selected = info.data.get('min_selected')
            if min_selected is not None and v < min_selected:
                raise ValueError(t("select.max_less_than_min"))
        return v

    def get_valid_values(self) -> Set[str]:
        """Retorna un conjunto de valores válidos para este campo"""
        return {option.value for option in self.options}


class TextField(FormFieldBase):
    field_type: FieldType = FieldType.TEXT
    minlength: Optional[int] = None
    maxlength: Optional[int] = None
    pattern: Optional[str] = None

    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                re.compile(v)
            except re.error:
                raise ValueError(t("text.invalid_regex"))
        return v

    def validate_value(self, value: str) -> tuple[bool, Optional[str]]:
        if value is None:
            if self.required:
                return False, t("field.required")
            return True, None

        if self.minlength and len(value) < self.minlength:
            return False, t("text.minlength", min=self.minlength)

        if self.maxlength and len(value) > self.maxlength:
            return False, t("text.maxlength", max=self.maxlength)

        if self.pattern and not re.match(self.pattern, value):
            return False, t("text.pattern_mismatch")

        return True, None


class EmailField(FormFieldBase):
    field_type: FieldType = FieldType.EMAIL

    @field_validator('default_value')
    @classmethod
    def validate_email(cls, v: Any) -> Any:
        if v is not None:
            EmailStr.validate(v)
        return v


class NumberField(FormFieldBase):
    field_type: FieldType = FieldType.NUMBER
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None


class DateField(FormFieldBase):
    field_type: FieldType = FieldType.DATE
    min_date: Optional[date] = None
    max_date: Optional[date] = None


class FileField(FormFieldBase):
    field_type: FieldType = FieldType.FILE
    accept: Optional[str] = None
    multiple: bool = False


class HiddenField(FormFieldBase):
    field_type: FieldType = FieldType.HIDDEN
    value: Union[str, int, float, bool] = ""


class UrlField(FormFieldBase):
    """Campo para URLs"""
    field_type: FieldType = FieldType.URL
    minlength: Optional[int] = None
    maxlength: Optional[int] = None

    @field_validator('default_value')
    @classmethod
    def validate_url(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str):
            # Validación básica de URL
            if not v.startswith(('http://', 'https://')):
                raise ValueError(t("url.invalid_scheme"))
        return v


class TextareaField(FormFieldBase):
    """Campo de texto multilínea"""
    field_type: FieldType = FieldType.TEXTAREA
    minlength: Optional[int] = None
    maxlength: Optional[int] = None
    rows: Optional[int] = 3
    cols: Optional[int] = None


class ListField(FormFieldBase):
    """Campo para listas de valores (ej: lista de participantes)"""
    field_type: FieldType = FieldType.LIST
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    item_type: str = "text"  # Tipo de cada item en la lista


class FieldGroup(BaseModel):
    """Representa un grupo de campos en un formulario para organización en secciones"""
    container_type: str = "group"  # Discriminador explícito para distinguir de FormStep
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    fields: List[Any]
    css_classes: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    collapsible: bool = False  # Si el grupo puede colapsarse
    collapsed: bool = False    # Si el grupo está colapsado por defecto

    model_config = {
        "json_serializers": {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    }

    @model_validator(mode='before')
    @classmethod
    def resolve_group_fields(cls, data: Any) -> Any:
        """Resolve field dicts to instances using the registry."""
        if isinstance(data, dict) and 'fields' in data:
            from codeforms.registry import resolve_content_item
            data = data.copy()
            data['fields'] = [resolve_content_item(item) for item in data['fields']]
        return data

    @model_validator(mode='after')
    def validate_field_names_in_group(self) -> 'FieldGroup':
        """Valida que los nombres de campos dentro del grupo sean únicos"""
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError(t("form.unique_field_names_in_group", title=self.title))
        return self

    def export(self, output_format: str = 'html', **kwargs) -> str:
        """Método para exportar el grupo de campos en diferentes formatos"""
        from codeforms.export import group_exporter
        return group_exporter(self, output_format, kwargs=kwargs)


class FormStep(BaseModel):
    """Representa un paso en un formulario multi-paso (wizard).

    Agrupa campos y/o grupos de campos en una secuencia lógica.
    Se diferencia de FieldGroup mediante el discriminador explícito type="step".
    """
    type: Literal["step"] = "step"  # Discriminador explícito (RISK-1)
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    content: List[Any]  # Puede contener campos y/o FieldGroups
    css_classes: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    validation_mode: str = "on_next"  # on_next | on_submit | on_change
    skippable: bool = False

    model_config = {
        "json_serializers": {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    }

    @field_validator('attributes', mode='before')
    @classmethod
    def coerce_attributes_to_strings(cls, v: Any) -> Dict[str, str]:
        if v is None:
            return {}
        if isinstance(v, dict):
            return {str(k): str(val) for k, val in v.items()}
        return v

    @model_validator(mode='before')
    @classmethod
    def resolve_step_content(cls, data: Any) -> Any:
        """Resolver items del contenido del paso usando el registry."""
        if isinstance(data, dict) and 'content' in data:
            from codeforms.registry import resolve_content_item
            data = data.copy()
            data['content'] = [resolve_content_item(item) for item in data['content']]
        return data

    @property
    def fields(self) -> List[FormFieldBase]:
        """Devuelve una lista plana de todos los campos en este paso,
        incluyendo campos dentro de FieldGroups anidados (RISK-2)."""
        all_fields = []
        for item in self.content:
            if isinstance(item, FieldGroup):
                all_fields.extend(item.fields)
            elif isinstance(item, FormFieldBase):
                all_fields.append(item)
        return all_fields

    def export(self, output_format: str = 'html', **kwargs) -> str:
        """Exportar el paso en diferentes formatos."""
        from codeforms.export import step_exporter
        return step_exporter(self, output_format, kwargs=kwargs)

