# ================================================
# csv_levels.py – post-processing pipeline helpers
# -----------------------------------------------
# This script takes the Level-0 CSV produced by
# `dss_to_csv.py` and walks it through successive
# filtering stages, OR prints inspection aids.
#
# Modes (first positional argument)
#   0     Build Level-0   — needs --dss and output_csv
#   1     Build Level-1   — needs input_csv (L0)   and output_csv
#   2     Build Level-2   — needs input_csv (L1), output_csv, and --config keep.yml
#   listC Print unique Part C values found in input_csv (L0)
#   mapBC Print or save (with --mapfile) mapping of PartC → PartB's
#
# Common positional arguments
#   input_csv   Level-0 or Level-1 file, as required by mode
#   output_csv  File to write for modes 0,1,2 (omit for listC/mapBC)
#
# Common optional flags
#   --dss PATH        DSS file to read when mode 0 builds Level-0
#   --drop REGEX ...  Regex(es) for B-part names to drop when making Level-1
#   --config YAML     Mapping C: [B1,…] for selecting Level-2
#   --mapfile TXT     Save mapBC output to a text file instead of stdout
# ================================================

import argparse
import re
import sys
import yaml
import pandas as pd
from pathlib import Path

HEADER_ROWS = 7  # Rows 0-6 contain metadata (A, B, C, D, E, TYPE, UNITS)

META_LABELS = [
    'A', 'B', 'C', 'D', 'E', 'TYPE', 'UNITS'
]


def read_level0(csv_path: Path):
    """Read Level-0 CSV exported by dss_to_csv.py and split header/meta."""
    df = pd.read_csv(csv_path, header=None)
    header = df.iloc[:HEADER_ROWS].copy()
    data = df.iloc[HEADER_ROWS:].reset_index(drop=True)

    # Build a meta-data DataFrame: one row per column (skip DateTime col)
    meta_df = (
        header.iloc[1:, 1:]  # drop DateTime column
        .T
        .reset_index(drop=True)
    )
    meta_df.columns = META_LABELS
    return header, data, meta_df, df


def filter_level1(meta_df: pd.DataFrame, drop_patterns: list[str]):
    """Return boolean mask of columns to KEEP for Level-1."""
    mask = pd.Series(True, index=meta_df.index)
    for pat in drop_patterns:
        regex = re.compile(pat, flags=re.I)
        mask &= ~meta_df['B'].str.contains(regex)
    return mask


def write_level_csv(original_df: pd.DataFrame, keep_mask, out_path: Path):
    """Write a CSV keeping only columns where keep_mask is True (plus DateTime)."""
    cols_to_keep = [0] + (keep_mask[keep_mask].index + 1).tolist()  # +1 for DateTime offset
    filtered_df = original_df.iloc[:, cols_to_keep]
    filtered_df.to_csv(out_path, index=False, header=False, na_rep='NaN')


def summary_by_partc(meta_df: pd.DataFrame, mask):
    """Print PartC ➜ list of retained PartB's."""
    view = meta_df[mask]
    grouped = view.groupby('C')['B'].unique()
    for c, b_list in grouped.items():
        print(f"{c}:")
        for b in sorted(b_list):
            print(f"  {b}")
        print()


def load_level2_config(config_path: Path):
    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)
    # cfg expected as mapping of C: list_of_B
    allowed = set()
    for c, bs in cfg.items():
        allowed.update((c, b) for b in bs)
    return allowed


def filter_level2(meta_df: pd.DataFrame, allowed_pairs):
    pairs = [(row.C, row.B) for _, row in meta_df.iterrows()]
    mask = [pair in allowed_pairs for pair in pairs]
    return pd.Series(mask, index=meta_df.index)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utilities to move from Level-0 ➜ Level-1 ➜ Level-2 or just inspect metadata.")

    parser.add_argument("mode", choices=["0", "1", "2", "listC", "mapBC"],
                        help="0=create Level-0, 1=create Level-1, 2=create Level-2, listC=print unique PartC's, mapBC=print PartC→B list")
    parser.add_argument("input_csv", nargs="?", help="Input CSV (not needed for mode 0)")
    parser.add_argument("output_csv", nargs="?", help="Output CSV (required for modes 0,1,2)")
    parser.add_argument("--dss", help="Path to DSS file (required for mode 0)")
    parser.add_argument("--drop", nargs="*", default=[r"_SYS$", r"_VAL$"],
                        help="Regex patterns to drop B-parts when building Level-1")
    parser.add_argument("--config", help="YAML with mapping of C: [B1, B2, ...] for Level-2")
    parser.add_argument("--mapfile", help="If provided with mapBC, write the mapping to this text file instead of stdout")

    args = parser.parse_args()

    if args.mode == "0":
        if not (args.dss and args.output_csv):
            parser.error("For mode 0 you must provide --dss and output_csv path")
        from dss_to_csv import export_all_paths_to_csv
        export_all_paths_to_csv(args.dss, args.output_csv)
        sys.exit(0)

    if not args.input_csv:
        parser.error("input_csv is required for modes 1,2,listC,mapBC")

    in_path = Path(args.input_csv)

    # read once
    header, data, meta, df_full = read_level0(in_path)

    if args.mode == "listC":
        unique_c = sorted(meta['C'].unique())
        for c in unique_c:
            print(c)
        sys.exit(0)

    if args.mode == "mapBC":
        mapping_out = []
        grouped = meta.groupby('C')['B'].unique()
        for c in sorted(grouped.index):
            mapping_out.append(f"{c}:")
            for b in sorted(grouped[c]):
                mapping_out.append(f"  {b}")
            mapping_out.append("")

        if args.mapfile:
            Path(args.mapfile).write_text("\n".join(mapping_out))
        else:
            print("\n".join(mapping_out))
        sys.exit(0)

    # Modes 1 and 2 need output_csv
    if not args.output_csv:
        parser.error("output_csv is required for modes 1 and 2")

    out_path = Path(args.output_csv)

    if args.mode == "1":
        mask = filter_level1(meta, args.drop)
        write_level_csv(df_full, mask, out_path)
        summary_by_partc(meta, mask)
    elif args.mode == "2":
        if not args.config:
            parser.error("--config YAML must be provided for Level-2 generation")
        allowed = load_level2_config(Path(args.config))
        mask = filter_level2(meta, allowed)
        write_level_csv(df_full, mask, out_path) 