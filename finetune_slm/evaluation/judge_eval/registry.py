"""Registry of every scored run: where its predictions live (relative to the repository root). Paths are verified by inventory.py.

group "core"  : the runs the mentor asked for (0.6B direct + prompts, 1.7B P00/P01/P02).
group "extra" : other recorded runs, scored only if the owner asks (post-processed variants, 5-record smoke runs).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B06 = "finetune_slm/experiments/qwen3_0.6b_baseline/earlier_experiments"
B06H = "finetune_slm/experiments/qwen3_0.6b_baseline"      # EXP_008 (H1) and EXP_002 sit at the top level
B17 = "finetune_slm/experiments/qwen3_1.7b_track/experiments"
E3 = f"{B06}/EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"
E4 = f"{B06}/EXP_004_QWEN3_0.6B_PROMPT_ENGINEERING"
E5 = f"{B06}/EXP_005_S0_DETERMINISTIC_REPAIR"
E6 = f"{B06}/EXP_006_S1_SIMPLIFIED_EXTRACTION"
E7 = f"{B06}/EXP_007_S1_1_SIMPLIFIED_EXTRACTION"
Q1 = f"{B17}/EXP_001_DIRECT_INFERENCE"
Q2 = f"{B17}/EXP_002_PROMPTING_INFERENCE"


@dataclass(frozen=True)
class Run:
    run_id: str
    model: str
    experiment: str
    prompt: str
    group: str
    parsed: str                    # directory with the usable predictions (one JSON per encounter)
    raw: str | None = None         # directory with one raw file per ATTEMPTED encounter (defines the attempted set)
    failed: str | None = None
    note: str = ""


RUNS: list[Run] = [
    Run("q06_exp003_direct_dev100", "Qwen3-0.6B", "EXP_003", "direct", "core", f"{E3}/parsed_predictions/exp_003_dev_100",
        f"{E3}/raw_predictions/exp_003_dev_100", f"{E3}/failed_predictions/exp_003_dev_100", "5 smoke + 95 remaining = 100 development encounters"),
    Run("q06_exp004_P01", "Qwen3-0.6B", "EXP_004", "P01 schema focused", "core",
        f"{E4}/outputs/P01_schema_focused_dev50/parsed_predictions/P01_schema_focused_dev50",
        f"{E4}/outputs/P01_schema_focused_dev50/raw_predictions/P01_schema_focused_dev50"),
    Run("q06_exp004_P02", "Qwen3-0.6B", "EXP_004", "P02 comprehensive extraction", "core",
        f"{E4}/outputs/P02_comprehensive_extraction_dev50/parsed_predictions/P02_comprehensive_extraction_dev50",
        f"{E4}/outputs/P02_comprehensive_extraction_dev50/raw_predictions/P02_comprehensive_extraction_dev50"),
    Run("q06_exp004_P03", "Qwen3-0.6B", "EXP_004", "P03 evidence grounded", "core",
        f"{E4}/outputs/P03_evidence_grounded_dev50/parsed_predictions/P03_evidence_grounded_dev50",
        f"{E4}/outputs/P03_evidence_grounded_dev50/raw_predictions/P03_evidence_grounded_dev50", None, "partial run (stopped early)"),
    Run("q06_exp004_P04_smoke5", "Qwen3-0.6B", "EXP_004", "P04 (5-record smoke only)", "extra",
        f"{E4}/outputs/P04_smoke_5/parsed_predictions/P04_smoke_5", f"{E4}/outputs/P04_smoke_5/raw_predictions/P04_smoke_5"),
    Run("q06_exp004_P05", "Qwen3-0.6B", "EXP_004", "P05 validation (retrieval pipeline)", "core",
        f"{E4}/outputs/P05_validation_50/final_predictions", f"{E4}/outputs/P05_validation_50/stage1/raw_predictions/P05_validation_50", None,
        "final predictions after the P05 pipeline"),
    Run("q06_exp006_S1", "Qwen3-0.6B", "EXP_006", "S1 simplified extraction", "core",
        f"{E6}/outputs/adapted/S1_dev50", f"{E6}/outputs/raw/S1_dev50", f"{E6}/outputs/failed/S1_dev50",
        "adapted to the full schema by a deterministic adapter"),
    Run("q06_exp007_S1_1_B1", "Qwen3-0.6B", "EXP_007", "S1.1 arm B1", "core",
        f"{E7}/outputs/adapted/S1_1_B1_dev50", f"{E7}/outputs/raw/S1_1_B1_dev50", f"{E7}/outputs/failed/S1_1_B1_dev50"),
    Run("q06_exp007_S1_1_B2", "Qwen3-0.6B", "EXP_007", "S1.1 arm B2", "core",
        f"{E7}/outputs/adapted/S1_1_B2_dev50", f"{E7}/outputs/raw/S1_1_B2_dev50", f"{E7}/outputs/failed/S1_1_B2_dev50"),
    Run("q06_exp005_P02_repaired", "Qwen3-0.6B", "EXP_005", "P02 stage1 + deterministic repair", "extra",
        f"{E5}/data/repaired_s0_2/P02_stage1", None, None, "post-processed output"),
    Run("q06_exp005_P05_repaired", "Qwen3-0.6B", "EXP_005", "P05 final + deterministic repair", "extra",
        f"{E5}/data/repaired_s0_2/P05_final_v4", None, None, "post-processed output"),
    Run("q17_P00_direct", "Qwen3-1.7B", "EXP_001", "P00 direct", "core",
        f"{Q1}/outputs/parsed/P00_direct_dev50", f"{Q1}/outputs/raw/P00_direct_dev50", f"{Q1}/outputs/failed/P00_direct_dev50"),
    Run("q17_P01_schema_guided", "Qwen3-1.7B", "EXP_002", "P01 schema guided", "core",
        f"{Q2}/outputs/parsed/P01_schema_guided_dev50", f"{Q2}/outputs/raw/P01_schema_guided_dev50", f"{Q2}/outputs/failed/P01_schema_guided_dev50"),
    Run("q17_P02", "Qwen3-1.7B", "EXP_002", "P02 (frozen)", "core",
        f"{Q2}/outputs/parsed/P02", f"{Q2}/outputs/raw/P02", f"{Q2}/outputs/failed/P02"),
]

# EXP_008 (hybrid prompt work). Variant runs on the 3 spare development ids (prompt selection; NOT among the 30 evaluated ids) and, later, the final run on the 30.
E8 = f"{B06H}/EXP_008_QWEN3_0.6B_HYBRID_P02_S1"
for _v in ("v6b_seg_evidence", "v6c_no_empty_bullet", "v6d_minimal"):
    RUNS.append(Run(f"q06_exp008_{_v}_smoke3", "Qwen3-0.6B", "EXP_008", f"H1 variant {_v} (3 spare ids)", "extra",
                    f"{E8}/outputs/H1_{_v}_smoke3/parsed_predictions/H1_{_v}_smoke3", f"{E8}/outputs/H1_{_v}_smoke3/raw_predictions/H1_{_v}_smoke3",
                    f"{E8}/outputs/H1_{_v}_smoke3/failed_predictions/H1_{_v}_smoke3", "prompt-selection smoke run"))

# EXP_008 final run (frozen H1 hybrid prompt) on the 30 shared encounters.
RUNS.append(Run("q06_exp008_H1_main30", "Qwen3-0.6B", "EXP_008", "H1 hybrid (full P02 schema + faithfulness rules, no examples)", "core",
                f"{E8}/outputs/H1_main30/parsed_predictions/H1_main30", f"{E8}/outputs/H1_main30/raw_predictions/H1_main30",
                f"{E8}/outputs/H1_main30/failed_predictions/H1_main30", "frozen prompt sha256 dc10ba06..."))

# P05 was run on its own validation-50 split, which shares no encounter with the prompt-development 50 used by every other run (verified by
# inventory.py). Its fair comparison partner is EXP_003 (whose 100 development encounters contain that split), never the 1.7B runs.
VALIDATION_SPLIT_RUNS = {"q06_exp004_P05"}

# Ground truth. Every recorded run names finetune_slm/archive/dataset_v2_batch_001_corrected (checked against the run manifests); the pre-correction batch has
# different transcripts AND labels for all 500 encounters and must never be mixed in.
DATASET = "finetune_slm/archive/dataset_v2_batch_001_corrected"
INPUT_DIR = ROOT / DATASET / "output" / "inputs"
LABEL_DIR = ROOT / DATASET / "output" / "labels"
