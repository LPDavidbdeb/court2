import os
import sys
import time

# --- Django Setup ---
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings') # Adjust if needed
import django
django.setup()
# --- End Django Setup ---

try:
    # THE FIX: Import GmailDAO first to resolve the circular dependency.
    from DAL.gmailDAO import GmailDAO
    from email_manager.models import Email as DjangoEmailModel
    from helpers.Email import Email as EmailHelper
except ImportError as e:
    print(f"Error: Could not import a required module: {e}")
    print("Please ensure:")
    print("1. This script is in your project's root directory.")
    print("2. The 'DJANGO_SETTINGS_MODULE' points to your correct settings file.")
    print("3. Your app and model names in the import statements are correct.")
    sys.exit(1)


def redownload_and_relink_all():
    """
    Iterates through ALL database records, re-downloads the .eml file from Google
    to a single consistent location, and updates the database path.
    """
    print("--- Step 1: Connecting to Gmail API ---")
    dao = GmailDAO()
    if not dao.connect():
        print("Failed to connect to Gmail API. Aborting.")
        return
    print("Gmail API connected successfully.\n")

    # The single, correct destination for all gmail files.
    # The save_eml method will construct DL/Email/gmail from this.
    correct_base_dir = "DL"

    print(f"--- Step 2: Re-downloading all emails to ensure consistency ---")
    # Get ALL email records from the database.
    all_db_emails = DjangoEmailModel.objects.all()
    total_to_process = all_db_emails.count()

    if total_to_process == 0:
        print("No email records found in the database. Nothing to do.")
        return

    print(f"Found {total_to_process} records to process.")
    success_count = 0
    failed_count = 0

    for db_email in all_db_emails:
        gmail_id = db_email.message_id
        print(f"\nProcessing record for Subject: '{db_email.subject}' (Gmail ID: {gmail_id})")

        try:
            # 1. Fetch the full, raw message data from Google
            raw_message_data = dao.get_raw_message(gmail_id)
            time.sleep(0.1) # Be polite to the API

            if not raw_message_data:
                print("  - FAILED: Could not fetch message data from API.")
                failed_count += 1
                continue

            # 2. Use your existing EmailHelper class to process the data
            email_helper_obj = EmailHelper(raw_message_data, dao, source="gmail")

            # 3. Use your existing save_eml() method to download the file
            #    This ensures all files land in the correct 'DL/Email/gmail' directory.
            saved_file_path = email_helper_obj.save_eml(base_download_dir=correct_base_dir)

            if saved_file_path:
                # 4. Update the database record with the definitive new path
                db_email.eml_file_path = saved_file_path
                db_email.save()
                success_count += 1
                print(f"  - SUCCESS: Synced and linked to {os.path.basename(saved_file_path)}")
            else:
                print("  - FAILED: The save_eml() method did not return a file path.")
                failed_count += 1

        except Exception as e:
            print(f"  - FAILED: An unexpected error occurred: {e}")
            failed_count += 1

    print("\n--- Full Re-sync Complete ---")
    print(f"Successfully synced {success_count} records.")
    print(f"Failed to sync {failed_count} records.")
    print("\nAll database records should now be linked to a file in the correct directory.")
    print("You can now safely delete the old 'DL/Email/Email' directory if it still exists.")


if __name__ == "__main__":
    redownload_and_relink_all()