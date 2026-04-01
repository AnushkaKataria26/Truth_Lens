import subprocess
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class TextBundle:
    raw_text: str
    source_language: Optional[str]
    exif_metadata: dict

def extract_text(input_source: str, is_media_path: bool = False) -> TextBundle:
    # Input: raw text string OR media file path
    exif_metadata = {}
    raw_text = ""
    
    if is_media_path:
        # Extract EXIF metadata, embedded captions
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_entries", "format_tags",
                input_source
            ], capture_output=True, text=True, check=True)
            probe_data = json.loads(result.stdout)
            format_tags = probe_data.get("format", {}).get("tags", {})
            exif_metadata = format_tags
            
            # Use comment or title as raw text if available
            raw_text = format_tags.get("comment", format_tags.get("title", ""))
        except Exception:
            pass
    else:
        raw_text = input_source
        
    # Normalize unicode, strip HTML
    import html
    import unicodedata
    import re
    
    # Strip HTML
    clean_text = re.sub(r'<[^>]+>', '', str(raw_text))
    # Normalize unicode
    clean_text = unicodedata.normalize('NFKC', clean_text)
    # Truncate to 2000 chars
    clean_text = clean_text[:2000]
    
    return TextBundle(
        raw_text=clean_text,
        source_language=None, # Mock language detection
        exif_metadata=exif_metadata
    )
