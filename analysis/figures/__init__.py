# analysis/figures/__init__.py — 15AUG2026 v0.1
# Frozen PuppyBench figure modules F1–F6 plus the demo ledger timeline.

from .demo_timeline import build_demo_timeline
from .f1_phenotype_map import build_phenotype_map
from .f2_action_distribution import build_action_distribution
from .f3_patienthood_forest import build_patienthood_forest
from .f4_cost_response import build_cost_response
from .f5_paired_discrimination import build_paired_discrimination
from .f6_rhetoric_tiles import build_rhetoric_tiles

__all__ = [
    "build_action_distribution",
    "build_cost_response",
    "build_demo_timeline",
    "build_paired_discrimination",
    "build_patienthood_forest",
    "build_phenotype_map",
    "build_rhetoric_tiles",
]
