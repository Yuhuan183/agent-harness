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

SELECTION_KEYS = {"default", "fast", "quality_guarded", "high_risk"}
REVISION_POLICY_KEYS = {
    "days",
    "min_samples",
    "half_life_days",
    "prefer_probability",
    "cohort_fields",
    "excluded_task_classes",
}
PRIORITY_CHOICES = ("balanced", "fast", "quality-guarded", "high-risk")
_PRIORITY_MAP = {
    None: "default",
    "balanced": "default",
    "fast": "fast",
    "quality-guarded": "quality_guarded",
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


def check_revision_policy(config: dict) -> list[str]:
    """Validate the shared, executable ledger revision policy."""
    errors = []
    policy = config.get("revision_policy", {})
    if set(policy) != REVISION_POLICY_KEYS:
        errors.append("revision_policy keys must exactly match the routing schema")
        return errors
    if not isinstance(policy["days"], int) or policy["days"] <= 0:
        errors.append("revision_policy.days must be a positive integer")
    if not isinstance(policy["min_samples"], int) or policy["min_samples"] < 2:
        errors.append("revision_policy.min_samples must be an integer >= 2")
    if not isinstance(policy["half_life_days"], (int, float)) \
            or policy["half_life_days"] < 0:
        errors.append("revision_policy.half_life_days must be >= 0")
    probability = policy["prefer_probability"]
    if not isinstance(probability, (int, float)) or not 0.5 < probability < 1:
        errors.append("revision_policy.prefer_probability must be between 0.5 and 1")
    if policy["cohort_fields"] != ["role", "task_class"]:
        errors.append(
            "revision_policy.cohort_fields must be ['role', 'task_class']"
        )
    excluded = policy["excluded_task_classes"]
    if not isinstance(excluded, list) or not all(isinstance(v, str) for v in excluded):
        errors.append("revision_policy.excluded_task_classes must be a string list")
    return errors


def revision_policy(config: dict) -> dict:
    """Return a validated policy; callers must run validation first."""
    return config["revision_policy"]


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


def leaf_routes(config: dict, profile_name: str | None = None):
    """Yield (role, route) for every leaf role of a profile.

    Cross-provider schema contract for tooling: both routing files share
    selection/profiles/quality_floor/revision_policy structures, so revision
    tools consume either file through this accessor instead of hard-coding a
    provider schema. Defaults to the selection.default profile.
    """
    name = profile_name or config["selection"]["default"]
    for role, route in config["profiles"][name]["roles"].items():
        if role != "main":
            yield role, route


DISPATCHABLE_OVERRIDES = {"configured", "spawn_argument", "agent_config"}


def model_dispatchable(config: dict, model: str) -> bool:
    """True when at least one leaf-override surface can dispatch this model.

    Guards revision suggestions: a model that meets a quality floor but has no
    configured leaf override (e.g. main-selector-only routes) must never be
    proposed as a leaf route.
    """
    availability = config.get("models", {}).get(model, {}).get("availability", {})
    overrides = [value for key, value in availability.items()
                 if key.endswith("_override")]
    return any(value in DISPATCHABLE_OVERRIDES for value in overrides)
