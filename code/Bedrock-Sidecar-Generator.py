import json
import os

def generate_sidecars(master_json_path, output_dir):
    """
    Reads a master JSON catalog of documents and outputs individual 
    AWS Bedrock/Pinecone compliant .md.metadata.json sidecar files.
    """
    
    # Ensure the output directory exists (like your datasimple-processed-md bucket source)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the master metadata file
    try:
        with open(master_json_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: {master_json_path} not found.")
        return

    documents = data.get('documents', [])
    print(f"Found {len(documents)} documents to process...")

    # Iterate through and create individual files
    for doc in documents:
        filename = doc.get('filename')
        attributes = doc.get('metadataAttributes')

        if not filename or not attributes:
            print(f"Skipping malformed entry: {doc}")
            continue

        # AWS Bedrock expects the metadata file to be named [filename].metadata.json
        # E.g., for 'nlp-project.md', the sidecar is 'nlp-project.md.metadata.json'
        sidecar_filename = f"{filename}.metadata.json"
        sidecar_path = os.path.join(output_dir, sidecar_filename)

        # Construct the exact Bedrock-expected JSON format
        bedrock_payload = {
            "metadataAttributes": attributes
        }

        # Write to the individual file
        with open(sidecar_path, 'w') as sidecar_file:
            json.dump(bedrock_payload, sidecar_file, indent=4)
        
        print(f"Created: {sidecar_filename}")

    print("\n✅ Success! All sidecar files are ready to be uploaded to your AWS S3 bucket.")

if __name__ == "__main__":
    # Ensure this points to where your JSON file actually lives
    MASTER_JSON_FILE = r'C:\Users\maxx9\Desktop\DataSimple\01. DataSimple-ChatBot\master_metadata2.json' 
    
    # This MUST be the exact same folder where your .md files were just created
    OUTPUT_DIRECTORY = r'C:\Users\maxx9\Desktop\DataSimple\01. DataSimple-ChatBot\datasimple-processed-md'

    generate_sidecars(MASTER_JSON_FILE, OUTPUT_DIRECTORY)