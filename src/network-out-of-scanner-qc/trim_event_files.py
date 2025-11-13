"""
Script to copy and trim event files based on scan time data.

For event files that need to be trimmed (final_decision == 'trim'),
this script:
1. Copies original event files to untrimmed_event_files
2. Trims event files (removes rows after scan_time_seconds) and saves to trimmed_event_files
"""
import pandas as pd
from pathlib import Path
import shutil
import sys

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import load_config
from utils.trimmed_behavior_utils import get_bids_task_name

# Load config
cfg = load_config()

# Scratch directory for event files
SCRATCH_BASE = Path('/scratch/users/kritiach/validation_BIDS_trimming_event_files')
UNTRIMMED_DIR = SCRATCH_BASE / 'untrimmed_event_files'
TRIMMED_DIR = SCRATCH_BASE / 'trimmed_event_files'

# Create directories
UNTRIMMED_DIR.mkdir(parents=True, exist_ok=True)
TRIMMED_DIR.mkdir(parents=True, exist_ok=True)


def find_event_files(subject_id, session, task_name, bids_path):
    """
    Find event files matching subject, session, and task in BIDS structure.
    
    Returns list of event file paths.
    """
    subject_path = bids_path / f'sub-{subject_id}'
    if not subject_path.exists():
        return []
    
    session_path = subject_path / session
    if not session_path.exists():
        return []
    
    func_path = session_path / 'func'
    if not func_path.exists():
        return []
    
    # Look for event files matching the task
    print(f"Looking for event files in {func_path} for task {task_name}")
    event_files = list(func_path.glob(f'sub-{subject_id}_{session}_task-{task_name}_run-*_events.tsv'))
    
    return event_files


def trim_event_file(event_file, scan_time_seconds):
    """
    Trim event file by removing all rows where onset >= scan_time_seconds.
    
    Args:
        event_file: Path to event file
        scan_time_seconds: Time in seconds to trim at
        
    Returns:
        Trimmed DataFrame
    """
    df = pd.read_csv(event_file, sep='\t')
    
    # Filter rows where onset < scan_time_seconds
    if 'onset' in df.columns:
        df_trimmed = df[df['onset'] < scan_time_seconds].copy()
    else:
        # If no onset column, return original
        print(f"Warning: No 'onset' column in {event_file}")
        return df
    
    return df_trimmed


def process_event_files():
    """
    Process event files based on trimmed_fmri_csvs_with_scan_time.csv
    """
    # Read the CSV with scan time data
    scan_time_file = cfg.trimmed_csv_output_path / 'trimmed_fmri_csvs_with_scan_time.csv'
    if not scan_time_file.exists():
        print(f"Error: {scan_time_file} not found. Run process_trimmed_with_scan_time.py first.")
        return
    
    scan_time_df = pd.read_csv(scan_time_file)
    
    # Filter to only files that should be trimmed
    to_trim_df = scan_time_df[scan_time_df['final_decision'] == 'trim'].copy()
    
    print(f"Found {len(to_trim_df)} tasks to trim")
    
    # Get BIDS paths from config
    discovery_bids_path = cfg.discovery_bids_path
    validation_bids_path = cfg.validation_bids_path
    discovery_subjects = cfg.discovery_subjects
    
    processed_count = 0
    error_count = 0
    
    for idx, row in to_trim_df.iterrows():
        subject_id = row['subject_id']
        session = row['session']
        task_name = row['task_name']
        scan_time_seconds = row['scan_time_seconds']
        
        # Skip if scan_time is NaN
        if pd.isna(scan_time_seconds):
            print(f"Skipping {subject_id} {session} {task_name}: no scan time")
            continue
        
        # Determine which BIDS path to use
        if subject_id in discovery_subjects:
            bids_path = discovery_bids_path
        else:
            bids_path = validation_bids_path
        
        # Convert task name to BIDS format
        bids_task_name = get_bids_task_name(task_name)
        
        # Find event files
        event_files = find_event_files(subject_id, session, bids_task_name, bids_path)
        
        if not event_files:
            print(f"No event files found for {subject_id} {session} {bids_task_name}")
            continue
        
        print(f"Processing {subject_id} {session} {bids_task_name}: {len(event_files)} event file(s)")
        
        for event_file in event_files:
            try:
                # Create output filename preserving BIDS structure
                output_filename = event_file.name
                
                # Copy original to untrimmed directory
                untrimmed_file = UNTRIMMED_DIR / output_filename
                shutil.copy2(event_file, untrimmed_file)
                
                # Trim event file
                df_trimmed = trim_event_file(event_file, scan_time_seconds)
                
                # Save trimmed version
                trimmed_file = TRIMMED_DIR / output_filename
                df_trimmed.to_csv(trimmed_file, sep='\t', index=False)
                
                print(f"  Processed: {output_filename} (trimmed at {scan_time_seconds:.2f}s, {len(df_trimmed)} rows)")
                processed_count += 1
                
            except Exception as e:
                print(f"  Error processing {event_file}: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
                continue
    
    print(f"\nProcessing complete:")
    print(f"  Processed: {processed_count} event files")
    print(f"  Errors: {error_count}")
    print(f"  Untrimmed files: {UNTRIMMED_DIR}")
    print(f"  Trimmed files: {TRIMMED_DIR}")


if __name__ == '__main__':
    process_event_files()

