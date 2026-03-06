"""Copy and trim BIDS event files based on scan-time metadata."""

from pathlib import Path
import shutil

import pandas as pd

from network_behavior_qc.config import load_config

cfg = load_config()

SCRATCH_BASE = Path('/scratch/users/kritiach/validation_BIDS_trimming_event_files')
UNTRIMMED_DIR = SCRATCH_BASE / 'untrimmed_event_files'
TRIMMED_DIR = SCRATCH_BASE / 'trimmed_event_files'

UNTRIMMED_DIR.mkdir(parents=True, exist_ok=True)
TRIMMED_DIR.mkdir(parents=True, exist_ok=True)


def find_event_files(subject_id, session, task_name, bids_path):
    subject_path = bids_path / f'sub-{subject_id}'
    if not subject_path.exists():
        return []

    session_path = subject_path / session
    if not session_path.exists():
        return []

    func_path = session_path / 'func'
    if not func_path.exists():
        return []

    return list(func_path.glob(f'sub-{subject_id}_{session}_task-{task_name}_run-*_events.tsv'))


def trim_event_file(event_file, scan_time_seconds):
    df = pd.read_csv(event_file, sep='\t')
    if 'onset' in df.columns:
        return df[df['onset'] < scan_time_seconds].copy()
    print(f"Warning: No 'onset' column in {event_file}")
    return df


def main():
    scan_time_file = cfg.trimmed_csv_output_path / 'trimmed_fmri_csvs_with_scan_time.csv'
    if not scan_time_file.exists():
        print(f'Error: {scan_time_file} not found. Run process_trimmed_with_scan_time.py first.')
        return

    scan_time_df = pd.read_csv(scan_time_file)
    to_trim_df = scan_time_df[scan_time_df['final_decision'] == 'trim'].copy()
    print(f'Found {len(to_trim_df)} tasks to trim')

    discovery_bids_path = cfg.discovery_bids_path
    validation_bids_path = cfg.validation_bids_path
    discovery_subjects = cfg.discovery_subjects

    processed_count = 0
    error_count = 0
    for _, row in to_trim_df.iterrows():
        subject_id = row['subject_id']
        session = row['session']
        task_name = row['task_name']
        scan_time_seconds = row['scan_time_seconds']
        if pd.isna(scan_time_seconds):
            print(f'Skipping {subject_id} {session} {task_name}: no scan time')
            continue

        bids_path = discovery_bids_path if subject_id in discovery_subjects else validation_bids_path
        event_files = find_event_files(subject_id, session, task_name, bids_path)
        if not event_files:
            print(f'No event files found for {subject_id} {session} {task_name}')
            continue

        print(f'Processing {subject_id} {session} {task_name}: {len(event_files)} event file(s)')
        for event_file in event_files:
            try:
                output_filename = event_file.name
                untrimmed_file = UNTRIMMED_DIR / output_filename
                shutil.copy2(event_file, untrimmed_file)
                df_trimmed = trim_event_file(event_file, scan_time_seconds)
                trimmed_file = TRIMMED_DIR / output_filename
                df_trimmed.to_csv(trimmed_file, sep='\t', index=False)
                processed_count += 1
            except Exception as e:
                print(f'Error processing {event_file}: {e}')
                error_count += 1
                continue

    print('\nProcessing complete:')
    print(f'  Processed: {processed_count} event files')
    print(f'  Errors: {error_count}')
    print(f'  Untrimmed files: {UNTRIMMED_DIR}')
    print(f'  Trimmed files: {TRIMMED_DIR}')


if __name__ == '__main__':
    main()

