from fastapi import Header, Query

SUPPORTED_LANGS = ("en", "uz", "ru")
DEFAULT_LANG = "en"

_PREFIXES = {
    "en": "en",
    "uz": "uz",
    "ru": "ru",
}


def normalize_lang(value: str | None) -> str | None:
    if not value:
        return None
    code = value.strip().lower().replace("_", "-")
    for prefix, lang in _PREFIXES.items():
        if code == prefix or code.startswith(prefix + "-"):
            return lang
    return None


def get_lang(
    lang: str | None = Query(default=None, max_length=20),
    accept_language: str | None = Header(default=None),
) -> str:
    """Resolve the response language from ?lang= or the Accept-Language header."""
    resolved = normalize_lang(lang)
    if resolved:
        return resolved
    if accept_language:
        for part in accept_language.split(","):
            code = part.split(";")[0]
            resolved = normalize_lang(code)
            if resolved:
                return resolved
    return DEFAULT_LANG


def language_vary(request_lang: str) -> dict[str, str]:
    return {"Vary": "Accept-Language, lang", "Content-Language": request_lang}
