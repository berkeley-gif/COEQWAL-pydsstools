import pandas as pd
import numpy as np
import argparse
import os
from datetime import datetime

def compare_csv_files(ref_path, file_path, tolerance=1e-5, verbose=False):
    """
    Compare two CSV files with DSS-style headers for exact value matches
    
    Args:
        ref_path: Path to reference CSV file
        file_path: Path to comparison CSV file
        tolerance: Numerical tolerance for floating point comparison
        verbose: Print detailed progress information
    """
    print("=" * 70)
    print("CSV TO CSV COMPARISON TOOL")
    print("=" * 70)
    print(f"Reference CSV: {ref_path}")
    print(f"Comparison CSV: {file_path}")
    print(f"Tolerance: {tolerance}")
    print()
    
    # Check file existence
    if not os.path.exists(ref_path):
        print(f"❌ ERROR: Reference file does not exist: {ref_path}")
        return False
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Comparison file does not exist: {file_path}")
        return False
    
    # Read both CSV files
    print("📄 Reading CSV files...")
    try:
        csv1_df = pd.read_csv(ref_path, header=None, dtype=object, na_values=['NaN'], keep_default_na=True)
        csv2_df = pd.read_csv(file_path, header=None, dtype=object, na_values=['NaN'], keep_default_na=True)
    except Exception as e:
        print(f"❌ ERROR: Failed to read CSV files: {e}")
        return False
    
    print(f"✅ Reference file shape: {csv1_df.shape}")
    print(f"✅ Comparison file shape: {csv2_df.shape}")
    
    # Parse headers and data (assuming 7 header rows: A, B, C, D, E, F, UNITS)
    print("\n🔍 Parsing file structures...")
    
    # Extract headers (first 7 rows) and data (remaining rows)
    header1_df = csv1_df.iloc[:7].copy()
    data1_df = csv1_df.iloc[7:].copy()
    
    header2_df = csv2_df.iloc[:7].copy()
    data2_df = csv2_df.iloc[7:].copy()
    
    # Set column names from the header row (row 1 contains the B parts)
    data1_df.columns = header1_df.iloc[1]  # Row B contains the main identifiers
    data2_df.columns = header2_df.iloc[1]
    
    # Convert DateTime columns
    try:
        data1_df.iloc[:, 0] = pd.to_datetime(data1_df.iloc[:, 0])
        data2_df.iloc[:, 0] = pd.to_datetime(data2_df.iloc[:, 0])
        
        data1_df.set_index(data1_df.iloc[:, 0], inplace=True)
        data2_df.set_index(data2_df.iloc[:, 0], inplace=True)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse DateTime columns: {e}")
        return False
    
    # Find overlapping columns (excluding DateTime column)
    cols1 = set(data1_df.columns[1:])  # Skip DateTime column
    cols2 = set(data2_df.columns[1:])
    
    common_columns = cols1.intersection(cols2)
    only_in_file1 = cols1 - cols2
    only_in_file2 = cols2 - cols1
    
    print(f"📊 Columns in reference file: {len(cols1)}")
    print(f"📊 Columns in comparison file: {len(cols2)}")
    print(f"🤝 Common columns: {len(common_columns)}")
    print(f"📋 Only in reference: {len(only_in_file1)}")
    print(f"📋 Only in comparison: {len(only_in_file2)}")
    
    if len(common_columns) == 0:
        print("❌ ERROR: No overlapping columns found!")
        return False
    
    # Show examples of unique columns if any
    if only_in_file1 and verbose:
        print(f"\n📝 Sample columns only in reference: {list(only_in_file1)[:5]}")
    if only_in_file2 and verbose:
        print(f"📝 Sample columns only in comparison: {list(only_in_file2)[:5]}")
    
    # Compare overlapping time periods
    print(f"\n📅 Analyzing time periods...")
    date_range1 = (data1_df.index.min(), data1_df.index.max())
    date_range2 = (data2_df.index.min(), data2_df.index.max())
    
    print(f"📅 Reference time range: {date_range1[0]} to {date_range1[1]}")
    print(f"📅 Comparison time range: {date_range2[0]} to {date_range2[1]}")
    
    # Find overlapping date range
    overlap_start = max(date_range1[0], date_range2[0])
    overlap_end = min(date_range1[1], date_range2[1])
    
    if overlap_start > overlap_end:
        print("❌ ERROR: No overlapping time periods found!")
        return False
    
    print(f"🔗 Overlapping period: {overlap_start} to {overlap_end}")
    
    # Filter to overlapping period
    data1_overlap = data1_df.loc[overlap_start:overlap_end]
    data2_overlap = data2_df.loc[overlap_start:overlap_end]
    
    print(f"📊 Reference rows in overlap: {len(data1_overlap)}")
    print(f"📊 Comparison rows in overlap: {len(data2_overlap)}")
    
    # Perform comparison for each common column
    print(f"\n🔍 Comparing {len(common_columns)} common columns...")
    
    total_mismatches = 0
    mismatch_details = []
    columns_with_mismatches = 0
    
    for i, column in enumerate(sorted(common_columns)):
        if verbose and i % 100 == 0:
            print(f"   Processing column {i+1}/{len(common_columns)}: {column}")
        
        try:
            # Get data for this column from both files
            series1 = data1_overlap[column].copy()
            series2 = data2_overlap[column].copy()
            
            # Convert to numeric, handling NaN values
            series1_numeric = pd.to_numeric(series1, errors='coerce')
            series2_numeric = pd.to_numeric(series2, errors='coerce')
            
            # Find mismatches using multiple criteria
            mismatches_mask = ~(
                (series1_numeric == series2_numeric) |  # Exact equality
                (series1_numeric.isna() & series2_numeric.isna()) |  # Both NaN
                (np.isclose(series1_numeric, series2_numeric, rtol=tolerance, equal_nan=True))  # Within tolerance
            )
            
            mismatch_dates = series1_numeric[mismatches_mask].index
            
            if len(mismatch_dates) > 0:
                columns_with_mismatches += 1
                total_mismatches += len(mismatch_dates)
                
                # Store detailed mismatch info
                first_mismatch_date = mismatch_dates[0]
                mismatch_info = {
                    'column': column,
                    'num_mismatches': len(mismatch_dates),
                    'first_mismatch_date': first_mismatch_date,
                    'reference_value': series1_numeric.loc[first_mismatch_date],
                    'comparison_value': series2_numeric.loc[first_mismatch_date],
                    'sample_dates': list(mismatch_dates[:3])  # First 3 mismatch dates
                }
                
                # Calculate difference if both are numeric
                if not pd.isna(mismatch_info['reference_value']) and not pd.isna(mismatch_info['comparison_value']):
                    mismatch_info['difference'] = abs(mismatch_info['reference_value'] - mismatch_info['comparison_value'])
                else:
                    mismatch_info['difference'] = 'N/A (NaN involved)'
                
                mismatch_details.append(mismatch_info)
        
        except Exception as e:
            print(f"⚠️  Warning: Error processing column '{column}': {e}")
            continue
    
    # Print summary results
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    print(f"Total columns compared: {len(common_columns)}")
    print(f"Columns with mismatches: {columns_with_mismatches}")
    print(f"Total individual mismatches: {total_mismatches}")
    
    if mismatch_details:
        print(f"\nDETAILED MISMATCH REPORT:")
        print("-" * 70)
        
        # Sort by number of mismatches (worst first)
        mismatch_details.sort(key=lambda x: x['num_mismatches'], reverse=True)
        
        for i, detail in enumerate(mismatch_details[:10]):  # Show top 10 worst
            print(f"\n{i+1}. Column: {detail['column']}")
            print(f"   Mismatches: {detail['num_mismatches']}")
            print(f"   First mismatch date: {detail['first_mismatch_date']}")
            print(f"   Reference value: {detail['reference_value']}")
            print(f"   Comparison value: {detail['comparison_value']}")
            print(f"   Difference: {detail['difference']}")
            if len(detail['sample_dates']) > 1:
                print(f"   Sample mismatch dates: {detail['sample_dates']}")
        
        if len(mismatch_details) > 10:
            print(f"\n... and {len(mismatch_details) - 10} more columns with mismatches")
        
        print(f"\n❌ RESULT: Files do NOT match exactly")
        return False
    else:
        print(f"\n✅ RESULT: All overlapping values match perfectly!")
        print(f"✅ Validated {len(common_columns)} columns across {len(data1_overlap)} time periods")
        return True

def main():
    parser = argparse.ArgumentParser(description='Compare two CSV files for exact value matches')
    parser.add_argument('--ref', type=str, required=True, help='Path to reference CSV file')
    parser.add_argument('--file', type=str, required=True, help='Path to comparison CSV file') 
    parser.add_argument('--tolerance', type=float, default=1e-5, help='Numerical tolerance for comparison (default: 1e-5, suitable for engineering data)')
    parser.add_argument('--verbose', action='store_true', help='Print detailed progress information')
    
    args = parser.parse_args()
    
    success = compare_csv_files(args.ref, args.file, args.tolerance, args.verbose)
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main() 