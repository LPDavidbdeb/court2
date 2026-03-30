
from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock

# Import the components we need to test
from .models import Email, EmailThread
from helpers.Email import Email as EmailHelper
from DAL.gmailDAO import GmailDAO
from dateutil import parser

class EmailSavingTestCase(TestCase):
    """
    Tests the process of fetching, saving, and linking an email to ensure
    data integrity is enforced.
    """

    def setUp(self):
        """Set up a dummy email thread for our tests."""
        self.thread = EmailThread.objects.create(thread_id="dummy_thread_123", subject="Test Thread")

    @patch('DAL.gmailDAO.GmailDAO')
    def test_email_creation_saves_path_and_source(self, MockGmailDAO):
        """
        Verify that processing and saving an email record correctly populates
        the mandatory 'eml_file_path' and 'dao_source' fields.
        """
        # 1. --- Setup Mocks ---
        mock_dao_instance = MockGmailDAO.return_value
        fake_gmail_id = "12345abcde"
        fake_raw_message_data = {
            'id': fake_gmail_id,
            'threadId': self.thread.thread_id,
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'Sender <sender@example.com>'},
                    {'name': 'To', 'value': 'Receiver <receiver@example.com>'},
                    {'name': 'Date', 'value': 'Tue, 29 Mar 2022 12:00:00 -0000'},
                    {'name': 'Message-ID', 'value': '<unique-id@mail.gmail.com>'},
                ]
            },
            'snippet': 'This is a test email.'
        }
        mock_dao_instance.get_raw_message.return_value = fake_raw_message_data
        mock_dao_instance.download_raw_eml_file.return_value = True

        # 2. --- Simulate the Business Logic ---
        email_helper = EmailHelper(fake_raw_message_data, mock_dao_instance, source="gmail")
        saved_path = email_helper.save_eml(base_download_dir="DL")

        # Create and save the Django database model
        new_email_record = Email.objects.create(
            thread=self.thread,
            message_id=fake_gmail_id,
            subject=email_helper.headers.get('Subject'),
            sender=email_helper.headers.get('From'),
            date_sent=parser.parse(email_helper.headers.get('Date')),
            dao_source=email_helper.source,
            eml_file_path=saved_path
        )

        # 3. --- Assertions ---
        retrieved_record = Email.objects.get(pk=new_email_record.pk)

        self.assertEqual(retrieved_record.dao_source, "gmail")
        self.assertIsNotNone(retrieved_record.eml_file_path)
        self.assertTrue(retrieved_record.eml_file_path.endswith(".eml"))
        self.assertIn("Test_Subject", retrieved_record.eml_file_path)

        # 4. --- Test Validation Failure --- 
        # This is the corrected test for mandatory fields.
        # The .create() method bypasses validation, so we must instantiate the object
        # and call full_clean() to trigger the validation that blank=False enforces.
        
        invalid_email = Email(
            thread=self.thread,
            message_id="another_fake_id",
            dao_source="",  # blank=False should reject this
            eml_file_path="" # blank=False should reject this
        )

        # Assert that Django's validation layer catches the empty fields
        with self.assertRaises(ValidationError):
            invalid_email.full_clean()

        print("\nUnit test passed: Email model correctly requires dao_source and eml_file_path.")
