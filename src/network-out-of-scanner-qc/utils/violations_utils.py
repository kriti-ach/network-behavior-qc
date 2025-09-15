import pandas as pd
import os
from pathlib import Path
import re
import numpy as np

def compute_violations(subject_id, df, task_name):
    violations_row = []

    for i in range(len(df) - 1):  # Go until the second to last trial
        # Check for a Go trial followed by a Stop trial with a violation
        if (df.iloc[i]['stop_signal_condition'] == 'go' and
            df.iloc[i + 1]['stop_signal_condition'] == 'stop' and
            (df.iloc[i + 1]['rt'] != -1)):
            
            go_rt = df.iloc[i]['rt']         # RT of Go trial
            stop_rt = df.iloc[i + 1]['rt']  # RT of Stop trial
            
            if pd.notna(go_rt) and pd.notna(stop_rt):  # Ensure RTs are valid
                difference = stop_rt - go_rt  # Calculate the difference
                ssd = df.iloc[i + 1]['SS_delay']    # SSD for the Stop trial
                violations_row.append({'subject_id': subject_id, 'task_name': task_name, 'ssd': ssd, 'difference': difference})

    return pd.DataFrame(violations_row)

