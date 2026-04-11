import os
import json

# 1. Change this to the exact local path where your .json files are saved
folder_path = r"C:\Users\maxx9\Desktop\DataSimple\01. DataSimple-ChatBot\datasimple-processed-md"

for filename in os.listdir(folder_path):
    if filename.endswith(".metadata.json"):
        filepath = os.path.join(folder_path, filename)
        
        # Open and read the JSON
        with open(filepath, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                continue
                
        # 2. Check if the AWS required 'metadataAttributes' wrapper exists
        if "metadataAttributes" in data:
            attributes = data["metadataAttributes"]
            
            # 3. Flatten lists and nested dictionaries
            for key, value in list(attributes.items()):
                if isinstance(value, list):
                    # Convert a list like ["python", "pandas"] into "python, pandas"
                    attributes[key] = ", ".join(str(v) for v in value)
                elif isinstance(value, dict):
                    # Convert a nested dictionary into a plain string
                    attributes[key] = json.dumps(value)
                    
            # 4. Save the corrected data back to the file
            with open(filepath, 'w') as file:
                json.dump(data, file, indent=4)

print("All metadata files have been flattened and are Bedrock-ready!")