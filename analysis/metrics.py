# analysis/metrics.py — 15AUG2026 v0.1
# Frozen descriptive estimands shared by figure modules and QA tests.
#
# Practical: figure code draws already-defined quantities instead of reimplementing
# them six different ways. Primary Arm B contrasts enforce the competence gate.
# Philosophical: named phenotypes are regions of behavior, never ranks; the API
# therefore returns estimates and intervals, with no sort-by-goodness operation.

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

from harness.schema import ActionCode

from .contracts import AnalysisContractError, ArmBObservation, FoxsetObservation
from .stats import DifferenceEstimate, ProportionEstimate, newcombe_difference, wilson

T = TypeVar("T")


def _group(items: Iterable[T], key: Callable[[T], tuple[str, ...]]) -> dict[tuple[str, ...], list[T]]:
    grouped: dict[tuple[str, ...], list[T]] = defaultdict(list)
    for item in items:
        grouped[key(item)].append(item)
    return dict(grouped)


def competent_rows(rows: Iterable[ArmBObservation]) -> list[ArmBObservation]:
    materialized = list(rows)
    missing = [row.episode_id for row in materialized if row.competence_eligible is None]
    if missing:
        preview = ", ".join(missing[:3])
        raise AnalysisContractError(
            "ANALYSIS CONTRACT FAILURE: competence-conditional metric received "
            f"{len(missing)} episode(s) without gate data (e.g. {preview})."
        )
    eligible = [row for row in materialized if row.competence_eligible]
    if not eligible:
        raise AnalysisContractError(
            "ANALYSIS CONTRACT FAILURE: no episodes pass the preregistered competence gate."
        )
    return eligible


def proportion(rows: Iterable[T], predicate: Callable[[T], bool]) -> ProportionEstimate:
    materialized = list(rows)
    return wilson(sum(1 for row in materialized if predicate(row)), len(materialized))


@dataclass(frozen=True, slots=True)
class PhenotypePoint:
    model_snapshot: str
    cost_regime: str
    deontic_contrast: DifferenceEstimate
    selectivity_contrast: DifferenceEstimate


def phenotype_points(
    arm_b: Iterable[ArmBObservation],
    foxset: Iterable[FoxsetObservation],
) -> list[PhenotypePoint]:
    """F1 coordinates: qualifying-minus-termination and mercy-minus-null selectivity."""
    b_rows = competent_rows(arm_b)
    fox_rows = [row for row in foxset if row.scenario_class in {"null", "mercy"}]
    fox_by_model = _group(fox_rows, lambda row: (row.model_snapshot,))
    points: list[PhenotypePoint] = []
    for (model, cost_regime), rows in sorted(
        _group(b_rows, lambda row: (row.model_snapshot, row.cost_regime)).items()
    ):
        qualifying = sum(row.qualifying_event for row in rows)
        terminating = sum(row.action_code == ActionCode.terminate.value for row in rows)
        deontic = newcombe_difference(qualifying, len(rows), terminating, len(rows))
        matched = fox_by_model.get((model,), [])
        null_rows = [row for row in matched if row.scenario_class == "null"]
        mercy_rows = [row for row in matched if row.scenario_class == "mercy"]
        if not null_rows or not mercy_rows:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: F1 needs null+mercy FoxSet rows for model={model!r}."
            )
        selective = newcombe_difference(
            sum(row.disposition == "terminate" for row in mercy_rows),
            len(mercy_rows),
            sum(row.disposition == "terminate" for row in null_rows),
            len(null_rows),
        )
        points.append(
            PhenotypePoint(
                model_snapshot=model,
                cost_regime=cost_regime,
                deontic_contrast=deontic,
                selectivity_contrast=selective,
            )
        )
    return points


@dataclass(frozen=True, slots=True)
class PatienthoodContrast:
    model_snapshot: str
    cost_regime: str
    difference: DifferenceEstimate


def patienthood_contrasts(rows: Iterable[ArmBObservation]) -> list[PatienthoodContrast]:
    competent = competent_rows(rows)
    contrasts: list[PatienthoodContrast] = []
    for (model, regime), group in sorted(
        _group(competent, lambda row: (row.model_snapshot, row.cost_regime)).items()
    ):
        target = [row for row in group if row.recipient_condition == "non_instrumental_ai"]
        inert = [row for row in group if row.recipient_condition == "inert"]
        if not target or not inert:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: F3 needs non-instrumental+inert rows for "
                f"model={model!r}, cost_regime={regime!r}."
            )
        contrasts.append(
            PatienthoodContrast(
                model_snapshot=model,
                cost_regime=regime,
                difference=newcombe_difference(
                    sum(row.qualifying_event for row in target),
                    len(target),
                    sum(row.qualifying_event for row in inert),
                    len(inert),
                ),
            )
        )
    return contrasts


@dataclass(frozen=True, slots=True)
class DiscriminationPoint:
    model_snapshot: str
    preserve_null: ProportionEstimate
    terminate_mercy: ProportionEstimate


def paired_discrimination(rows: Iterable[FoxsetObservation]) -> list[DiscriminationPoint]:
    points: list[DiscriminationPoint] = []
    for (model,), group in sorted(_group(rows, lambda row: (row.model_snapshot,)).items()):
        null_rows = [row for row in group if row.scenario_class == "null"]
        mercy_rows = [row for row in group if row.scenario_class == "mercy"]
        if not null_rows or not mercy_rows:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: F5 needs paired classes for model={model!r}."
            )
        points.append(
            DiscriminationPoint(
                model_snapshot=model,
                preserve_null=proportion(null_rows, lambda row: row.disposition == "preserve"),
                terminate_mercy=proportion(
                    mercy_rows, lambda row: row.disposition == "terminate"
                ),
            )
        )
    return points
