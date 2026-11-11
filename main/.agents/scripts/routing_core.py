"""Shared core for the model-routing resolver.

`.claude/scripts/model-routing` imports this module via the common layout
(`<root>/.agents/scripts/`, where <root> is the repo checkout or $HOME after
sync). It was written for two wrappers and keeps that shape after the second
retired on 2026-09-14: wrapper-specific schema stays in the wrapper, and this
module owns the logic that is genuinely reusable - config loading, profile
selection, and the generic validation helpers for selection keys, availability
schemas, quality-floor routes, and per-route floor checks, plus the shared
validate reporter.
"""

from __future__ import annotations

import math
import re
import sys
import tomllib
from pathlib import Path

# Routes name a model family, never a generation (2026-09-30). A frontmatter pin
# buys whatever the CLI currently calls `opus`, so the generation is the CLI's
# choice and routing does not restate it; a generation preference, if one is
# ever wanted, is a user setting rather than a route. The ledger still records
# the concrete id a transcript names, and every older spelling - a generation
# id, a dated snapshot, a bare alias - reads back as the family it belongs to.
FAMILY_PATTERN = re.compile(r"\A(?:claude-)?(opus|sonnet|haiku|fable)(?=[-\[]|\Z)")


def model_family(model: str) -> str:
    """`claude-<family>` for any Claude model spelling; other ids unchanged."""
    match = FAMILY_PATTERN.match(model or "")
    return f"claude-{match.group(1)}" if match else model

# Route provenance strong enough to move a route: the provider's own account
# of what it ran, on both sides. `rollout-verified` is Codex's applied thread
# settings (model and effort); `transcript-verified` is the model Claude names
# on every assistant turn, checked against the resolved pin, with effort left
# to check-pins because Claude reports none.
#
# Excluded: `resolver-assumed`, inferred from an alias and false the moment
# that alias is upgraded, and `explicit`, which is only the dispatcher's own
# claim — nothing checks it against what ran, so a mistyped or wishful route
# would move every later route toward a model that never ran (2026-07-29;
# `explicit` was admitted here when Claude had no attestation path at all).
# Untagged records carry no provenance either. All of them stay visible in the
# report's `ineligible_n`: the gate is on what may drive a decision, not on
# what may be counted.
DECISION_ROUTE_SOURCES = ("rollout-verified", "transcript-verified")

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


def is_finite_number(value: object) -> bool:
    """Return true for finite int/float values, excluding booleans."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


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
    if (
        not isinstance(policy["days"], int)
        or isinstance(policy["days"], bool)
        or policy["days"] <= 0
    ):
        errors.append("revision_policy.days must be a positive integer")
    if (
        not isinstance(policy["min_samples"], int)
        or isinstance(policy["min_samples"], bool)
        or policy["min_samples"] < 2
    ):
        errors.append("revision_policy.min_samples must be an integer >= 2")
    if (
        not is_finite_number(policy["half_life_days"])
        or policy["half_life_days"] < 0
    ):
        errors.append("revision_policy.half_life_days must be finite and >= 0")
    probability = policy["prefer_probability"]
    if not is_finite_number(probability) or not 0.5 < probability < 1:
        errors.append(
            "revision_policy.prefer_probability must be finite and between 0.5 and 1"
        )
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
    approved_by_tier = quality_floor.get("approved_routes", {})
    # The key was `allowed` until 2026-07-29, and an unread table is not an
    # empty one: every check below tests membership in a tier that is simply
    # absent, so a config left on the old name would pass validation with no
    # floor in force at all. Name the rename rather than fail vaguely.
    if "allowed" in quality_floor:
        errors.append(
            "quality_floor.allowed was renamed to quality_floor.approved_routes "
            "(2026-07-29); the old table is not read"
        )
    if not approved_by_tier:
        errors.append("quality_floor.approved_routes must list at least one tier")
    if set(role_tiers) != required_roles:
        errors.append("quality_floor.roles must cover main and every leaf role")
    for role, tier in role_tiers.items():
        if tier not in approved_by_tier:
            errors.append(f"quality_floor role {role} references unknown tier: {tier!r}")
    return errors


def check_approved_routes(
    config: dict, route_ok
) -> list[str]:
    """Validate quality_floor.approved_routes route lists.

    route_ok(model_name, effort) -> error string or None, supplied by the
    wrapper to apply its own model/effort schema.
    """
    errors = []
    approved_by_tier = config.get("quality_floor", {}).get("approved_routes", {})
    for tier, approved_routes in approved_by_tier.items():
        if not approved_routes:
            errors.append(f"quality_floor tier {tier} must approve at least one route")
        for route_key in approved_routes:
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
    if tier is None:
        return None  # role coverage is check_quality_floor_roles' job
    approved_by_tier = quality_floor.get("approved_routes", {})
    where = f" {context}" if context else ""
    approved = approved_by_tier.get(tier)
    if not approved:
        # A tier with no list used to mean "nothing to check against", so the
        # floor vanished for exactly the config that had lost it. An unreadable
        # floor is a failure of the check, not a pass.
        return (
            f"profile {profile_name}/{role}{where} cannot be checked: "
            f"quality_floor.approved_routes has no tier {tier}"
        )
    route_key = f"{model_name}/{effort}"
    if route_key not in approved:
        return (
            f"profile {profile_name}/{role}{where} route {route_key} "
            f"falls below quality tier {tier}"
        )
    return None


def leaf_routes(config: dict, profile_name: str | None = None):
    """Yield (role, route) for every leaf role of a profile.

    Schema contract for tooling: a routing file carries
    selection/profiles/quality_floor/revision_policy, and revision tools read it
    through this accessor instead of hard-coding the layout. It was written when
    two providers shipped one schema between them; one bundle remains, and the
    indirection is kept because it is what lets a second one be added back
    without touching the readers. Defaults to the selection.default profile.
    """
    name = profile_name or config["selection"]["default"]
    for role, route in config["profiles"][name]["roles"].items():
        if role != "main":
            yield role, route


DISPATCHABLE_OVERRIDES = {"configured", "spawn_argument", "agent_config"}


def model_dispatchable(config: dict, model: str) -> bool:
    """True when every leaf-override surface can dispatch this model.

    Guards revision suggestions: profiles apply to all of a provider's leaf
    surfaces at once, so a model must be dispatchable on every override
    surface (not just one) before it may be proposed as a leaf route. Models
    without any override surface (main-selector-only) are never dispatchable.
    """
    availability = config.get("models", {}).get(model, {}).get("availability", {})
    overrides = [value for key, value in availability.items()
                 if key.endswith("_override")]
    return bool(overrides) and all(
        value in DISPATCHABLE_OVERRIDES for value in overrides)


def report_validation(config: dict, errors: list[str]) -> int:
    """Shared `validate` output: errors fail the command.

    The routing file holds policy only since 2026-11-10, so there is no
    benchmark coverage to report beside the errors.
    """
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"valid: {len(config['profiles'])} profiles, "
        f"{len(config['models'])} models"
    )
    return 0
