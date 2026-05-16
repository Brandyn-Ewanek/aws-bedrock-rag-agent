import pandas as pd
import glob
import os

def build_master_dataframe(directory_path="../data"):
    # 1. Find all CSV files that match your naming convention
    file_pattern = os.path.join(directory_path, "multi_agent_evaluation_report*.csv")
    file_list = glob.glob(file_pattern)

    # List to hold each individual dataframe
    dfs = []

    for file in file_list:
        try:
            # 2. Read the CSV
            df = pd.read_csv(file)
            
            # 3. Add a column to track which experiment this data came from
            experiment_name = os.path.basename(file).replace('.csv', '').strip()
            df['Experiment_Source'] = experiment_name
            
            # 4. Clean numeric columns (scrubbing '$' and ',' from the cost column)
            cols_to_clean = [
                'Total Latency (s)', 'Input Tokens', 'Output Tokens', 
                'Est. Cost ($)', 'Accuracy', 'Persona', 'Faithfulness'
            ]
            
            for col in cols_to_clean:
                if col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            dfs.append(df)
            print(f"Successfully loaded: {file}")
            
        except Exception as e:
            print(f"Error loading {file}: {e}")

    # 5. Concatenate everything into one master DataFrame
    if dfs:
        master_df = pd.concat(dfs, ignore_index=True)
        print(f"\nSuccess! Combined {len(dfs)} files.")
        print(f"Master DataFrame Shape: {master_df.shape} (Rows, Columns)")
        return master_df
    else:
        print("No matching files found.")
        return pd.DataFrame()

# Execute the function
master_df = build_master_dataframe()

# Optional: Save the combined data to a new CSV file

master_df.to_csv("../data/master_agent_evaluation_report.csv", index=False)
print("\nSaved master report to ../data/master_agent_evaluation_report.csv")

# Optional: View a summary of the combined data grouped by Agent and Experiment
if not master_df.empty:
    summary_cols = ['Total Latency (s)', 'Accuracy', 'Faithfulness', 'Est. Cost ($)']
    print("\n=== Master Summary ===")
    print(master_df.groupby(['Agent', 'Experiment_Source'])[summary_cols].mean().round(4))