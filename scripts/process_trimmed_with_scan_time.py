"""Process trimmed behavioral CSVs and add scan time metadata."""

import json
from pathlib import Path

import nibabel as nib
import pandas as pd

from network_behavior_qc.config import load_config
from network_behavior_qc.trimmed_behavior_utils import get_bids_task_name

cfg = load_config()
DISCOVERY_BIDS_PATH = cfg.discovery_bids_path
VALIDATION_BIDS_PATH = cfg.validation_bids_path
DISCOVERY_SUBJECTS = cfg.discovery_subjects


def get_scan_time_from_bids(subject_id, session, task_name, bids_path):
    subject_path = bids_path / f'sub-{subject_id}'
    if not subject_path.exists():
        return None

    session_path = subject_path / f'{session}'
    if not session_path.exists():
        return None
    total_duration = 0.0

    json_files = list(
        session_path.glob(f'func/sub-{subject_id}_{session}_task-{task_name}_run-*_echo-2_bold.json')
    )
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if 'RepetitionTime' in data:
                    nii_file = json_file.with_suffix('.nii.gz')
                    if not nii_file.exists():
                        nii_file = json_file.with_suffix('.nii')
                    if nii_file.exists():
                        try:
                            nii = nib.load(str(nii_file))
                            n_vols = nii.shape[-1] if len(nii.shape) > 3 else 1
                            tr = float(data['RepetitionTime'])
                            total_duration += tr * n_vols
                        except Exception:
                            pass
        except Exception as e:
            print(f'Warning: Could not read JSON file {json_file}: {e}')
            continue

    if total_duration == 0.0:
        nii_files = list(session_path.glob('**/*.nii.gz')) + list(session_path.glob('**/*.nii'))
        for nii_file in nii_files:
            try:
                nii = nib.load(str(nii_file))
                tr = nii.header.get_zooms()[-1] if len(nii.shape) > 3 else 2.0
                if not isinstance(tr, (int, float)) or tr <= 0:
                    tr = 2.0
                n_vols = nii.shape[-1] if len(nii.shape) > 3 else 1
                total_duration += tr * n_vols
            except Exception as e:
                print(f'Warning: Could not read NIfTI file {nii_file}: {e}')
                continue

    return total_duration if total_duration > 0 else None


def main():
    trimmed_tasks_file = cfg.trimmed_csv_output_path / 'trimmed_fmri_behavior_tasks.csv'
    if not trimmed_tasks_file.exists():
        print(f'Error: {trimmed_tasks_file} not found. Run run_qc.py first to create it.')
        return

    trimmed_tasks_df = pd.read_csv(trimmed_tasks_file)
    print(f'Found {len(trimmed_tasks_df)} trimmed tasks to process')

    all_trimmed_data = []
    for _, row in trimmed_tasks_df.iterrows():
        subject_id = row['subject_id']
        session = row['session']
        task_name = get_bids_task_name(row['task_name'])
        bids_path = DISCOVERY_BIDS_PATH if subject_id in DISCOVERY_SUBJECTS else VALIDATION_BIDS_PATH

        try:
            scan_time = get_scan_time_from_bids(subject_id, session, task_name, bids_path)
            if (subject_id == 's394' and session == 'ses-07') or (
                subject_id == 's1445' and session == 'ses-11'
            ):
                final_decision = 'do not trim because subject fell asleep'
            else:
                final_decision = 'trim'

            all_trimmed_data.append(
                {
                    'subject_id': subject_id,
                    'session': session,
                    'task_name': task_name,
                    'scan_time_seconds': scan_time,
                    'final_decision': final_decision,
                }
            )
        except Exception as e:
            print(f'Error processing {subject_id} {session} {task_name}: {e}')
            continue

    if all_trimmed_data:
        summary_df = pd.DataFrame(all_trimmed_data)
        summary_file = cfg.trimmed_csv_output_path / 'trimmed_fmri_csvs_with_scan_time.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f'Summary saved to: {summary_file}')
        print(f'Total files processed: {len(all_trimmed_data)}')
    else:
        print('No files were processed.')


if __name__ == '__main__':
    main()

