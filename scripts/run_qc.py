import glob
import os
import re
import sys
from pathlib import Path

import pandas as pd

from network_behavior_qc.config import load_config
from network_behavior_qc.exclusion_utils import (
    check_exclusion_criteria,
    create_combined_exclusions_csv,
    remove_some_flags_for_exclusion,
)
from network_behavior_qc.globals import DUAL_TASKS, LAST_N_TEST_TRIALS, SINGLE_TASKS
from network_behavior_qc.qc_utils import (
    append_summary_rows_to_csv,
    correct_columns,
    extract_task_name_out_of_scanner,
    get_task_metrics,
    infer_task_name_from_filename,
    initialize_qc_csvs,
    normalize_flanker_conditions,
    sort_subject_ids,
    update_qc_csv,
)
from network_behavior_qc.trimmed_behavior_utils import preprocess_rt_tail_cutoff
from network_behavior_qc.violations_utils import (
    aggregate_violations,
    compute_violations,
    create_violations_matrices,
    plot_violations,
)


def main() -> None:
    # Optional CLI override: --mode=fmri or --mode=out_of_scanner
    for arg in sys.argv[1:]:
        if arg.startswith('--mode='):
            os.environ['QC_DATA_MODE'] = arg.split('=', 1)[1]

    cfg = load_config()
    input_root = cfg.input_folder
    output_path = cfg.qc_output_folder
    flags_output_path = cfg.flags_output_folder
    exclusions_output_path = cfg.exclusions_output_folder
    violations_output_path = cfg.violations_output_folder
    trimmed_csv_output_path = cfg.trimmed_csv_output_path
    trimmed_records = []
    last_n_test_trials = LAST_N_TEST_TRIALS

    if cfg.is_fmri:
        discovered_tasks = set()
        for subj_dir in glob.glob(str(input_root / 's*')):
            for ses_dir in glob.glob(str(Path(subj_dir) / 'ses-*')):
                for file in glob.glob(str(Path(ses_dir) / '*.csv')):
                    if '/practice/' in file.lower():
                        continue
                    tname = infer_task_name_from_filename(Path(file).name)
                    if tname:
                        discovered_tasks.add(tname)
        tasks = sorted(discovered_tasks)
    else:
        tasks = SINGLE_TASKS + DUAL_TASKS

    initialize_qc_csvs(tasks, output_path, include_session=cfg.is_fmri)

    violations_df = pd.DataFrame()
    if cfg.is_fmri:
        for subj_dir in glob.glob(str(input_root / 's*')):
            subject_id = Path(subj_dir).name
            if not re.match(r's\d{2,}', subject_id):
                continue
            print(f'Processing Subject: {subject_id}')
            for ses_dir in glob.glob(str(Path(subj_dir) / 'ses-*')):
                for file in glob.glob(str(Path(ses_dir) / '*.csv')):
                    if '/practice/' in file.lower():
                        continue
                    filename = Path(file).name
                    task_name = infer_task_name_from_filename(filename)
                    if not task_name:
                        continue
                    try:
                        df = pd.read_csv(file)
                        if 'flanker' in task_name and 'stop_signal' in task_name:
                            df = normalize_flanker_conditions(df)
                        df_trimmed, cut_pos, cut_before_halfway, proportion_blank = preprocess_rt_tail_cutoff(
                            df,
                            subject_id=subject_id,
                            session=Path(ses_dir).name,
                            task_name=task_name,
                            last_n_test_trials=last_n_test_trials,
                        )
                        if cut_pos is not None:
                            trimmed_records.append(
                                {
                                    'subject_id': subject_id,
                                    'session': Path(ses_dir).name,
                                    'task_name': task_name,
                                    'cutoff_index': int(cut_pos),
                                    'before_halfway': bool(cut_before_halfway),
                                    'proportion_blank_trials': float(proportion_blank),
                                }
                            )
                            if cut_before_halfway:
                                continue
                            df = df_trimmed

                        metrics = get_task_metrics(df, task_name, cfg)
                        session = Path(ses_dir).name if cfg.is_fmri else None
                        update_qc_csv(output_path, task_name, subject_id, metrics, session=session)
                    except Exception as e:
                        print(f'Error processing {task_name} for subject {subject_id}: {str(e)}')
    else:
        for subject_folder in glob.glob(str(input_root / 's*')):
            subject_id = Path(subject_folder).name
            if re.match(r's\d{2,}', subject_id):
                print(f'Processing Subject: {subject_id}')
                for file in glob.glob(str(Path(subject_folder) / '*.csv')):
                    filename = Path(file).name
                    task_name = extract_task_name_out_of_scanner(filename)
                    if task_name == 'stop_signal_with_go_no_go':
                        task_name = 'stop_signal_with_go_nogo'
                    if task_name:
                        try:
                            df = pd.read_csv(file)
                            if 'flanker' in task_name and 'stop_signal' in task_name:
                                df = normalize_flanker_conditions(df)
                            df_trimmed, cut_pos, cut_before_halfway, proportion_blank = preprocess_rt_tail_cutoff(
                                df,
                                subject_id=subject_id,
                                session=None,
                                task_name=task_name,
                                last_n_test_trials=last_n_test_trials,
                            )
                            if cut_pos is not None:
                                trimmed_records.append(
                                    {
                                        'subject_id': subject_id,
                                        'session': '',
                                        'task_name': task_name,
                                        'cutoff_index': int(cut_pos),
                                        'before_halfway': bool(cut_before_halfway),
                                        'proportion_blank_trials': float(proportion_blank),
                                    }
                                )
                                if cut_before_halfway:
                                    continue
                                df = df_trimmed
                            metrics = get_task_metrics(df, task_name, cfg)
                            if 'stop_signal' in task_name:
                                violations_df = pd.concat(
                                    [violations_df, compute_violations(subject_id, df, task_name)]
                                )
                            update_qc_csv(output_path, task_name, subject_id, metrics, session=None)
                        except Exception as e:
                            print(f'Error processing {task_name} for subject {subject_id}: {str(e)}')

    for task in tasks:
        exclusion_df = pd.DataFrame({'subject_id': [], 'metric': [], 'metric_value': [], 'threshold': []})
        append_summary_rows_to_csv(output_path / f'{task}_qc.csv')
        if task in {'flanker_with_cued_task_switching', 'shape_matching_with_cued_task_switching'}:
            correct_columns(output_path / f'{task}_qc.csv')
        task_csv = pd.read_csv(output_path / f'{task}_qc.csv')

        if cfg.is_fmri and 'session' in task_csv.columns:
            from network_behavior_qc.exclusion_utils import flag_fmri_condition_metrics

            condition_acc_flags_df, omission_rate_flags_df = flag_fmri_condition_metrics(task, task_csv)
        else:
            condition_acc_flags_df = pd.DataFrame(
                {'subject_id': [], 'metric': [], 'metric_value': [], 'threshold': []}
            )
            omission_rate_flags_df = pd.DataFrame(
                {'subject_id': [], 'metric': [], 'metric_value': [], 'threshold': []}
            )

        exclusion_df = check_exclusion_criteria(task, task_csv, exclusion_df)
        flagged_df = exclusion_df.copy()
        exclusion_df = remove_some_flags_for_exclusion(task, exclusion_df)
        flagged_df = flagged_df[~flagged_df.index.isin(exclusion_df.index)]

        if cfg.is_fmri:
            flags_to_merge = []
            if len(condition_acc_flags_df) > 0:
                flags_to_merge.append(condition_acc_flags_df)
            if len(omission_rate_flags_df) > 0:
                flags_to_merge.append(omission_rate_flags_df)
            if flags_to_merge:
                flagged_df = pd.concat([flagged_df] + flags_to_merge, ignore_index=True)
                flagged_df = sort_subject_ids(flagged_df)

        task_csv = task_csv.loc[:, ~task_csv.columns.str.contains('new', case=False)]
        task_csv.to_csv(output_path / f'{task}_qc.csv', index=False)
        flagged_df.to_csv(flags_output_path / f'flagged_data_{task}.csv', index=False)
        exclusion_df.to_csv(exclusions_output_path / f'excluded_data_{task}.csv', index=False)

    create_combined_exclusions_csv(tasks, exclusions_output_path)

    if not cfg.is_fmri:
        violations_df.to_csv(violations_output_path / 'violations_data.csv', index=False)
        aggregated_violations_df = aggregate_violations(violations_df)
        aggregated_violations_df.to_csv(
            violations_output_path / 'aggregated_violations_data.csv', index=False
        )
        plot_violations(aggregated_violations_df, violations_output_path)
        create_violations_matrices(aggregated_violations_df, violations_output_path)

    if len(trimmed_records) > 0:
        trimmed_df = pd.DataFrame(trimmed_records)
        out_csv = (
            trimmed_csv_output_path / 'trimmed_fmri_behavior_tasks.csv'
            if cfg.is_fmri
            else trimmed_csv_output_path / 'trimmed_out_of_scanner_tasks.csv'
        )
        trimmed_df.to_csv(out_csv, index=False)


if __name__ == '__main__':
    main()

