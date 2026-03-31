import os
import sys
import json
import yt_dlp

# Force UTF-8 encoding for standard output to avoid UnicodeEncodeError in Windows terminal (cp1252)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

video_id = "slvoERjMjuQ"
url = f"https://www.youtube.com/watch?v={video_id}"

# Ensure the directory exists so Windows doesn't throw a folder error
os.makedirs("clean-md", exist_ok=True)
output_filename = f"clean-md/{video_id}_transcript.txt"
temp_sub_file = f"{video_id}.en.json3"

ydl_opts = {
    'skip_download': True,           # We only want subtitles, not the video
    'writesubtitles': True,          # Write manual subtitles
    'writeautomaticsub': True,       # Fallback to auto-generated subtitles
    'subtitleslangs': ['en'],        # Preferred language
    'subtitlesformat': 'json3',      # JSON3 format is much easier to parse clearly into text
    'outtmpl': f'{video_id}.%(ext)s',# Save as video ID for easy cleanup
    'quiet': True,                   # Less clutter in the console
    'no_warnings': True
}

try:
    print(f"Fetching clean text transcript for {video_id} using yt-dlp...")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # This will directly download a .json3 file to disk
        ydl.download([url])
    
    # Read the JSON3 subtitle file downloaded by yt-dlp
    with open(temp_sub_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Combine all the text blocks into one giant string (NO TIMESTAMPS)
    chunks = []
    for event in data.get('events', []):
        for seg in event.get('segs', []):
            text = seg.get('utf8', '')
            if text == '\n':
                chunks.append(' ')
            else:
                chunks.append(text)
                
    # Join into a single clean string without weird spacing
    full_transcript = " ".join("".join(chunks).split())
    
    # Save the clean transcript to a text file
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write(full_transcript)
        
    print(f"✅ Clean transcript successfully saved to {output_filename}")

    # Clean up the downloaded temporary json3 file
    if os.path.exists(temp_sub_file):
        os.remove(temp_sub_file)

except Exception as e:
    print(f"❌ Error: {e}")