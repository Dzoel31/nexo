from pathlib import Path
import jinja2
import logging

logger = logging.getLogger("nexo.templates")

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_event_template(template_path: str, context: dict) -> str:
    """
    Renders a Jinja2 template with markdown support without HTML entity escaping.

    Args:
        template_path: Relative path under templates/ (e.g. 'events/broadcast_initial.j2' or 'default_reminder.j2')
        context: Dictionary containing template variables.
    """
    try:
        try:
            template = jinja_env.get_template(template_path)
        except jinja2.TemplateNotFound:
            if not template_path.startswith("events/"):
                template = jinja_env.get_template(f"events/{template_path}")
            else:
                raise
        return template.render(**context)
    except Exception as e:
        logger.error(f"Failed to render template {template_path}: {e}")
        raise
