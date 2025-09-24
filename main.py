from pathlib import Path
import runpy


def main() -> None:
    project_root = Path(__file__).resolve().parent

    # Run QC
    runpy.run_path(str(project_root / 'src' / 'network-out-of-scanner-qc' / 'qc' / 'qc.py'), run_name='__main__')

    # Run Exclusions
    runpy.run_path(str(project_root / 'src' / 'network-out-of-scanner-qc' / 'exclusions' / 'exclusions.py'), run_name='__main__')

    # Run Violations
    runpy.run_path(str(project_root / 'src' / 'network-out-of-scanner-qc' / 'violations' / 'violations.py'), run_name='__main__')


if __name__ == '__main__':
    main()


