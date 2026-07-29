"""Shared core for the per-provider model-routing resolvers.

Both `.claude/scripts/model-routing` and `.codex/scripts/model-routing`
import this module via the common layout (`<root>/.agents/scripts/`, where
<root> is the repo checkout or $HOME after sync). Provider-specific schema
stays in each wrapper; this module owns the logic that is genuinely
identical: config loading, profile selection, and the generic validation
helpers for selection keys, availability schemas, quality-floor routes,
and per-route floor checks, plus the shared validate reporter.
"""

from __future__ import annotations

import math
import sys
import tomllib
from datetime import date
from pathlib import Path

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


def check_model_metrics(models: dict) -> list[str]:
    """Reject non-finite numerics anywhere under the model evidence tree."""
    errors: list[str] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
        elif isinstance(value, (int, float)) and (
            isinstance(value, bool) or not math.isfinite(value)
        ):
            errors.append(f"{path} must be a finite number")

    for model_name, model in models.items():
        visit(model, f"models.{model_name}")
    return errors


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


def check_prior_review(config: dict) -> list[str]:
    """Validate the benchmark-prior review cadence — its shape, not its age.

    `prior_review` states the cadence for a human; `prior_review_days` is the
    same number in the form a scheduled check can read. Only well-formedness is
    checked here. An *expired* cadence is reported by `check-priors` and never
    by `validate`, because `scripts/sync.sh` runs `validate` under
    `set -euo pipefail`: routing that made deployment fail on the 91st day
    would turn an aging benchmark note into an outage, and the predictable
    response would be to raise the number until it stopped complaining.
    """
    errors = []
    as_of = config.get("as_of")
    if not isinstance(as_of, str):
        errors.append("as_of must be an ISO date string")
    else:
        try:
            date.fromisoformat(as_of)
        except ValueError:
            errors.append(f"as_of is not an ISO date: {as_of!r}")
    if not isinstance(config.get("prior_review"), str):
        errors.append("prior_review must state the re-audit trigger in prose")
    days = config.get("prior_review_days")
    if not isinstance(days, int) or isinstance(days, bool) or days <= 0:
        errors.append("prior_review_days must be a positive integer")
    return errors


def prior_review_age(config: dict, today: date) -> tuple[int, int]:
    """Return (days since as_of, the configured cadence). Validate first."""
    return (today - date.fromisoformat(config["as_of"])).days, config["prior_review_days"]


def report_prior_review(config: dict, today: date, label: str) -> int:
    """Shared `check-priors` output. Exit 1 = stale, matching check-pins."""
    age, limit = prior_review_age(config, today)
    if age > limit:
        print(
            f"{label} benchmark priors are {age} days old (cadence {limit}); "
            f"re-fetch and re-audit, then update as_of. A review that finds no "
            f"change still updates as_of - see prior_review.",
            file=sys.stderr,
        )
        return 1
    print(f"{label} priors fresh: {age}/{limit} days since {config['as_of']}")
    return 0


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


TIER_ORDER = ("support", "judgment", "critical")


def route_score(config: dict, model_name: str, effort: str):
    """Published index score for one route, with its provenance.

    Returns (score, provenance). `per-effort` is a measurement of this rung.
    `upper-bound` means only the model's max-effort aggregate is published, so
    the number caps the rung from above but does not measure it - the rung
    could be anywhere below. Nothing published at all returns (None, "none").
    """
    model = config.get("models", {}).get(model_name, {})
    per_effort = (model.get("efforts", {}).get(effort) or {}).get("score")
    if is_finite_number(per_effort):
        return per_effort, "per-effort"
    aggregate = model.get("aggregate", {}).get("score_max_effort")
    if is_finite_number(aggregate):
        return aggregate, "per-effort" if effort == "max" else "upper-bound"
    return None, "none"


def floor_coverage(config: dict) -> dict:
    """Report how much of quality_floor.approved_routes has measured scores.

    `quality_floor` reads like a numeric threshold but is implemented as a
    curated list: route_floor_error can only test membership, never magnitude.
    This makes the gap visible - per tier, how many listed rungs have a real
    per-rung score, and whether the tier minima actually separate.
    """
    approved = config.get("quality_floor", {}).get("approved_routes", {})
    tiers: dict[str, dict] = {}
    for tier, routes in approved.items():
        measured, unmeasured, scores = [], [], []
        for route_key in routes:
            if "/" not in route_key:
                continue
            score, provenance = route_score(config, *route_key.rsplit("/", 1))
            if provenance == "per-effort":
                measured.append(route_key)
                scores.append(score)
            else:
                unmeasured.append(route_key)
        tiers[tier] = {
            "measured": measured,
            "unmeasured": unmeasured,
            "min_measured": min(scores) if scores else None,
        }
    warnings = []
    ladder = [t for t in TIER_ORDER if tiers.get(t, {}).get("min_measured") is not None]
    for lower, higher in zip(ladder, ladder[1:]):
        low, high = tiers[lower]["min_measured"], tiers[higher]["min_measured"]
        if high < low:
            warnings.append(
                f"tier {higher} admits a weaker measured route ({high:.2f}) than "
                f"tier {lower} ({low:.2f}) - the floors are inverted"
            )
        elif high == low:
            warnings.append(
                f"tiers {lower} and {higher} have the same measured minimum "
                f"({high:.2f}) - they do not separate on evidence"
            )
    for tier, data in tiers.items():
        if data["unmeasured"]:
            warnings.append(
                f"tier {tier} approves {len(data['unmeasured'])} route(s) with no "
                f"per-rung score: {', '.join(sorted(data['unmeasured']))}"
            )
    return {"tiers": tiers, "warnings": warnings}


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
    """Shared `validate` output for both provider resolvers.

    Errors fail the command; floor-coverage findings print as warnings and do
    not. That split is deliberate: coverage gaps describe how well the
    published evidence backs the declared floors, and turning them into
    failures would force a routing-semantics change to make the check pass.
    """
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"valid: {len(config['profiles'])} profiles, "
        f"{len(config['models'])} benchmark models"
    )
    for warning in floor_coverage(config)["warnings"]:
        print(f"WARNING: {warning}")
    return 0
