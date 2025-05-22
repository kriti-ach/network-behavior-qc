import pandas as pd
import glob
from pathlib import Path
import re

folder_path = Path("/oak/stanford/groups/russpold/data/network_grant/behavioral_data/out_of_scanner/") 

for subject_folder in glob.glob(str(folder_path / "*")):
    subject_id = Path(subject_folder).name
    if re.match(r"s\d{2,}", subject_id):
        print(f"Processing Subject: {subject_id}")

        for file in glob.glob(str(Path(subject_folder) / "*.csv")):
            df = pd.read_csv(file)