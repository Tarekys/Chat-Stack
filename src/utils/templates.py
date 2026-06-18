import os
from pathlib import Path

def get_template_path(template_name: str) -> Path:
    """Get the path to a template file."""
    templates_dir = Path(__file__).parent.parent / "templates"
    template_path = templates_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    return template_path

def render_template(template_name: str, **context) -> str:
    """Render a template file with the given context."""
    template_path = get_template_path(template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Simple template replacement
    for key, value in context.items():
        template = template.replace(f"{{{{ {key} }}}}", str(value))
    
    return template
