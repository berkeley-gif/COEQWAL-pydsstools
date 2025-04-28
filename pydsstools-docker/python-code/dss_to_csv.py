from pydsstools.heclib.dss import HecDss
from pandas.tseries.offsets import MonthEnd
import pandas as pd
import numpy as np
import os
import argparse

def export_all_paths_to_csv(dss_file_path, output_csv_path):
    print(f"\nStarting export process...")
    print(f"Input DSS: {dss_file_path}")
    print(f"Output CSV: {output_csv_path}")
    
    if not os.path.exists(dss_file_path):
        print(f"❌ ERROR: DSS file does not exist: {dss_file_path}")
        return
    
    # Open the DSS file
    print("\nOpening DSS file...")
    dss = HecDss.Open(dss_file_path)

    # Check available pathnames
    print("Getting pathname list...")
    available_pathnames = dss.getPathnameList("/*/*/*/*/*/*/")
    print(f"Found {len(available_pathnames)} pathnames to process")

    all_datetimes = set()
    time_series_groups = {}

    # Process each path
    for pathname in available_pathnames:
        try:
            data = dss.read_ts(pathname)
            parts = pathname.split('/')
            a, b, c, d, e, f = parts[1:7]
            series_key = f"{b}_{c}_{e}_{f}"

            if series_key not in time_series_groups:
                time_series_groups[series_key] = {
                    'data': {},
                    'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f,
                    'units': getattr(data, 'units', ''),
                    'type': getattr(data, 'type', '')
                }

            values = np.where(data.values == -901, np.nan, data.values)
            
            for dt, value in zip(data.pytimes, values):
                # All series are monthly ⇒ shift timestamp back one month so
                # value represents previous month (end-of-month)
                ts_dt = pd.Timestamp(dt).normalize() - MonthEnd(1)

                time_series_groups[series_key]['data'][ts_dt] = value
                all_datetimes.add(ts_dt)
        
        except Exception as e:
            print(f"⚠️ Warning: Error processing '{pathname}': {e}")

    sorted_datetimes = sorted(list(all_datetimes))
    sorted_keys = sorted(time_series_groups.keys(), key=lambda x: time_series_groups[x]['b'])

    dfs_to_concat = [pd.DataFrame({'DateTime': sorted_datetimes})]

    for series_key in sorted_keys:
        info = time_series_groups[series_key]
        column_name = f"{info['b']}_{info['c']}_{info['f']}"
        series_data = [info['data'].get(dt, np.nan) for dt in sorted_datetimes]
        dfs_to_concat.append(pd.DataFrame({column_name: series_data}))

    combined = pd.concat(dfs_to_concat, axis=1)

    # Clip to modeller's expected date window
    START_DATE = pd.Timestamp("1921-10-31")
    END_DATE   = pd.Timestamp("2021-09-30")
    combined = combined[(combined["DateTime"] >= START_DATE) &
                         (combined["DateTime"] <= END_DATE)]

    # Drop rows where every data column (excluding DateTime) is NaN
    if combined.shape[1] > 1:
        combined = combined[combined.iloc[:, 1:].notna().any(axis=1)]

    header_df = pd.DataFrame({
        'DateTime': ['A', 'B', 'C', 'D', 'E', 'F', 'UNITS'],
        **{f"{info['b']}_{info['c']}_{info['f']}": [
            info['a'],                      # Row A: Part A
            info['b'],                      # Row B: Part B
            info['c'],                      # Row C: Part C
            info['e'],                      # Row D: *Part E* per new mapping
            info['f'],                      # Row E: *Part F* per new mapping
            info.get('type', ''),           # Row F: record type (INST-VAL, PER-VAL, ...)
            info['units']                  # Row UNITS: units string
        ] for info in [time_series_groups[key] for key in sorted_keys]}
    })

    final_df = pd.concat([header_df, combined], ignore_index=True)
    # Create output directory if a folder path is provided
    output_dir = os.path.dirname(output_csv_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    final_df.to_csv(output_csv_path, index=False, header=False, na_rep='NaN')
    print(f"✅ Exported to '{output_csv_path}'")

    dss.close()
    print("🎉 Export completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DSS to CSV")
    parser.add_argument("--dss", type=str, required=True, help="Path to DSS file")
    parser.add_argument("--csv", type=str, required=True, help="Path to output CSV file")
    
    args = parser.parse_args()
    export_all_paths_to_csv(args.dss, args.csv)
