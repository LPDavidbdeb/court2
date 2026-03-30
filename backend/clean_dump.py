import json

def clean_dump(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    cleaned_data = []
    for entry in data:
        if entry.get('model') == 'case_manager.producedexhibit':
            if 'fields' in entry and 'public_url' in entry['fields']:
                del entry['fields']['public_url']
        cleaned_data.append(entry)

    with open(output_file, 'w') as f:
        json.dump(cleaned_data, f, indent=2)

if __name__ == "__main__":
    clean_dump('db_dump.json', 'db_dump_cleaned.json')
    print("Cleaned dump saved to db_dump_cleaned.json")
