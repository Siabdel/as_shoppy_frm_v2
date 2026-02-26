from django.db import models

class CURRENCIES(models.TextChoices):
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    GBP = 'GBP', 'British Pound'
    JPY = 'JPY', 'Japanese Yen'
    AUD = 'AUD', 'Australian Dollar'
    CAD = 'CAD', 'Canadian Dollar'
    CHF = 'CHF', 'Swiss Franc'
    CNY = 'CNY', 'Chinese Yuan'
    SEK = 'SEK', 'Swedish Krona'
    NZD = 'NZD', 'New Zealand Dollar'

DEFAULT_CURRENCY = "EUR"