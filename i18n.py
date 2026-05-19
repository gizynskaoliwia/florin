# i18n.py — Internationalization string system
# All UI labels routed through t() for future language switching.

_LANG = "en"

_STRINGS = {
    "en": {
        "nav.dashboard": "Dashboard",
        "nav.income": "Income",
        "nav.expenses": "Expenses",
        "nav.savings": "Savings",
        "nav.cashflow": "Cash Flow",
        "nav.history": "History",
        "nav.settings": "Settings",
        "nav.help": "Help",
        "help.title": "Help",
        "help.search_placeholder": "Search help...",
        "help.no_results": "No matching sections found.",
    },
}

def set_language(lang: str):
    global _LANG
    _LANG = lang

def t(key: str) -> str:
    """Get translated string for key. Falls back to English, then key itself."""
    return _STRINGS.get(_LANG, _STRINGS["en"]).get(key, _STRINGS["en"].get(key, key))
