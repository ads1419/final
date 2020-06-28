import pandas as pd
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("filename")
args = parser.parse_args()

FILE = Path(args.filename)

if __name__ == "__main__":
    df = pd.read_excel(FILE)
    print(f"\nRead {FILE} with {len(df)} rows!")
    custs = df["Customer Name "].unique()

    fname = "splitted-" + str(FILE.stem) + ".xlsx"
    with pd.ExcelWriter(fname) as writer:
        for cust in custs:
            df[df["Customer Name "] == cust].to_excel(writer, sheet_name=cust)
    print(f"Saved splitted file to {fname}!\n")