from enum import Enum
from codeforms.forms import Form
from codeforms.fields import FormFieldBase
from codeforms.i18n import t


class ExportFormat(Enum):
    HTML = 'html'
    BOOTSTRAP4 = 'html_bootstrap4'
    BOOTSTRAP5 = 'html_bootstrap5'


def generate_validation_code(form, output_format: str) -> str:
    """Genera el código de validación en Javascript"""
    if output_format == 'html':
        validation_code = f"""
        <script>
        function validate_{form.name}(form) {{
            let errors = [];
            let validated_data = {{}};

            {js_generate_field_validations(form)}

            if (errors.length > 0) {{
                alert('{t("export.fix_errors")}\\n' + errors.join('\\n'));
                return false;
            }}
            return true;
        }}

        document.getElementById('{form.name}').onsubmit = function(e) {{
            return validate_{form.name}(this);
        }};
        </script>
        """
        return validation_code
    return ""


def js_generate_field_validations(form) -> str:
    """Genera el código JavaScript para validar cada campo"""
    validations = []

    # Usar form.fields que devuelve la lista plana de todos los campos
    for field in form.fields:
        field_validation = f"""
            // Validación para {field.name}
            let {field.name} = form.elements['{field.name}'].value;
        """

        if field.required:
            field_validation += f"""
            if (!{field.name}) {{
                errors.push('{t("export.field_required", label=field.label)}');
            }}
            """

        for rule in field.validation_rules:
            if rule.type == "min":
                field_validation += f"""
                if ({field.name} && {field.name} < {rule.value}) {{
                    errors.push('{rule.message}');
                }}
                """
            elif rule.type == "max":
                field_validation += f"""
                if ({field.name} && {field.name} > {rule.value}) {{
                    errors.push('{rule.message}');
                }}
                """
            elif rule.type == "regex":
                field_validation += f"""
                if ({field.name} && !new RegExp('{rule.value}').test({field.name})) {{
                    errors.push('{rule.message}');
                }}
                """
            elif rule.type == "minlength":
                field_validation += f"""
                if ({field.name} && {field.name}.length < {rule.value}) {{
                    errors.push('{rule.message}');
                }}
                """
            elif rule.type == "maxlength":
                field_validation += f"""
                if ({field.name} && {field.name}.length > {rule.value}) {{
                    errors.push('{rule.message}');
                }}
                """

        field_validation += f"""
            if (!errors.length) {{
                validated_data['{field.name}'] = {field.name};
            }}
        """

        validations.append(field_validation)

    return "\n".join(validations)

def field_exporter(field: FormFieldBase, output_format: str, **kwargs) -> str:
    """Exporta un campo individual al formato especificado"""
    if output_format == 'html':
        return field_to_html(field, kwargs=kwargs)
    return ""


def group_exporter(group, output_format: str, **kwargs) -> str:
    """Exporta un grupo de campos al formato especificado"""
    if output_format == 'html':
        return group_to_html(group, kwargs=kwargs)
    return ""


def group_to_html(group, **kwargs) -> str:
    """Genera la representación HTML del grupo de campos usando fieldset y legend"""
    output_format = kwargs.get('output_format', ExportFormat.HTML.value)
    is_bootstrap = output_format in [ExportFormat.BOOTSTRAP4.value, ExportFormat.BOOTSTRAP5.value]
    
    # Clases CSS para el fieldset
    fieldset_class = f"mb-4 {group.css_classes or ''}".strip() if is_bootstrap else group.css_classes or ""
    legend_class = "h5 mb-3" if is_bootstrap else ""
    
    # Atributos del fieldset
    fieldset_attrs = {
        "id": f"group_{group.id}",
        "class": fieldset_class
    }
    
    # Agregar atributos personalizados del grupo
    fieldset_attrs.update(group.attributes)
    
    # Generar string de atributos
    attrs_str = " ".join(f'{k}="{v}"' for k, v in fieldset_attrs.items() if v)
    
    # Generar HTML de los campos dentro del grupo
    fields_html = "\n".join(field_to_html(field, **kwargs) for field in group.fields)
    
    # Generar descripción si existe
    description_html = ""
    if group.description:
        desc_class = "text-muted small mb-3" if is_bootstrap else "group-description"
        description_html = f'<p class="{desc_class}">{group.description}</p>'
    
    # Construir el HTML del fieldset
    html = f'<fieldset {attrs_str}>'
    html += f'<legend class="{legend_class}">{group.title}</legend>'
    html += description_html
    html += fields_html
    html += '</fieldset>'
    
    return html

def form_to_html(form: Form, **kwargs) -> str:
    """Genera el HTML completo del formulario"""
    output_format = kwargs.get('output_format', ExportFormat.HTML.value)
    form_class = "needs-validation" if output_format in [ExportFormat.BOOTSTRAP4.value, ExportFormat.BOOTSTRAP5.value] else ""
    
    attributes = {
        "id": kwargs.get('id') or str(form.id),
        "name": form.name,
        "class": f"{form_class} {form.css_classes or ''}".strip(),
        "enctype": kwargs.get('enctype') or "application/x-www-form-urlencoded"
    }

    attrs_str = " ".join(f'{k}="{v}"' for k, v in attributes.items() if v)
    
    # Generar HTML para cada elemento del contenido (campos o grupos)
    content_html_parts = []
    for item in form.content:
        if hasattr(item, 'fields') and hasattr(item, 'title'):  # Es un FieldGroup
            content_html_parts.append(group_to_html(item, **kwargs))
        else:  # Es un campo individual
            content_html_parts.append(field_to_html(item, **kwargs))
    
    content_html = "\n".join(content_html_parts)
    
    if kwargs.get('submit'):
        submit_class = "btn btn-primary" if output_format in [ExportFormat.BOOTSTRAP4.value, ExportFormat.BOOTSTRAP5.value] else ""
        submit_html = f'<button type="submit" class="{submit_class}">{t("export.submit")}</button>'
    else:
        submit_html = ""

    html = f"<form {attrs_str}>"
    html += f"\t{content_html}"
    html += f"\t{submit_html}"
    html += f"</form>"
    return html


def field_to_html(field: FormFieldBase, **kwargs) -> str:
    """Genera la representación HTML del campo"""
    output_format = kwargs.get('output_format', ExportFormat.HTML.value)
    is_bootstrap = output_format in [ExportFormat.BOOTSTRAP4.value, ExportFormat.BOOTSTRAP5.value]
    
    # Clases base para Bootstrap 4/5
    if is_bootstrap:
        base_input_class = "form-control"
        form_group_class = "mb-3" if output_format == ExportFormat.BOOTSTRAP5.value else "form-group"
        help_text_class = "form-text"  # Bootstrap 5 removed text-muted
    else:
        base_input_class = ""
        form_group_class = "form-field"
        help_text_class = "help-text"

    skip_label = ['hidden']
    
    label_html = ''
    if field.field_type_value not in skip_label:
        label_class = "form-label" if is_bootstrap else ""
        label_html = f'<label class="{label_class}" for="{field.id}">{field.label}</label>'
    
    help_html = f'<small class="{help_text_class}">{field.help_text}</small>' if field.help_text else ""

    # Manejar campos SELECT de manera especial
    if field.field_type_value == 'select':
        select_attrs = {
            "id": str(field.id),
            "name": field.name,
            "class": f"{base_input_class} {field.css_classes or ''}".strip(),
        }
        
        if field.required:
            select_attrs["required"] = "required"
            
        if hasattr(field, 'multiple') and field.multiple:
            select_attrs["multiple"] = "multiple"
            
        # Agregar atributos personalizados
        select_attrs.update(field.attributes)
        
        attrs_str = " ".join(f'{k}="{v}"' for k, v in select_attrs.items() if v)
        
        # Generar opciones
        options_html = ""
        if hasattr(field, 'options'):
            for option in field.options:
                selected = 'selected="selected"' if option.selected else ""
                options_html += f'<option value="{option.value}" {selected}>{option.label}</option>'
        
        input_html = f'<select {attrs_str}>{options_html}</select>'
    
    # Manejar campos RADIO de manera especial
    elif field.field_type_value == 'radio':
        radio_html_parts = []
        if hasattr(field, 'options'):
            for option in field.options:
                radio_attrs = {
                    "id": f"{field.id}_{option.value}",
                    "name": field.name,
                    "type": "radio",
                    "value": option.value,
                    "class": field.css_classes or ""
                }
                
                if option.selected:
                    radio_attrs["checked"] = "checked"
                    
                if field.required:
                    radio_attrs["required"] = "required"
                
                attrs_str = " ".join(f'{k}="{v}"' for k, v in radio_attrs.items() if v)
                radio_label = f'<label for="{field.id}_{option.value}">{option.label}</label>'
                radio_html_parts.append(f'<input {attrs_str}>{radio_label}')
        
        input_html = '<div class="radio-group">' + ''.join(radio_html_parts) + '</div>'
    
    # Manejar campos CHECKBOX con opciones múltiples
    elif field.field_type_value == 'checkbox' and hasattr(field, 'options'):
        checkbox_html_parts = []
        for option in field.options:
            checkbox_attrs = {
                "id": f"{field.id}_{option.value}",
                "name": field.name,
                "type": "checkbox",
                "value": option.value,
                "class": field.css_classes or ""
            }
            
            if option.selected:
                checkbox_attrs["checked"] = "checked"
                
            if field.required:
                checkbox_attrs["required"] = "required"
            
            attrs_str = " ".join(f'{k}="{v}"' for k, v in checkbox_attrs.items() if v)
            checkbox_label = f'<label for="{field.id}_{option.value}">{option.label}</label>'
            checkbox_html_parts.append(f'<input {attrs_str}>{checkbox_label}')
        
        input_html = '<div class="checkbox-group">' + ''.join(checkbox_html_parts) + '</div>'
    
    # Manejar campos normales (input)
    else:
        attributes = {
            "id": str(field.id),
            "name": field.name,
            "type": field.field_type_value,
            "class": f"{base_input_class} {field.css_classes or ''}".strip(),
            "placeholder": field.placeholder or "",
        }
        
        if hasattr(field, 'value'):
            attributes["value"] = getattr(field, 'value')

        if field.required:
            attributes["required"] = "required"

        if field.default_value is not None:
            attributes["value"] = str(field.default_value)
            
        # Para checkbox simple, manejar el atributo checked
        if field.field_type_value == 'checkbox' and hasattr(field, 'checked') and field.checked:
            attributes["checked"] = "checked"

        # Agregar atributos personalizados
        attributes.update(field.attributes)

        # Convertir atributos a string
        attrs_str = " ".join(f'{k}="{v}"' for k, v in attributes.items() if v)
        input_html = f'<input {attrs_str}>'

    return f"""<div class="{form_group_class}">{label_html}{input_html}{help_html}</div>"""

def exporter(form: Form, output_format: str, **kwargs) -> dict:
    export_result = {'format': output_format}
    if output_format in [format.value for format in ExportFormat]:
        actual_kwargs = kwargs.get('kwargs', kwargs)
        actual_kwargs['output_format'] = output_format
        export_result['output'] = form_to_html(form, **actual_kwargs)
        export_result['javascript_validation_code'] = generate_validation_code(form, output_format)

    return export_result