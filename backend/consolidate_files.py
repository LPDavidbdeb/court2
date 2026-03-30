import os
import sys
import shutil

# --- Django Setup ---
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')  # Adjust if needed
import django

django.setup()
# --- End Django Setup ---

try:
    from email_manager.models import Email as DjangoEmailModel
except ImportError as e:
    print(f"Error: Could not import the Email model: {e}")
    sys.exit(1)


def consolidate_email_files():
    """
    Moves email files from a nested directory to a primary directory
    and updates the corresponding database records using relative paths.
    """
    # Define the incorrect and correct directory paths relative to the project root
    incorrect_dir_relative = "DL/Email/Email/gmail"
    correct_dir_relative = "DL/Email/gmail"

    # Get absolute paths for file system operations
    project_root = os.getcwd()
    incorrect_dir_abs = os.path.join(project_root, incorrect_dir_relative)
    correct_dir_abs = os.path.join(project_root, correct_dir_relative)

    print("--- File Consolidation Script (Relative Path Mode) ---")
    print(f"Source (incorrect) directory: {incorrect_dir_abs}")
    print(f"Destination (correct) directory: {correct_dir_abs}\n")

    if not os.path.isdir(incorrect_dir_abs):
        print("The incorrect directory does not exist. Nothing to do.")
        return

    os.makedirs(correct_dir_abs, exist_ok=True)

    # --- Step 1: Find records using the RELATIVE path ---
    # THE FIX IS HERE: We query the database using the relative path string.
    records_to_update = DjangoEmailModel.objects.filter(eml_file_path__startswith=incorrect_dir_relative)
    total_to_process = records_to_update.count()

    if total_to_process == 0:
        print("No database records point to the incorrect relative path. All paths seem correct.")
        return

    print(f"Found {total_to_process} records to update.")
    moved_count = 0
    skipped_count = 0

    for db_email in records_to_update:
        # The old path is exactly as it is in the database (relative)
        old_path_relative = db_email.eml_file_path
        old_path_abs = os.path.join(project_root, old_path_relative)  # Create absolute path for file operations

        filename = os.path.basename(old_path_relative)

        # The new path should also be stored in its relative form
        new_path_relative = os.path.join(correct_dir_relative, filename)
        new_path_abs = os.path.join(project_root, new_path_relative)

        print(f"\nProcessing: {filename}")

        if not os.path.exists(old_path_abs):
            print(f"  - WARNING: Source file not found at '{old_path_abs}'. Skipping.")
            skipped_count += 1
            continue

        if os.path.exists(new_path_abs):
            print(f"  - WARNING: A file named '{filename}' already exists in the destination. Skipping move.")
            if db_email.eml_file_path != new_path_relative:
                print("    -> Updating database path to point to existing correct file.")
                db_email.eml_file_path = new_path_relative
                db_email.save()
            skipped_count += 1
            continue

        try:
            # --- Step 2: Move the file using absolute paths ---
            shutil.move(old_path_abs, new_path_abs)
            print(f"  - MOVED: '{filename}' to the correct directory.")

            # --- Step 3: Update the database with the new RELATIVE path ---
            db_email.eml_file_path = new_path_relative
            db_email.save()
            print("  - UPDATED: Database record with new relative path.")
            moved_count += 1

        except Exception as e:
            print(f"  - FAILED: An error occurred while moving '{filename}': {e}")
            skipped_count += 1

    # --- Step 4: Clean up the old directory structure ---
    print("\n--- Cleanup ---")
    try:
        os.rmdir(incorrect_dir_abs)
        print(f"Successfully removed empty directory: {incorrect_dir_abs}")
        parent_dir = os.path.dirname(incorrect_dir_abs)
        if not os.listdir(parent_dir):
            os.rmdir(parent_dir)
            print(f"Successfully removed empty parent directory: {parent_dir}")
    except OSError as e:
        print(f"Could not remove old directories (this is okay if they weren't empty): {e}")

    print("\n--- Consolidation Complete ---")
    print(f"Successfully moved and updated {moved_count} files.")
    print(f"Skipped {skipped_count} files (due to errors or duplicates).")


if __name__ == "__main__":
    consolidate_email_files()