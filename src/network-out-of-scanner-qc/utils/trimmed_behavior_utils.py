"""
Utilities for processing trimmed behavioral data.
"""
import pandas as pd
import numpy as np


def preprocess_rt_tail_cutoff(df: pd.DataFrame, subject_id: str | None = None, session: str | None = None, task_name: str | None = None, last_n_test_trials: int = 10):
    """
    Detects if the experiment was terminated early by finding the last valid
    response ('rt' != -1) within 'test_trial' rows. If any trials exist after
    this last valid response, they are considered a "tail" and are trimmed.

    The cutoff removes ALL rows (including fixations, etc.) after the
    last valid test trial.

    Returns a tuple: (df_trimmed, cutoff_index_within_test_trials, cutoff_before_halfway, proportion_blank)

    If no tail is found to trim, returns (df, None, False, proportion_blank).
    """
    if 'trial_id' not in df.columns or 'rt' not in df.columns:
        # Still calculate proportion of blank trials
        if 'rt' in df.columns and 'trial_id' in df.columns:
            df['rt'] = pd.to_numeric(df['rt'], errors='coerce').fillna(-1)
            test_trials = df[df['trial_id'] == 'test_trial']
            if len(test_trials) > 0:
                proportion_blank = (test_trials['rt'] == -1).sum() / len(test_trials)
            else:
                proportion_blank = 0.0
        else:
            proportion_blank = 0.0
        return df, None, False, proportion_blank

    # Ensure 'rt' column is numeric; treat NaN as non-response (-1)
    df['rt'] = pd.to_numeric(df['rt'], errors='coerce').fillna(-1)

    # Find the last row (across ALL rows) with a valid response
    valid_mask_all = df['rt'] != -1
    if not valid_mask_all.any():
        # No valid responses at all; nothing to trim specially here
        # Calculate proportion of blank trials
        test_trials = df[df['trial_id'] == 'test_trial']
        if len(test_trials) > 0:
            proportion_blank = (test_trials['rt'] == -1).sum() / len(test_trials)
        else:
            proportion_blank = 0.0
        return df, None, False, proportion_blank

    last_valid_idx = valid_mask_all[valid_mask_all].index[-1]
    if last_valid_idx == df.index[-1]:
        # Already ends with a valid response; no trailing -1 segment
        # Still calculate proportion of blank trials
        test_trials = df[df['trial_id'] == 'test_trial']
        if len(test_trials) > 0:
            proportion_blank = (test_trials['rt'] == -1).sum() / len(test_trials)
        else:
            proportion_blank = 0.0
        return df, None, False, proportion_blank

    # Verify that ALL rows after last_valid_idx are indeed -1
    tail_all_minus1 = (df.loc[last_valid_idx:].iloc[1:]['rt'] == -1).all()
    if not tail_all_minus1:
        # Mixed tail; do not trim
        # Still calculate proportion of blank trials
        test_trials = df[df['trial_id'] == 'test_trial']
        if len(test_trials) > 0:
            proportion_blank = (test_trials['rt'] == -1).sum() / len(test_trials)
        else:
            proportion_blank = 0.0
        return df, None, False, proportion_blank

    # Additional guard: require that the last last_n_test_trials test_trial RTs are -1
    df_test_end = df[df['trial_id'] == 'test_trial']
    if len(df_test_end) < last_n_test_trials:
        # Not enough trailing test trials to be confident; do not trim
        # Still calculate proportion of blank trials
        if len(df_test_end) > 0:
            proportion_blank = (df_test_end['rt'] == -1).sum() / len(df_test_end)
        else:
            proportion_blank = 0.0
        return df, None, False, proportion_blank
    if not (pd.to_numeric(df_test_end['rt'].tail(last_n_test_trials), errors='coerce').fillna(-1) == -1).all():
        # Do not trim unless the final last_n_test_trials test trials are all -1
        # Still calculate proportion of blank trials
        if len(df_test_end) > 0:
            proportion_blank = (df_test_end['rt'] == -1).sum() / len(df_test_end)
        else:
            proportion_blank = 0.0
        return df, None, False, proportion_blank

    # Trim to include up to and including last_valid_idx
    cutoff_iloc = df.index.get_loc(last_valid_idx)
    df_trimmed = df.iloc[:cutoff_iloc + 1].copy()

    # Compute cutoff position relative to ALL rows
    cutoff_pos = cutoff_iloc + 1  # first dropped row position in full df (0-based index within df)
    
    # Compute halfway point relative to test trials
    test_trials = df[df['trial_id'] == 'test_trial']
    if len(test_trials) > 0:
        halfway = len(test_trials) / 2.0
        # Find how many test trials are included up to and including last_valid_idx
        test_trials_included = test_trials[test_trials.index <= last_valid_idx]
        num_test_trials_before_cutoff = len(test_trials_included)
        cutoff_before_halfway = num_test_trials_before_cutoff < halfway
        
        # Calculate proportion of blank trials (rt == -1) in original dataframe
        proportion_blank = (test_trials['rt'] == -1).sum() / len(test_trials)
    else:
        # No test trials, use defaults
        halfway = len(df) / 2.0
        cutoff_before_halfway = cutoff_pos < halfway
        proportion_blank = 0.0

    return df_trimmed, cutoff_pos, cutoff_before_halfway, proportion_blank

