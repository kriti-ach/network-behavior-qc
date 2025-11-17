import pandas as pd
from utils.qc_utils import normalize_flanker_conditions

def test_normalize_flanker_conditions():
    """Test flanker condition normalization."""
    # Test with prefixed flanker conditions
    df = pd.DataFrame({
        'flanker_condition': ['H_incongruent', 'H_congruent', 'F_incongruent', 'F_congruent', 'other'],
        'other_col': [1, 2, 3, 4, 5]
    })
    
    normalized_df = normalize_flanker_conditions(df)
    
    # Check that prefixes are removed
    expected_conditions = ['incongruent', 'congruent', 'incongruent', 'congruent', 'other']
    assert list(normalized_df['flanker_condition']) == expected_conditions
    
    # Test with DataFrame without flanker_condition column
    df_no_flanker = pd.DataFrame({'other_col': [1, 2, 3]})
    normalized_df_no_flanker = normalize_flanker_conditions(df_no_flanker)
    assert list(normalized_df_no_flanker['other_col']) == [1, 2, 3]