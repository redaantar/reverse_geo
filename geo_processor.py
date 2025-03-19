import pandas as pd
import os
import argparse
import googlemaps

def reverse_geocode_google(lat, lon, api_key):
    """
    Reverse geocode using Google Maps API
    """
    gmaps = googlemaps.Client(key=api_key)
    try:
        result = gmaps.reverse_geocode((lat, lon))
        if result and len(result) > 0:
            return result[0]['formatted_address']
        else:
            return "No address found"
    except Exception as e:
        print(f"Error with coordinates {lat}, {lon}: {e}")
        return "Error in geocoding"

def clean_coordinates(input_file, output_file=None, delimiter=';'):
    """
    Clean the coordinates CSV file by:
    1. Removing any whitespace in values
    2. Ensuring proper CSV format
    3. Validating latitude and longitude values
    
    Returns the cleaned DataFrame and saves to output_file if provided
    """
    try:
        if delimiter is None:
            with open(input_file, 'r') as f:
                first_line = f.readline().strip()
                if ',' in first_line:
                    delimiter = ','
                elif ';' in first_line:
                    delimiter = ';'
                else:
                    delimiter = ','
        
        df = pd.read_csv(input_file, delimiter=delimiter)
        
        df.columns = [col.strip() for col in df.columns]
        
        if 'Latitude' in df.columns and 'Longitude' in df.columns:
            df['Latitude'] = df['Latitude'].astype(str).str.strip()
            df['Longitude'] = df['Longitude'].astype(str).str.strip()
            
            df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
            df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
            
            valid_mask = (
                (df['Latitude'] >= -90) & (df['Latitude'] <= 90) &
                (df['Longitude'] >= -180) & (df['Longitude'] <= 180)
            )
            
            invalid_rows = df[~valid_mask]
            if not invalid_rows.empty:
                print(f"Warning: Found {len(invalid_rows)} invalid coordinates that were kept but may need review:")
                print(invalid_rows)
            
            if output_file:
                df.to_csv(output_file, index=False)
                print(f"Cleaned coordinates saved to {output_file}")
            
            return df
            
        else:
            print("Error: Expected 'Latitude' and 'Longitude' columns not found")
            return None
            
    except Exception as e:
        print(f"Error processing the file: {e}")
        return None

def process_geocoding(df, output_file, api_key):
    """
    Process geocoding on a DataFrame with Latitude and Longitude columns using Google Maps API
    """
    if 'Address' not in df.columns:
        df['Address'] = None
    
    for index, row in df.iterrows():
        lat = row['Latitude']
        lon = row['Longitude']
        
        print(f"Processing coordinates {lat}, {lon} ({index+1}/{len(df)})")
        address = reverse_geocode_google(lat, lon, api_key)
        df.at[index, 'Address'] = address
    
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")
    return df

def create_sample_file(filename, delimiter=';'):
    """Create a sample coordinates file if needed"""
    with open(filename, 'w') as f:
        f.write(f"Latitude{delimiter}Longitude\n")
        f.write(f"27.340833{delimiter}35.708333\n")
        f.write(f"26.255833{delimiter}36.444444\n")
        f.write(f"28.451389{delimiter}36.504722\n")
        f.write(f"28.396951{delimiter}36.525397\n")
        f.write(f"28.410278{delimiter}36.545278\n")
        f.write(f"28.421136{delimiter}36.565740\n")
        f.write(f"28.356111{delimiter}36.567222\n")
        f.write(f"28.423833{delimiter}36.569083\n")
        f.write(f"28.416944{delimiter}36.582500\n")
    print(f"Created sample file {filename} with the provided data")

def main():
    parser = argparse.ArgumentParser(description='Process and geocode coordinates from a CSV file')
    parser.add_argument('--input', '-i', required=True, help='Input CSV file with coordinates')
    parser.add_argument('--output', '-o', required=True, help='Output CSV file for results')
    parser.add_argument('--cleaned', '-c', help='Optional intermediate file for cleaned coordinates')
    parser.add_argument('--delimiter', '-d', default=None, help='CSV delimiter (auto-detect if not specified)')
    parser.add_argument('--api-key', '-k', required=True, help='Google Maps API key')
    parser.add_argument('--create-sample', '-s', action='store_true', help='Create a sample input file if it doesn\'t exist')
    parser.add_argument('--skip-cleaning', action='store_true', help='Skip cleaning step if file is already cleaned')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        if args.create_sample:
            create_sample_file(args.input, args.delimiter or ';')
        else:
            print(f"Error: Input file {args.input} not found. Use --create-sample to create a sample file.")
            return
    
    is_already_cleaned = False
    if args.skip_cleaning:
        is_already_cleaned = True
    else:
        try:
            with open(args.input, 'r') as f:
                first_lines = [f.readline().strip() for _ in range(3)]
                
            if all(',' in line and ' ' not in line.replace(', ', '') for line in first_lines if line):
                is_already_cleaned = True
                print(f"Detected that input file appears to be already cleaned (comma-delimited, no extra spaces)")
            elif all(';' in line and ' ' not in line.replace('; ', '') for line in first_lines if line):
                is_already_cleaned = True
                print(f"Detected that input file appears to be already cleaned (semicolon-delimited, no extra spaces)")
        except Exception:
            pass
    
    if is_already_cleaned:
        print("Skipping cleaning step as file appears to be already cleaned")
        try:
            with open(args.input, 'r') as f:
                first_line = f.readline().strip()
                if ',' in first_line:
                    detected_delimiter = ','
                elif ';' in first_line:
                    detected_delimiter = ';'
                else:
                    detected_delimiter = ','  # Default
            
            df = pd.read_csv(args.input, delimiter=detected_delimiter)
            process_geocoding(df, args.output, args.api_key)
        except Exception as e:
            print(f"Error reading the cleaned file: {e}")
            print("Attempting to clean the file anyway...")
            cleaned_output = args.cleaned if args.cleaned else None
            cleaned_df = clean_coordinates(args.input, cleaned_output, args.delimiter)
            
            if cleaned_df is not None:
                process_geocoding(cleaned_df, args.output, args.api_key)
            else:
                print("Failed to process coordinates. Check the input file format.")
    else:
        cleaned_output = args.cleaned if args.cleaned else None
        cleaned_df = clean_coordinates(args.input, cleaned_output, args.delimiter)
        
        if cleaned_df is not None:
            process_geocoding(cleaned_df, args.output, args.api_key)
        else:
            print("Failed to process coordinates. Check the input file format.")

if __name__ == "__main__":
    main()