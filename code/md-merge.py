import os
import nbformat
from nbconvert import MarkdownExporter

def process_transcripts_and_notebooks(txt_folder, ipynb_folder, output_folder):
    """
    Processes transcripts. If a matching notebook exists, it merges them.
    If no notebook exists, it outputs just the transcript as a Markdown file.
    """
    # Ensure output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Initialize the Markdown exporter
    md_exporter = MarkdownExporter()

    # Get a list of all transcript files
    txt_files = [f for f in os.listdir(txt_folder) if f.endswith('.txt')]
    print(f"Found {len(txt_files)} transcripts to process...\n")

    for txt_filename in txt_files:
        base_name = os.path.splitext(txt_filename)[0]
        
        # Define the corresponding paths
        txt_path = os.path.join(txt_folder, txt_filename)
        ipynb_path = os.path.join(ipynb_folder, f"{base_name}.ipynb")
        output_md_path = os.path.join(output_folder, f"{base_name}.md")

        try:
            # 1. Read the transcript
            with open(txt_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()

            # Create the base Markdown structure
            combined_content = f"# {base_name.replace('-', ' ').title()}\n\n"
            combined_content += f"## Video Transcript\n{transcript_text}\n\n"

            # 2. Check for the notebook
            if os.path.exists(ipynb_path):
                # Notebook exists: Convert and append
                with open(ipynb_path, 'r', encoding='utf-8') as f:
                    notebook_node = nbformat.read(f, as_version=4)
                
                notebook_md, _ = md_exporter.from_notebook_node(notebook_node)
                combined_content += f"## Code Notebook\n{notebook_md}"
                print(f"✅ Merged Transcript + Code: {base_name}.md")
            else:
                # No notebook: Just output the transcript
                print(f"ℹ️ Converted Transcript Only (No Code): {base_name}.md")

            # 3. Save the final .md file
            with open(output_md_path, 'w', encoding='utf-8') as f:
                f.write(combined_content)

        except Exception as e:
            print(f"❌ Error processing {base_name}: {e}")

    print("\n🎉 Processing complete! All files are ready for metadata sidecars.")

if __name__ == "__main__":
    # Using absolute paths (the 'r' before the string handles Windows backslashes safely)
    TXT_FOLDER = r'C:\Users\maxx9\Desktop\DataSimple\01. DataSimple-ChatBot\clean-transcripts'
    IPYNB_FOLDER = r'C:\Users\maxx9\Desktop\DataSimple\01. DataSimple-ChatBot\clean-notebook'
    OUTPUT_FOLDER = r'C:\Users\maxx9\Desktop\DataSimple\01. DataSimple-ChatBot\datasimple-processed-md' 

    process_transcripts_and_notebooks(TXT_FOLDER, IPYNB_FOLDER, OUTPUT_FOLDER)