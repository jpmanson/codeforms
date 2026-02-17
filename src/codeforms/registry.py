"""
Field type registry for codeforms.

Maintains a mapping of field_type values to field classes, allowing
custom field types to be registered at runtime without modifying
the hardcoded Union types in Form or FieldGroup.

Usage:
    from codeforms.registry import register_field_type, get_registered_field_types

    class PhoneField(FormFieldBase):
        field_type: str = "phone"
        country_code: str = "+1"

    register_field_type(PhoneField)
"""

from __future__ import annotations

from typing import Any, Dict, List, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from codeforms.fields import FormFieldBase


# Maps field_type string value → list of candidate classes.
# Multiple classes may share a field_type (e.g. CheckboxField / CheckboxGroupField).
_field_type_registry: Dict[str, List[Type[FormFieldBase]]] = {}
_registry_initialized: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_field_type_key(cls: Type[FormFieldBase]) -> str:
    """Extract the field_type default value as a plain string."""
    field_info = cls.model_fields.get('field_type')
    if field_info is None:
        raise ValueError(f"{cls.__name__} has no 'field_type' field")
    default = field_info.default
    if default is None:
        raise ValueError(f"{cls.__name__} must define a default field_type value")
    return default.value if hasattr(default, 'value') else str(default)


def _register_class(cls: Type[FormFieldBase]) -> None:
    """Add a class to the internal registry (idempotent)."""
    key = _get_field_type_key(cls)
    if key not in _field_type_registry:
        _field_type_registry[key] = []
    if cls not in _field_type_registry[key]:
        _field_type_registry[key].append(cls)


def _init_builtin_types() -> None:
    """Lazily register all built-in field types (called once)."""
    global _registry_initialized
    if _registry_initialized:
        return
    _registry_initialized = True

    from codeforms.fields import (
        TextField, EmailField, NumberField, DateField,
        SelectField, RadioField, CheckboxField, CheckboxGroupField,
        FileField, HiddenField, UrlField, TextareaField, ListField,
    )

    for cls in [
        TextField, EmailField, NumberField, DateField,
        SelectField, RadioField, CheckboxField, CheckboxGroupField,
        FileField, HiddenField, UrlField, TextareaField, ListField,
    ]:
        _register_class(cls)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_field_type(field_class: Type[FormFieldBase]) -> None:
    """
    Register a custom field type so it can be used in Form and FieldGroup.

    The class must:
    - Be a subclass of ``FormFieldBase``.
    - Define a default ``field_type`` value (either a ``FieldType`` member
      or a plain string for truly custom types).

    Args:
        field_class: The field class to register.

    Raises:
        TypeError:  If *field_class* is not a FormFieldBase subclass.
        ValueError: If *field_class* has no default ``field_type``.

    Example::

        class PhoneField(FormFieldBase):
            field_type: str = "phone"
            country_code: str = "+1"

        register_field_type(PhoneField)
    """
    _init_builtin_types()
    from codeforms.fields import FormFieldBase as _Base
    if not issubclass(field_class, _Base):
        raise TypeError(
            f"{field_class.__name__} must be a subclass of FormFieldBase"
        )
    _register_class(field_class)


def get_registered_field_types() -> Dict[str, List[Type[FormFieldBase]]]:
    """
    Return a snapshot of the current registry.

    Returns:
        A dict mapping ``field_type`` string values to lists of
        candidate classes registered for that value.
    """
    _init_builtin_types()
    return {k: list(v) for k, v in _field_type_registry.items()}


def resolve_content_item(item: Any) -> Any:
    """
    Resolve a raw dict (or pass through an existing instance) to the
    appropriate field or FieldGroup instance, using the registry.

    Resolution rules:
    1. If *item* is not a dict, return it unchanged (already an instance).
    2. If the dict has ``title`` but no ``field_type``, treat it as a
       ``FieldGroup``.
    3. Otherwise, look up ``field_type`` in the registry and instantiate
       the best-matching class (the candidate whose declared model fields
       overlap most with the dict keys).

    Args:
        item: A dict from JSON/deserialization, or an already-validated
              model instance.

    Returns:
        A validated model instance.

    Raises:
        ValueError: If ``field_type`` is unknown.
    """
    _init_builtin_types()

    if not isinstance(item, dict):
        return item  # already an instance

    # Detect FieldGroup (has 'title', no 'field_type')
    if 'title' in item and 'field_type' not in item:
        from codeforms.fields import FieldGroup
        return FieldGroup.model_validate(item)

    field_type = item.get('field_type')
    if field_type is None:
        return item

    # Normalise enum → string
    if hasattr(field_type, 'value'):
        field_type = field_type.value

    candidates = _field_type_registry.get(field_type)
    if not candidates:
        raise ValueError(f"Unknown field type: {field_type!r}")

    if len(candidates) == 1:
        return candidates[0].model_validate(item)

    # Multiple candidates (e.g. CheckboxField / CheckboxGroupField):
    # pick the class whose declared fields overlap best with the input.
    best_cls = candidates[0]
    best_score = -1
    for cls in candidates:
        score = sum(1 for f in cls.model_fields if f in item)
        if score > best_score:
            best_score = score
            best_cls = cls

    return best_cls.model_validate(item)
