import pandas as pd

try:
    # Read the CSV files
    df1 = pd.read_csv('f_stop.csv')
    df2 = pd.read_csv('f_normal.csv')
    df3 = pd.read_csv('f_rung_6.csv')
    df4 = pd.read_csv('f_rung_12_5.csv')

    # Concatenate the dataframes
    merged_df = pd.concat([df1, df2, df3, df4], ignore_index=True)

    # Save the merged dataframe to a new CSV file
    output_file = 'merged_data_finalxyyz.csv'
    merged_df.to_csv(output_file, index=False)

    print(f"Files have been merged successfully into {output_file}")
    print(f"Total number of rows in merged file: {len(merged_df)}")
    print(f"Number of rows from f_stop.csv: {len(df1)}")
    print(f"Number of rows from f_normal.csv: {len(df2)}")
    print(f"Number of rows from f_rung_6.csv: {len(df3)}")
    print(f"Number of rows from f_rung_12_5.csv: {len(df4)}")

except FileNotFoundError as e:
    print(f"Error: Could not find one of the input files - {str(e)}")
except pd.errors.EmptyDataError:
    print("Error: One of the CSV files is empty")
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}") 