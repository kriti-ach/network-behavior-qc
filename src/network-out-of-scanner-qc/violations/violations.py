import sys
from pathlib import Path
import glob
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src" / "network-out-of-scanner-qc"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from qc.qc_utils import extract_task_name_out_of_scanner  # noqa: E402
from violations.violations_utils import (  # noqa: E402
    compute_violations,
    aggregate_violations,
    plot_violations,
    create_violations_matrices,
)


def run_violations() -> None:
    folder_path = Path(
        "/oak/stanford/groups/russpold/data/network_grant/behavioral_data/out_of_scanner"
    )
    violations_output_path = Path(
        "/oak/stanford/groups/russpold/data/network_grant/behavioral_data/out_of_scanner_violations"
    )
    violations_output_path.mkdir(parents=True, exist_ok=True)

    violations_df = pd.DataFrame()

    for subject_folder in glob.glob(str(folder_path / "s*")):
        subject_id = Path(subject_folder).name
        if subject_id and subject_id.startswith("s"):
            for file in glob.glob(str(Path(subject_folder) / "*.csv")):
                filename = Path(file).name
                task_name = extract_task_name_out_of_scanner(filename)
                if task_name == "stop_signal_with_go_no_go":
                    task_name = "stop_signal_with_go_nogo"

                if task_name and "stop_signal" in task_name:
                    try:
                        df = pd.read_csv(file)
                        violations_df = pd.concat(
                            [violations_df, compute_violations(subject_id, df, task_name)]
                        )
                    except Exception as e:  # pragma: no cover
                        print(f"Error computing violations {task_name} for {subject_id}: {str(e)}")

    violations_df.to_csv(violations_output_path / "violations_data.csv", index=False)
    aggregated_violations_df = aggregate_violations(violations_df)
    aggregated_violations_df.to_csv(
        violations_output_path / "aggregated_violations_data.csv", index=False
    )
    plot_violations(aggregated_violations_df, violations_output_path)
    create_violations_matrices(aggregated_violations_df, violations_output_path)


if __name__ == "__main__":
    run_violations()


