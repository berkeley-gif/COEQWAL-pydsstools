from pydsstools.heclib.dss import HecDss
import pandas as pd
import numpy as np
import argparse

def validate_dss_to_csv(dss_file_path, csv_file_path, validate_all=True):
    try:
        # Open the DSS file
        dss = HecDss.Open(dss_file_path)
        
        # Read the CSV file
        print("\nReading CSV file...")
        csv_df = pd.read_csv(csv_file_path, 
                            header=None,
                            dtype=object,
                            na_values=['NaN', '-901'],
                            keep_default_na=True)
        
        # Get the header rows and data rows
        # CSV format: A, B, C, D, E, F, UNITS (7 header rows), then data
        header_df = csv_df.iloc[:7].copy()
        data_df = csv_df.iloc[7:].copy()
        
        # Set column names from first row of header
        data_df.columns = header_df.iloc[1]
        
        # Convert first column to datetime and set as index
        data_df.iloc[:, 0] = pd.to_datetime(data_df.iloc[:, 0])
        data_df.set_index(data_df.iloc[:, 0], inplace=True)
        
        # Get available pathnames from DSS
        available_pathnames = dss.getPathnameList("/*/*/*/*/*/*/")
        
        # Determine which pathnames to check
        if validate_all:
            pathnames_to_check = available_pathnames
        else:
            pathnames_to_check = available_pathnames[:5]
        
        print(f"\nValidating {'all' if validate_all else '5'} paths...")
        print("Processing...", end="", flush=True)
        
        total_validated = 0
        total_mismatches = 0
        mismatch_details = []

        for pathname in pathnames_to_check:
            try:
                dss_data = dss.read_ts(pathname)
                parts = pathname.split('/')
                b_part = parts[2]
                
                matching_columns = [col for col in data_df.columns if b_part == str(col)]
                
                if not matching_columns:
                    continue
                
                dss_df = pd.DataFrame({
                    'DateTime': dss_data.pytimes,
                    'Value': dss_data.values
                })
                dss_df['DateTime'] = pd.to_datetime(dss_df['DateTime'])
                dss_df.set_index('DateTime', inplace=True)
                dss_df['Value'] = dss_df['Value'].replace(-901, np.nan)
                
                for column_name in matching_columns:
                    total_validated += 1
                    print(".", end="", flush=True)
                    
                    comparison = pd.merge(
                        dss_df,
                        data_df[[column_name]],
                        left_index=True,
                        right_index=True,
                        how='inner'
                    )
                    
                    # Convert the column to numeric
                    try:
                        csv_values = pd.to_numeric(comparison[column_name].astype(str), errors='coerce')
                        dss_values = comparison['Value']
                        
                        # Find mismatches
                        mismatches = comparison[
                            ~(
                                (dss_values == csv_values) |
                                (dss_values.isna() & csv_values.isna()) |
                                (np.isclose(dss_values, csv_values, rtol=1e-10, equal_nan=True))
                            )
                        ]
                        
                        if len(mismatches) > 0:
                            total_mismatches += 1
                            mismatch_info = {
                                'pathname': pathname,
                                'column': column_name,
                                'num_mismatches': len(mismatches),
                                'example_mismatch': {
                                    'date': mismatches.index[0],
                                    'dss_value': mismatches['Value'].iloc[0],
                                    'csv_value': csv_values[mismatches.index[0]],
                                    'difference': abs(mismatches['Value'].iloc[0] - csv_values[mismatches.index[0]])
                                }
                            }
                            mismatch_details.append(mismatch_info)
                    
                    except Exception as e:
                        print(f"\nWarning: Error processing column {column_name}: {str(e)}")
                        continue
            
            except Exception as e:
                print(f"\nError with pathname '{pathname}': {str(e)}")
                continue

        # Print final summary
        print("\n\n=== VALIDATION SUMMARY ===")
        print(f"Total paths validated: {total_validated}")
        print(f"Paths with mismatches: {total_mismatches}")
        
        if mismatch_details:
            print("\nMISMATCH DETAILS:")
            print("-----------------")
            for detail in mismatch_details:
                print(f"\nPathname: {detail['pathname']}")
                print(f"Column: {detail['column']}")
                print(f"Number of mismatches: {detail['num_mismatches']}")
                print("Example mismatch:")
                print(f"  Date: {detail['example_mismatch']['date']}")
                print(f"  DSS value: {detail['example_mismatch']['dss_value']}")
                print(f"  CSV value: {detail['example_mismatch']['csv_value']}")
                print(f"  Absolute difference: {detail['example_mismatch']['difference']}")
        else:
            print("\nAll validations passed successfully!")
            
    finally:
        dss.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate DSS to CSV conversion')
    parser.add_argument('--dss', type=str, required=True, help='Path to DSS file')
    parser.add_argument('--csv', type=str, required=True, help='Path to CSV file')
    parser.add_argument('--all', action='store_true', help='Validate all paths instead of just a sample')
    args = parser.parse_args()

    validate_dss_to_csv(args.dss, args.csv, validate_all=args.all)