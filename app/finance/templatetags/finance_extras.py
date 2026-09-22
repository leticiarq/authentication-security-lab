from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def brl(value):
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        number = Decimal("0")
    rendered = f"{number:,.2f}"
    return rendered.replace(",", "_").replace(".", ",").replace("_", ".")
