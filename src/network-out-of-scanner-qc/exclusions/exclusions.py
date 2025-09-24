import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src" / "network-out-of-scanner-qc"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.utils import (  # noqa: E402
    append_summary_rows_to_csv,
    correct_columns,
)
from utils.globals import (  # noqa: E402
    SINGLE_TASKS_OUT_OF_SCANNER,
    DUAL_TASKS_OUT_OF_SCANNER,
)
from utils.exclusion_utils import check_exclusion_criteria  # noqa: E402


def run_exclusions() -> None:
    output_path = Path(
        "/oak/stanford/groups/russpold/data/network_grant/behavioral_data/out_of_scanner_qc"
    )
    exclusions_output_path = Path(
        "/oak/stanford/groups/russpold/data/network_grant/behavioral_data/out_of_scanner_exclusions"
    )
    exclusions_output_path.mkdir(parents=True, exist_ok=True)

    exclusion_df = pd.DataFrame(
        {"subject_id": [], "task_name": [], "metric": [], "metric_value": [], "threshold": []}
    )

    for task in SINGLE_TASKS_OUT_OF_SCANNER + DUAL_TASKS_OUT_OF_SCANNER:
        # assume QC CSVs are already created by QC step
        task_csv = pd.read_csv(output_path / f"{task}_qc.csv")
        exclusion_df = check_exclusion_criteria(task, task_csv, exclusion_df)

    exclusion_df.to_csv(exclusions_output_path / "exclusion_data.csv", index=False)


if __name__ == "__main__":
    run_exclusions()


