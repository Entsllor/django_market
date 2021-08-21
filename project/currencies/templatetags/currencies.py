import logging

from django import template
from django.conf import settings

from currencies.services import get_currency_by_language, _exchange, _get_exchange_rate

register = template.Library()

logger = logging.getLogger('console')


@register.filter
def to_local_currency(amount):
    logger.error("filter <to_locale_currency> doesn't work")
    return f'{amount}{settings.CURRENCIES_SYMBOLS[settings.DEFAULT_CURRENCY]}'


@register.simple_tag
def get_currency_l10n_filter(language):
    currency = get_currency_by_language(language)
    rate = _get_exchange_rate(currency.code)

    @register.filter
    def to_local_currency(amount):
        exchanged_amount = _exchange(amount, rate)
        return f'{exchanged_amount}{currency.sym}'

    return to_local_currency
