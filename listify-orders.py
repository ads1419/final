#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import re
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filename")
args = parser.parse_args()


def get_qty(txt):

    """
        Returns the Special Quantity key for a given order. 
            Sample input string: '...no. of 500 gm packets required: 1)'
            Returns: 1
    """

    match = re.search(": ([0-9]+?)\)", txt)
    if match:
        return int(match.group(1))


def extract_num(txt):

    """
        Searches a string and returns the last number found, if present. 
        Otherwise return 1.
        Use case: For an item key such as 'Tondli 300 gms ', return 300 (to calculate total qty required)
    """

    match = re.findall("([0-9]+)", txt)
    if match:
        return int(match[-1])
    else:
        return 1


def get_unit(txt):

    """
        Gets unit from an item string.
        Assumption: standard occurence of units all across the board. 
    """
    
    txt = txt.lower()
    if txt.find(" gm") != -1:
        unit = "gms"
    elif txt.find(" pc") != -1:
        unit = "pcs"
    elif txt.find(" bunch") != -1:
        unit = "bunches"
    else:
        unit = "kgs"
    return unit


FILE = Path(args.filename)


if __name__ == "__main__":

    # Try to read valid `csv` and `xlsx` files into a dataframe `df`.
    try:
        if "csv" in FILE.suffix:
            df = pd.read_csv(FILE)
        else:
            df = pd.read_excel(FILE)
    except OSError:
        print("Error occured, invalid file!")

    print(f"\nSuccessfully read {str(FILE)} with {len(df)} rows.")

    # Identify the Orders Column
    for col in df.columns:
        if "Your Order" in col:
            your_order = col

    # ## Prepare Keys
    k = []
    for order in df[your_order]:
        split = order.split(")")[:-1]  # last item is always total cost
        split = [s.replace("\n", "") for s in split]  # remove newlines if present
        k.append(split)

    items = []
    for order in k:
        for item in order:
            if len(item.split("(")) > 1:
                items.append(item.split("(")[0].strip())

    all_items = sorted(list(set(items)))

    # ## Prepare Count Dictionary
    # init order dictionary
    all_orders = {}
    for item in all_items:
        all_orders[item] = 0

    for order in k:
        for i in order:
            i = i + ")"
            sp1 = i.split("(")
            if len(sp1) < 2:
                continue

            key = sp1[0].strip()
            val = get_qty(sp1[1])
            all_orders[key] += val

    # create empty dataframe
    cleaned_df = pd.DataFrame.from_dict(all_orders, orient="index")
    cleaned_df.reset_index(inplace=True)
    cleaned_df.columns = ["item", "num_units"]

    # find quantity per item (amount of stuff in one packet)
    packet = []
    for item in cleaned_df.item:
        packet.append(extract_num(item))
    cleaned_df["qty_per_packet"] = packet

    # ### Total Quantity to be Purchased
    cleaned_df["total_qty"] = cleaned_df.num_units * cleaned_df.qty_per_packet

    # extract qty unit from item
    cleaned_df["unit"] = cleaned_df.item.apply(get_unit)

    # ### Handling the Curious Case of Bell Peppers
    for index, row in cleaned_df.iterrows():
        if row["item"] == "Red & Yellow Bell Pepper 2 each in a pack":

            # add red bell peppers
            cleaned_df = cleaned_df.append(
                {
                    "item": "Red Bell Pepper per pc",
                    "num_units": row["num_units"] * 2,
                    "qty_per_packet": 1,
                    "total_qty": row["num_units"] * 2,
                    "unit": "pcs",
                },
                ignore_index=True,
            )

            # add yellow bell peppers
            cleaned_df = cleaned_df.append(
                {
                    "item": "Yellow Bell Pepper per pc",
                    "num_units": row["num_units"] * 2,
                    "qty_per_packet": 1,
                    "total_qty": row["num_units"] * 2,
                    "unit": "pcs",
                },
                ignore_index=True,
            )

            # remove packet entry
            cleaned_df.drop(index=index, inplace=True)

    # Save file to disk as `listified-filename.csv`

    fname = "listified-" + str(FILE.stem) + ".csv"
    print(f"Saved listified file to {fname}!\n")
    cleaned_df.to_csv(fname, index=False)
