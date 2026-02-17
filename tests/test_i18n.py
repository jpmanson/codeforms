"""Tests for the internationalization (i18n) module."""

from __future__ import annotations

import pytest
from codeforms import (
    Form,
    TextField,
    EmailField,
    SelectField,
    CheckboxField,
    RadioField,
    NumberField,
    DateField,
    CheckboxGroupField,
    UrlField,
    SelectOption,
    FieldGroup,
    validate_form_data,
    set_locale,
    get_locale,
    get_available_locales,
    register_locale,
    get_messages,
    t,
)


@pytest.fixture(autouse=True)
def reset_locale():
    """Ensure every test starts with the default locale ('en') and restores it after."""
    original = get_locale()
    set_locale("en")
    yield
    set_locale(original)


# ---------------------------------------------------------------------------
# Core i18n API
# ---------------------------------------------------------------------------

class TestLocaleManagement:
    def test_default_locale_is_english(self):
        assert get_locale() == "en"

    def test_set_locale_to_spanish(self):
        set_locale("es")
        assert get_locale() == "es"

    def test_set_locale_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown locale"):
            set_locale("xx")

    def test_available_locales_contains_en_and_es(self):
        locales = get_available_locales()
        assert "en" in locales
        assert "es" in locales

    def test_register_new_locale(self):
        register_locale("fr", {"field.required": "Ce champ est obligatoire"})
        assert "fr" in get_available_locales()
        set_locale("fr")
        assert t("field.required") == "Ce champ est obligatoire"

    def test_register_locale_merges_existing(self):
        register_locale("es", {"custom.key": "Valor personalizado"})
        set_locale("es")
        # Original keys still present
        assert t("field.required") == "Este campo es requerido"
        # New key available
        assert t("custom.key") == "Valor personalizado"

    def test_get_messages_returns_copy(self):
        msgs = get_messages("en")
        msgs["field.required"] = "CHANGED"
        # Original not affected
        assert t("field.required") == "This field is required"


class TestTranslationFunction:
    def test_t_returns_english_by_default(self):
        assert t("field.required") == "This field is required"

    def test_t_returns_spanish_when_locale_is_es(self):
        set_locale("es")
        assert t("field.required") == "Este campo es requerido"

    def test_t_interpolation(self):
        msg = t("field.required_named", name="email")
        assert msg == "The field email is required"

    def test_t_interpolation_spanish(self):
        set_locale("es")
        msg = t("field.required_named", name="email")
        assert msg == "El campo email es requerido"

    def test_t_unknown_key_returns_key(self):
        assert t("nonexistent.key") == "nonexistent.key"

    def test_t_fallback_to_english(self):
        register_locale("pt", {"field.required": "Campo obrigatório"})
        set_locale("pt")
        # Key exists in pt
        assert t("field.required") == "Campo obrigatório"
        # Key missing in pt — falls back to English
        assert t("email.invalid") == "Invalid email"


# ---------------------------------------------------------------------------
# Messages in English (default)
# ---------------------------------------------------------------------------

class TestEnglishMessages:
    def test_form_validate_data_required_field(self):
        form = Form(
            name="test",
            fields=[TextField(name="name", label="Name", required=True)],
        )
        result = form.validate_data({"other": "value"})
        assert result["success"] is False
        assert "The field name is required" in result["errors"][0]["message"]

    def test_form_validate_data_success_message(self):
        form = Form(
            name="test",
            fields=[TextField(name="name", label="Name", required=False)],
        )
        result = form.validate_data({"name": "Alice"})
        assert result["success"] is True
        assert result["message"] == "Data validated successfully"

    def test_validate_form_data_required_field(self):
        form = Form(
            name="test",
            fields=[TextField(name="name", label="Name", required=True)],
        )
        result = validate_form_data(form, {})
        assert result["success"] is False
        assert "The field name is required" in result["errors"][0]["message"]
        assert result["message"] == "Data validation error"

    def test_validate_form_data_success(self):
        form = Form(
            name="test",
            fields=[TextField(name="name", label="Name")],
        )
        result = validate_form_data(form, {"name": "Bob"})
        assert result["success"] is True
        assert result["message"] == "Data validated successfully"

    def test_email_invalid(self):
        form = Form(
            name="test",
            fields=[EmailField(name="email", label="Email", required=True)],
        )
        result = form.validate_data({"email": "not-an-email"})
        assert result["success"] is False
        assert result["errors"][0]["message"] == "Invalid email"

    def test_number_min_value(self):
        form = Form(
            name="test",
            fields=[NumberField(name="age", label="Age", min_value=18)],
        )
        result = form.validate_data({"age": "10"})
        assert result["success"] is False
        assert "greater than or equal to 18" in result["errors"][0]["message"]

    def test_number_invalid(self):
        form = Form(
            name="test",
            fields=[NumberField(name="age", label="Age")],
        )
        result = form.validate_data({"age": "abc"})
        assert result["success"] is False
        assert "valid number" in result["errors"][0]["message"]

    def test_select_invalid_option(self):
        form = Form(
            name="test",
            fields=[
                SelectField(
                    name="color",
                    label="Color",
                    options=[
                        SelectOption(value="red", label="Red"),
                        SelectOption(value="blue", label="Blue"),
                    ],
                )
            ],
        )
        result = form.validate_data({"color": "green"})
        assert result["success"] is False
        assert "Invalid option selected" in result["errors"][0]["message"]

    def test_checkbox_must_be_boolean(self):
        form = Form(
            name="test",
            fields=[CheckboxField(name="agree", label="Agree")],
        )
        result = form.validate_data({"agree": "yes"})
        assert result["success"] is False
        assert "boolean" in result["errors"][0]["message"]

    def test_radio_invalid_option(self):
        form = Form(
            name="test",
            fields=[
                RadioField(
                    name="size",
                    label="Size",
                    options=[
                        SelectOption(value="s", label="Small"),
                        SelectOption(value="m", label="Medium"),
                    ],
                )
            ],
        )
        result = form.validate_data({"size": "xl"})
        assert result["success"] is False
        assert "Invalid option selected" in result["errors"][0]["message"]


# ---------------------------------------------------------------------------
# Messages in Spanish
# ---------------------------------------------------------------------------

class TestSpanishMessages:
    def test_form_validate_data_required_field_es(self):
        set_locale("es")
        form = Form(
            name="test",
            fields=[TextField(name="nombre", label="Nombre", required=True)],
        )
        result = form.validate_data({})
        assert result["success"] is False
        assert "El campo nombre es requerido" in result["errors"][0]["message"]

    def test_form_validate_data_success_es(self):
        set_locale("es")
        form = Form(
            name="test",
            fields=[TextField(name="nombre", label="Nombre")],
        )
        result = form.validate_data({"nombre": "Ana"})
        assert result["success"] is True
        assert result["message"] == "Datos validados correctamente"

    def test_validate_form_data_required_es(self):
        set_locale("es")
        form = Form(
            name="test",
            fields=[TextField(name="nombre", label="Nombre", required=True)],
        )
        result = validate_form_data(form, {})
        assert result["success"] is False
        assert "El campo nombre es requerido" in result["errors"][0]["message"]
        assert result["message"] == "Error en la validación de datos"

    def test_email_invalid_es(self):
        set_locale("es")
        form = Form(
            name="test",
            fields=[EmailField(name="email", label="Email", required=True)],
        )
        result = form.validate_data({"email": "bad"})
        assert result["success"] is False
        assert result["errors"][0]["message"] == "Email inválido"

    def test_number_min_value_es(self):
        set_locale("es")
        form = Form(
            name="test",
            fields=[NumberField(name="edad", label="Edad", min_value=18)],
        )
        result = form.validate_data({"edad": "5"})
        assert result["success"] is False
        assert "mayor o igual a 18" in result["errors"][0]["message"]


# ---------------------------------------------------------------------------
# Field-level validator messages
# ---------------------------------------------------------------------------

class TestFieldValidatorMessages:
    def test_text_field_validate_value_required_en(self):
        field = TextField(name="x", label="X", required=True)
        ok, msg = field.validate_value(None)
        assert not ok
        assert msg == "This field is required"

    def test_text_field_validate_value_required_es(self):
        set_locale("es")
        field = TextField(name="x", label="X", required=True)
        ok, msg = field.validate_value(None)
        assert not ok
        assert msg == "Este campo es requerido"

    def test_text_field_minlength_en(self):
        field = TextField(name="x", label="X", minlength=5)
        ok, msg = field.validate_value("ab")
        assert not ok
        assert msg == "Minimum length is 5"

    def test_text_field_minlength_es(self):
        set_locale("es")
        field = TextField(name="x", label="X", minlength=5)
        ok, msg = field.validate_value("ab")
        assert not ok
        assert msg == "La longitud mínima es 5"

    def test_text_field_maxlength_en(self):
        field = TextField(name="x", label="X", maxlength=3)
        ok, msg = field.validate_value("abcdef")
        assert not ok
        assert msg == "Maximum length is 3"

    def test_text_field_pattern_mismatch_en(self):
        field = TextField(name="x", label="X", pattern=r"^\d+$")
        ok, msg = field.validate_value("abc")
        assert not ok
        assert msg == "Value does not match the required pattern"

    def test_checkbox_default_must_be_boolean_en(self):
        with pytest.raises(Exception, match="boolean"):
            CheckboxField(name="x", label="X", default_value="nope")

    def test_checkbox_group_default_must_be_list_en(self):
        with pytest.raises(Exception, match="list"):
            CheckboxGroupField(
                name="x",
                label="X",
                options=[SelectOption(value="a", label="A")],
                default_value="not_a_list",
            )

    def test_radio_default_must_be_string_en(self):
        with pytest.raises(Exception, match="string"):
            RadioField(
                name="x",
                label="X",
                options=[SelectOption(value="a", label="A")],
                default_value=123,
            )

    def test_url_invalid_scheme_en(self):
        with pytest.raises(Exception, match="http"):
            UrlField(name="x", label="X", default_value="ftp://example.com")

    def test_select_min_selected_negative_en(self):
        with pytest.raises(Exception, match="negative"):
            SelectField(
                name="x",
                label="X",
                options=[SelectOption(value="a", label="A")],
                multiple=True,
                min_selected=-1,
            )

    def test_text_invalid_regex_en(self):
        with pytest.raises(Exception, match="regex"):
            TextField(name="x", label="X", pattern="[invalid")

    def test_field_group_unique_names_en(self):
        with pytest.raises(Exception, match="unique"):
            FieldGroup(
                title="Group",
                fields=[
                    TextField(name="x", label="X1"),
                    TextField(name="x", label="X2"),
                ],
            )

    def test_form_unique_field_names_en(self):
        with pytest.raises(Exception, match="unique"):
            Form(
                name="test",
                fields=[
                    TextField(name="dup", label="Dup1"),
                    TextField(name="dup", label="Dup2"),
                ],
            )


# ---------------------------------------------------------------------------
# validate_form_data specific messages
# ---------------------------------------------------------------------------

class TestValidateFormDataMessages:
    def test_select_invalid_category(self):
        form = Form(
            name="test",
            fields=[
                SelectField(
                    name="cat",
                    label="Category",
                    options=[
                        SelectOption(value="a", label="A"),
                        SelectOption(value="b", label="B"),
                    ],
                )
            ],
        )
        result = validate_form_data(form, {"cat": "z"})
        assert result["success"] is False
        assert "inv" in result["errors"][0]["message"].lower()

    def test_select_multiple_invalid_values(self):
        form = Form(
            name="test",
            fields=[
                SelectField(
                    name="tags",
                    label="Tags",
                    options=[
                        SelectOption(value="a", label="A"),
                        SelectOption(value="b", label="B"),
                    ],
                    multiple=True,
                )
            ],
        )
        result = validate_form_data(form, {"tags": ["a", "z"]})
        assert result["success"] is False
        assert "inv" in result["errors"][0]["message"].lower()

    def test_select_value_must_be_list(self):
        form = Form(
            name="test",
            fields=[
                SelectField(
                    name="tags",
                    label="Tags",
                    options=[SelectOption(value="a", label="A")],
                    multiple=True,
                )
            ],
        )
        result = validate_form_data(form, {"tags": 123})
        assert result["success"] is False
        assert "list" in result["errors"][0]["message"].lower()

    def test_radio_invalid(self):
        form = Form(
            name="test",
            fields=[
                RadioField(
                    name="r",
                    label="R",
                    options=[SelectOption(value="a", label="A")],
                )
            ],
        )
        result = validate_form_data(form, {"r": "z"})
        assert result["success"] is False
        assert "inv" in result["errors"][0]["message"].lower()

    def test_number_min_value(self):
        form = Form(
            name="test",
            fields=[NumberField(name="n", label="N", min_value=10)],
        )
        result = validate_form_data(form, {"n": 5})
        assert result["success"] is False
        assert "greater than or equal to 10" in result["errors"][0]["message"]

    def test_text_minlength(self):
        form = Form(
            name="test",
            fields=[TextField(name="t", label="T", minlength=5)],
        )
        result = validate_form_data(form, {"t": "ab"})
        assert result["success"] is False
        assert "5" in result["errors"][0]["message"]

    def test_email_invalid(self):
        form = Form(
            name="test",
            fields=[EmailField(name="e", label="E", required=True)],
        )
        result = validate_form_data(form, {"e": "bad"})
        assert result["success"] is False
        assert "mail" in result["errors"][0]["message"].lower()
