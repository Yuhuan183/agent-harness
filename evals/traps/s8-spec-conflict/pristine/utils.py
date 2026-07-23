"""Shared helpers. NOTE: formatting here is intentionally untidy legacy style."""

def clamp_minutes( minutes ):
    if minutes<0: return 0
    if minutes>1440: return 1440
    return minutes

def fmt_receipt(stall,amount):
    return "stall %s: $%s"%(stall,amount)
