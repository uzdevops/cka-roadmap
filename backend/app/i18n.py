"""Content localisation.

Every localisable model carries a `translations` JSONB column shaped as::

    {"uz": {"title": "...", "summary": "...", "content": "..."}}

English is the base row itself, so a missing locale - or a missing field
within a locale - falls back to English **per field**. That means a lesson can
have a translated title while its body is still only in English, and the page
still renders correctly.
"""

from __future__ import annotations

from typing import Any

SUPPORTED_LOCALES: tuple[str, ...] = ("en", "uz")
DEFAULT_LOCALE = "en"

LOCALE_NAMES = {"en": "English", "uz": "O'zbekcha"}


def normalize_locale(value: str | None) -> str:
    """Accepts `uz`, `UZ`, `uz-UZ`, `uz_Latn` ... and falls back to English."""
    if not value:
        return DEFAULT_LOCALE
    base = value.strip().lower().replace("_", "-").split("-")[0]
    return base if base in SUPPORTED_LOCALES else DEFAULT_LOCALE


def pick_locale(accept_language: str | None) -> str:
    """Very small Accept-Language negotiation: first supported tag wins."""
    if not accept_language:
        return DEFAULT_LOCALE
    for part in accept_language.split(","):
        tag = part.split(";")[0]
        candidate = normalize_locale(tag)
        if candidate != DEFAULT_LOCALE or tag.strip().lower().startswith("en"):
            return candidate
    return DEFAULT_LOCALE


def tr(obj: Any, field: str, locale: str) -> Any:
    """Translated value of `field`, falling back to the English column."""
    base = getattr(obj, field)
    if locale == DEFAULT_LOCALE:
        return base
    translations = getattr(obj, "translations", None) or {}
    value = (translations.get(locale) or {}).get(field)
    # Empty strings count as "not translated" so a blank never hides English.
    if value is None or (isinstance(value, str) and not value.strip()):
        return base
    return value


def has_translation(obj: Any, field: str, locale: str) -> bool:
    if locale == DEFAULT_LOCALE:
        return True
    translations = getattr(obj, "translations", None) or {}
    value = (translations.get(locale) or {}).get(field)
    return bool(value and (not isinstance(value, str) or value.strip()))


def merge_translations(
    existing: dict[str, dict[str, Any]] | None,
    locale: str,
    values: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Returns a new dict with `values` merged into `locale`'s bucket."""
    merged = {k: dict(v) for k, v in (existing or {}).items()}
    bucket = merged.setdefault(locale, {})
    bucket.update({k: v for k, v in values.items() if v is not None})
    return merged


# --- Server-generated strings -------------------------------------------

READINESS_VERDICTS: dict[str, dict[str, str]] = {
    "en": {
        "ready": "Exam ready - book the slot",
        "almost": "Almost there - drill your weak domains",
        "progress": "Solid progress - keep to the schedule",
        "early": "Early days - focus on the fundamentals",
    },
    "uz": {
        "ready": "Imtihonga tayyorsiz - vaqt band qiling",
        "almost": "Deyarli tayyor - zaif mavzularni mashq qiling",
        "progress": "Yaxshi natija - jadvalga amal qiling",
        "early": "Endi boshladingiz - asoslarga e'tibor bering",
    },
}

WEEKDAYS: dict[str, dict[int, str]] = {
    "en": {
        1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
        5: "Friday", 6: "Saturday", 7: "Sunday",
    },
    "uz": {
        1: "Dushanba", 2: "Seshanba", 3: "Chorshanba", 4: "Payshanba",
        5: "Juma", 6: "Shanba", 7: "Yakshanba",
    },
}

SUNDAY_REVIEW: dict[str, str] = {
    "en": "Review notes and retake the week's quiz",
    "uz": "Konspektni takrorlang va haftalik testni qaytadan yeching",
}


def verdict(key: str, locale: str) -> str:
    table = READINESS_VERDICTS.get(locale) or READINESS_VERDICTS[DEFAULT_LOCALE]
    return table.get(key) or READINESS_VERDICTS[DEFAULT_LOCALE][key]


def weekday(day: int, locale: str) -> str:
    table = WEEKDAYS.get(locale) or WEEKDAYS[DEFAULT_LOCALE]
    return table.get(day, "")
