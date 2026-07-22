"""Shared core for the per-provider model-routing resolvers.

Both `.claude/scripts/model-routing` and `.codex/scripts/model-routing`
import this module via the common layout (`<root>/.agents/scripts/`, where
<root> is the repo checkout or $HOME after sync). Provider-specific schema
stays in each wrapper; this module owns the logic that is genuinely
identical: config loading, profile selection, and the generic validation
helpers for selection keys, availability schemas, quality-floor routes,
and per-route floor checks.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

SELECTION_KEYS = {"default", "fast", "quality_guarded", "economy", "high_risk"}
PRIORITY_CHOICES = ("balanced", "fast", "quality-guarded", "economy", "high-risk")
_PRIORITY_MAP = {
    None: "default",
    "balanced": "default",
    "fast": "fast",
    "quality-guarded": "quality_guarded",
    "economy": "economy",
    "high-risk": "high_risk",
}


def load_config(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def resolve_profile(config: dict, profile: str | None, priority: str | None) -> str:
    if profile:
        return profile
    return config["selection"][_PRIORITY_MAP[priority]]


def check_selection(config: dict) -> list[str]:
    errors = []
    selection = config.get("selection", {})
    profiles = config.get("profiles", {})
    if set(selection) != SELECTION_KEYS:
        errors.append("selection keys must exactly match the routing schema")
    for key, profile in selection.items():
        if profile not in profiles:
            errors.append(f"selection.{key} references unknown profile: {profile!r}")
    return errors


def check_availability(models: dict, schema: dict[str, set]) -> list[str]:
    errors = []
    for model_name, model in models.items():
        availability = model.get("availability", {})
        if set(availability) != set(schema):
            errors.append(f"model {model_name} availability must cover every surface")
        for surface, valid_states in schema.items():
            if availability.get(surface) not in valid_states:
                errors.append(
                    f"model {model_name} has invalid {surface} availability: "
                    f"{availability.get(surface)!r}"
                )
    return errors


def check_quality_floor_roles(
    config: dict, required_roles: set[str]
) -> list[str]:
    errors = []
    quality_floor = config.get("quality_floor", {})
    role_tiers = quality_floor.get("roles", {})
    allowed_by_tier = quality_floor.get("allowed", {})
    if set(role_tiers) != required_roles:
        errors.append("quality_floor.roles must cover main and every leaf role")
    for role, tier in role_tiers.items():
        if tier not in allowed_by_tier:
            errors.append(f"quality_floor role {role} references unknown tier: {tier!r}")
    return errors


def check_allowed_routes(
    config: dict, route_ok
) -> list[str]:
    """Validate quality_floor.allowed route lists.

    route_ok(model_name, effort) -> error string or None, supplied by the
    wrapper to apply its own model/effort schema.
    """
    errors = []
    allowed_by_tier = config.get("quality_floor", {}).get("allowed", {})
    for tier, allowed_routes in allowed_by_tier.items():
        if not allowed_routes:
            errors.append(f"quality_floor tier {tier} must allow at least one route")
        for route_key in allowed_routes:
            if "/" not in route_key:
                errors.append(
                    f"quality_floor tier {tier} has malformed route: {route_key!r}"
                )
                continue
            model_name, effort = route_key.rsplit("/", 1)
            problem = route_ok(model_name, effort)
            if problem:
                errors.append(f"quality_floor tier {tier} {problem}")
    return errors


def route_floor_error(
    config: dict, profile_name: str, role: str, model_name: str, effort: str,
    context: str = "",
) -> str | None:
    """Return an error when a chosen route falls below the role's tier."""
    quality_floor = config.get("quality_floor", {})
    tier = quality_floor.get("roles", {}).get(role)
    allowed_by_tier = quality_floor.get("allowed", {})
    route_key = f"{model_name}/{effort}"
    if tier in allowed_by_tier and route_key not in allowed_by_tier[tier]:
        where = f" {context}" if context else ""
        return (
            f"profile {profile_name}/{role}{where} route {route_key} "
            f"falls below quality tier {tier}"
        )
    return None
