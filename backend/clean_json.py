# clean_json.py
import sys

input_file = 'datadump.json'
output_file = 'datadump_cleaned.json'

try:
    with open(input_file, 'r', encoding='utf-8') as f_in:
        print(f"Reading from {input_file}...")
        data = f_in.read()

    print("Replacing null characters (\\u0000)...")
    cleaned_data = data.replace('\\u0000', '')

    with open(output_file, 'w', encoding='utf-8') as f_out:
        print(f"Writing cleaned data to {output_file}...")
        f_out.write(cleaned_data)

    print("\\nCleaning complete.")
    print(f"You can now run: python manage.py loaddata {output_file}")

except FileNotFoundError:
    print(f"Error: The file '{input_file}' was not found in the current directory.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)
