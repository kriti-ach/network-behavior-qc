import pandas as pd
import numpy as np

def test_cued_task_switching():
    """Test cued task switching + stop signal condition parsing."""
    
    # Create test data
    data = {
        'SS_trial_type': ['go', 'go', 'stop', 'go', 'stop', 'go', 'stop', 'go'],
        'correct_trial': [1, 1, 0, 1, 1, 1, 0, 1],  # Stop failures are incorrect (0)
        'rt': [0.5, 0.6, 0.7, 0.8, np.nan, 1.0, 0.9, 1.2],  # Stop success has no RT
        'key_press': [1, 1, 2, 1, -1, 1, 2, 1],  # -1 for stop success
        'task_condition': ['stay', 'stay', 'stay', 'stay', 'stay', 'switch', 'switch', 'switch'],
        'cue_condition': ['stay', 'stay', 'stay', 'stay', 'stay', 'stay', 'stay', 'stay'],
        'stim_number': ['1', '2', '1', '2', '1', '2', '1', '2'],
        'task': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
        'correct_response': [1, 2, 1, 2, 1, 2, 1, 2]
    }
    
    df = pd.DataFrame(data)
    
    print("Test data:")
    print(df)
    print()
    
    # Test the condition parsing logic
    paired_conditions = ['tstay_cstay', 'tswitch_cstay']
    
    for paired_cond in paired_conditions:
        print(f"Testing condition: {paired_cond}")
        
        # Parse the condition manually
        if paired_cond.startswith('t') and '_c' in paired_cond:
            task_part = paired_cond[1:paired_cond.index('_c')]  # Extract "stay" from "tstay_cstay"
            cue_part = paired_cond[paired_cond.index('_c')+2:]  # Extract "stay" from "tstay_cstay"
            print(f"  task_part='{task_part}', cue_part='{cue_part}'")
            
            # Create the mask
            paired_mask = (df['task_condition'] == task_part) & (df['cue_condition'] == cue_part)
            print(f"  paired_mask sum: {paired_mask.sum()}")
            print(f"  paired_mask: {paired_mask.values}")
            
            # Calculate metrics manually
            go_mask = (df['SS_trial_type'] == 'go') & paired_mask
            stop_mask = (df['SS_trial_type'] == 'stop') & paired_mask
            stop_fail_mask = stop_mask & (df['correct_trial'] == 0)
            stop_succ_mask = stop_mask & (df['correct_trial'] == 1)
            
            print(f"  Go trials: {go_mask.sum()}")
            print(f"  Stop trials: {stop_mask.sum()}")
            print(f"  Stop fail trials: {stop_fail_mask.sum()}")
            print(f"  Stop success trials: {stop_succ_mask.sum()}")
            
            # Check stop failure RTs
            stop_fail_rts = df.loc[stop_fail_mask & (df['rt'].notna()), 'rt']
            print(f"  Stop fail RTs: {stop_fail_rts.values}")
            print(f"  Stop fail RT mean: {stop_fail_rts.mean()}")
            
            # Check go RTs
            go_rts = df.loc[go_mask & (df['rt'].notna()), 'rt']
            print(f"  Go RTs: {go_rts.values}")
            print(f"  Go RT mean: {go_rts.mean()}")
            
        else:
            print(f"  ERROR: Could not parse condition {paired_cond}")
        
        print()

if __name__ == "__main__":
    test_cued_task_switching() 