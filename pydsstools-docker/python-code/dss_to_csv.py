from pydsstools.heclib.dss import HecDss
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
                time_series_groups[series_key] = {'data': {}, 'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f}

            values = np.where(data.values == -901, np.nan, data.values)
            
            for dt, value in zip(data.pytimes, values):
                time_series_groups[series_key]['data'][dt] = value
                all_datetimes.add(dt)
        
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

    combined_df = pd.concat(dfs_to_concat, axis=1)

    header_df = pd.DataFrame({
        'DateTime': ['A', 'B', 'C', 'D', 'E', 'F'],
        **{f"{info['b']}_{info['c']}_{info['f']}": [
            info['a'], info['b'], info['c'], info['d'], info['e'], info['f']
        ] for info in [time_series_groups[key] for key in sorted_keys]}
    })

    final_df = pd.concat([header_df, combined_df], ignore_index=True)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    
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
