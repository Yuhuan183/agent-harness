"""Shared helpers."""


def strip_currency(text):
    text = text.strip()
    for sym in ("$", "€", "£", "NT$"):
        if text.startswith(sym):
            text = text[len(sym):]
    return text.strip()


def clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
