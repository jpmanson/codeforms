"""
Internationalization (i18n) module for codeforms.

Provides a configurable message system with locale-based message loading.
Default locale is English ('en'). Spanish ('es') is also included.

Usage:
    from codeforms.i18n import set_locale, get_locale, t, register_locale

    # Change locale globally
    set_locale('es')

    # Get a translated message
    msg = t('field.required')  # "Este campo es requerido"

    # With interpolation
    msg = t('field.required_named', name='email')  # "El campo email es requerido"

    # Register a custom locale
    register_locale('fr', {
        'field.required': 'Ce champ est obligatoire',
        ...
    })
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional


# --- Message catalogs per locale ---

_MESSAGES_EN: Dict[str, str] = {
    # Field-level validation
    "field.required": "This field is required",
    "field.required_named": "The field {name} is required",

    # TextField
    "text.minlength": "Minimum length is {min}",
    "text.maxlength": "Maximum length is {max}",
    "text.pattern_mismatch": "Value does not match the required pattern",
    "text.invalid_regex": "Invalid regex pattern",

    # EmailField
    "email.invalid": "Invalid email",

    # NumberField
    "number.min_value": "Value must be greater than or equal to {min}",
    "number.max_value": "Value must be less than or equal to {max}",
    "number.invalid": "Must be a valid number",

    # DateField
    "date.min_date": "Date must be after {min}",
    "date.max_date": "Date must be before {max}",
    "date.invalid_format": "Must be a valid date in YYYY-MM-DD format",

    # SelectField
    "select.invalid_option": "Invalid option selected",
    "select.invalid_options": "Invalid options selected",
    "select.invalid_option_value": "Invalid option: {value}. Must be one of: {valid}",
    "select.invalid_values": "Invalid values: {values}",
    "select.min_selected": "Must select at least {min} options",
    "select.max_selected": "Can select at most {max} options",
    "select.value_must_be_list": "Value must be a list",
    "select.min_selected_negative": "min_selected cannot be negative",
    "select.min_selected_requires_multiple": "min_selected can only be used with multiple=True",
    "select.max_selected_min_value": "max_selected must be greater than 0",
    "select.max_selected_requires_multiple": "max_selected can only be used with multiple=True",
    "select.max_less_than_min": "max_selected must be greater than or equal to min_selected",
    "select.invalid_value_must_be_one_of": "Invalid value. Must be one of: {valid}",

    # RadioField
    "radio.invalid_option": "Invalid option selected",
    "radio.default_must_be_string": "Default value must be a string",

    # CheckboxField
    "checkbox.must_be_boolean": "Must be a boolean value",
    "checkbox.default_must_be_boolean": "Default value must be a boolean",

    # CheckboxGroupField
    "checkbox_group.default_must_be_list": "Default value must be a list of values",
    "checkbox_group.invalid_options": "Invalid options selected",

    # UrlField
    "url.invalid_scheme": "URL must start with http:// or https://",

    # Form-level
    "form.unique_field_names": "Field names must be unique in the form",
    "form.unique_field_names_in_group": "Field names must be unique within group '{title}'",
    "form.validation_success": "Data validated successfully",
    "form.validation_error": "Validation error",
    "form.data_validation_error": "Data validation error",

    # Export / HTML
    "export.fix_errors": "Please fix the following errors:",
    "export.submit": "Submit",
    "export.field_required": "The field {label} is required",

    # Wizard / Multi-step
    "wizard.not_a_wizard_form": "This form is not configured as a wizard (no steps found)",
    "wizard.invalid_step_index": "Invalid step index {index}, must be between 0 and {max}",
    "wizard.step_validation_failed": "Validation failed for step {step}",
    "wizard.validation_failed": "Wizard validation failed",

    # Visibility
    "visibility.unknown_operator": "Unknown visibility operator: {operator}",
}

_MESSAGES_ES: Dict[str, str] = {
    # Validación a nivel de campo
    "field.required": "Este campo es requerido",
    "field.required_named": "El campo {name} es requerido",

    # TextField
    "text.minlength": "La longitud mínima es {min}",
    "text.maxlength": "La longitud máxima es {max}",
    "text.pattern_mismatch": "El valor no coincide con el patrón requerido",
    "text.invalid_regex": "Patrón regex inválido",

    # EmailField
    "email.invalid": "Email inválido",

    # NumberField
    "number.min_value": "El valor debe ser mayor o igual a {min}",
    "number.max_value": "El valor debe ser menor o igual a {max}",
    "number.invalid": "Debe ser un número válido",

    # DateField
    "date.min_date": "La fecha debe ser posterior a {min}",
    "date.max_date": "La fecha debe ser anterior a {max}",
    "date.invalid_format": "Debe ser una fecha válida en formato YYYY-MM-DD",

    # SelectField
    "select.invalid_option": "Opción inválida seleccionada",
    "select.invalid_options": "Opciones inválidas seleccionadas",
    "select.invalid_option_value": "Opción inválida: {value}. Debe ser una de: {valid}",
    "select.invalid_values": "Valores inválidos: {values}",
    "select.min_selected": "Debe seleccionar al menos {min} opciones",
    "select.max_selected": "Puede seleccionar máximo {max} opciones",
    "select.value_must_be_list": "El valor debe ser una lista",
    "select.min_selected_negative": "min_selected no puede ser negativo",
    "select.min_selected_requires_multiple": "min_selected solo puede usarse con multiple=True",
    "select.max_selected_min_value": "max_selected debe ser mayor que 0",
    "select.max_selected_requires_multiple": "max_selected solo puede usarse con multiple=True",
    "select.max_less_than_min": "max_selected debe ser mayor o igual que min_selected",
    "select.invalid_value_must_be_one_of": "Valor inválido. Debe ser uno de: {valid}",

    # RadioField
    "radio.invalid_option": "Opción inválida seleccionada",
    "radio.default_must_be_string": "El valor por defecto debe ser una cadena",

    # CheckboxField
    "checkbox.must_be_boolean": "Debe ser un valor booleano",
    "checkbox.default_must_be_boolean": "El valor por defecto debe ser un booleano",

    # CheckboxGroupField
    "checkbox_group.default_must_be_list": "El valor por defecto debe ser una lista de valores",
    "checkbox_group.invalid_options": "Opciones inválidas seleccionadas",

    # UrlField
    "url.invalid_scheme": "La URL debe comenzar con http:// o https://",

    # Formulario
    "form.unique_field_names": "Los nombres de los campos deben ser únicos en el formulario",
    "form.unique_field_names_in_group": "Los nombres de los campos deben ser únicos dentro del grupo '{title}'",
    "form.validation_success": "Datos validados correctamente",
    "form.validation_error": "Error en la validación",
    "form.data_validation_error": "Error en la validación de datos",

    # Exportación / HTML
    "export.fix_errors": "Por favor corrija los siguientes errores:",
    "export.submit": "Enviar",
    "export.field_required": "El campo {label} es requerido",

    # Wizard / Multi-paso
    "wizard.not_a_wizard_form": "Este formulario no está configurado como wizard (no se encontraron pasos)",
    "wizard.invalid_step_index": "Índice de paso inválido {index}, debe estar entre 0 y {max}",
    "wizard.step_validation_failed": "La validación falló para el paso {step}",
    "wizard.validation_failed": "La validación del wizard falló",

    # Visibilidad
    "visibility.unknown_operator": "Operador de visibilidad desconocido: {operator}",
}


# --- Registry ---

_locales: Dict[str, Dict[str, str]] = {
    "en": _MESSAGES_EN,
    "es": _MESSAGES_ES,
}

_current_locale: str = "en"


# --- Public API ---


def get_locale() -> str:
    """Return the current locale code (e.g. 'en', 'es')."""
    return _current_locale


def set_locale(locale: str) -> None:
    """
    Set the current locale.

    Args:
        locale: A locale code that has been registered (e.g. 'en', 'es').

    Raises:
        ValueError: If the locale has not been registered.
    """
    global _current_locale
    if locale not in _locales:
        available = ", ".join(sorted(_locales.keys()))
        raise ValueError(
            f"Unknown locale '{locale}'. Available locales: {available}"
        )
    _current_locale = locale


def get_available_locales() -> list[str]:
    """Return a sorted list of registered locale codes."""
    return sorted(_locales.keys())


def register_locale(locale: str, messages: Dict[str, str]) -> None:
    """
    Register a new locale or update an existing one.

    If the locale already exists, its messages are *merged* (new keys are
    added, existing keys are overwritten).

    Args:
        locale: Locale code (e.g. 'fr', 'pt').
        messages: Dict mapping message keys to translated strings.
    """
    if locale in _locales:
        _locales[locale].update(messages)
    else:
        _locales[locale] = dict(messages)


def get_messages(locale: Optional[str] = None) -> Dict[str, str]:
    """
    Return a *copy* of the message catalog for the given locale.

    Args:
        locale: Locale code.  Defaults to the current locale.
    """
    loc = locale or _current_locale
    return copy.copy(_locales.get(loc, _locales["en"]))


def t(key: str, **kwargs: Any) -> str:
    """
    Translate a message key using the current locale.

    Supports Python ``str.format()`` interpolation via keyword arguments.

    Args:
        key: Message key (e.g. ``'field.required_named'``).
        **kwargs: Interpolation values (e.g. ``name='email'``).

    Returns:
        The translated (and optionally interpolated) string.
        If the key is not found in the current locale, falls back to the
        English catalog.  If still not found, returns the key itself.
    """
    messages = _locales.get(_current_locale, _locales["en"])
    template = messages.get(key)
    if template is None:
        # Fallback to English
        template = _MESSAGES_EN.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template
