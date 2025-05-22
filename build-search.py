import json
import os
import base36
import base64
import lzstring  # Import the lzstring library
from pathlib import Path

def process_files():
    # Initialize LZString compressor/decompressor
    lz = lzstring.LZString()

    # Step 1: Check for search.json.lz and initialize low_index
    # Changed from search.json.xz to search.json.lz
    search_file_compressed = Path("search.json.lz")
    if not search_file_compressed.exists():
        search_data = {"index": 1, "items": {}}
        low_index = 1
    else:
        # Decompress using lzstring's decompressFromBase64
        with open(search_file_compressed, "r") as f:
            compressed_data_str = f.read()

        # Decompress the string; it will return None if decompression fails
        decompressed_string = lz.decompressFromBase64(compressed_data_str)

        if decompressed_string is None:
            # Handle cases where decompression fails (e.g., corrupted file or wrong format)
            print(f"Warning: Could not decompress {search_file_compressed}. Starting fresh.")
            search_data = {"index": 1, "items": {}}
            low_index = 1
        else:
            search_data = json.loads(decompressed_string)
            low_index = search_data["index"]

    # Step 2: Collect filenames from images subfolders and find high_index
    high_index = 0
    images_path = Path("images")
    if images_path.exists():
        for subfolder in images_path.iterdir():
            if subfolder.is_dir():
                for subsubfolder in subfolder.iterdir():
                    if subsubfolder.is_dir():
                        for file in subsubfolder.iterdir():
                            if file.is_file():
                                # Convert filename (base36, lowercase) to base10
                                try:
                                    file_index = base36.loads(file.stem.lower())
                                    high_index = max(high_index, file_index)
                                except ValueError:
                                    continue

    # Step 3: Process files from low_index to high_index
    for i in range(low_index, high_index + 1):
        # Convert index to lowercase base36
        base36_name = base36.dumps(i).lower()
        # Create path using first and second characters
        first_char = base36_name[0] if len(base36_name) > 0 else "0"
        second_char = base36_name[1] if len(base36_name) > 1 else "0"
        file_path = f"images/{first_char}/{second_char}/{base36_name}"

        # Read file and extract base64-decoded "p" value
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                p_value = data.get("p")
                if p_value is not None:
                    # Decode base64 p_value
                    decoded_p = base64.b64decode(p_value).decode('utf-8')
                    # Store in items object with base36_name as key
                    search_data["items"][base36_name] = decoded_p
        except (FileNotFoundError, json.JSONDecodeError, KeyError, base64.binascii.Error) as e:
            # print(f"Error processing file {file_path}: {e}") # Uncomment for debugging
            continue

    # Step 4: Update search.json.lz with new index and items
    search_data["index"] = high_index + 1

    # Convert search_data dictionary to a JSON string
    search_data_json_string = json.dumps(search_data)

    # Compress the JSON string using lzstring's compressToBase64
    compressed_data_for_lz = lz.compressToBase64(search_data_json_string)

    # Write the compressed string to search.json.lz
    # Changed from search.json.xz to search.json.lz, and opened in "w" mode for string
    with open("search.json.lz", "w") as f:
        f.write(compressed_data_for_lz)

# Execute the function
process_files()