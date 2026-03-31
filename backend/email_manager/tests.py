"""
Email Manager API & EML Ingestion Test Suite — Phase 3
Tests the EML parsing pipeline, thread CRUD, and upload endpoint.
"""
import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import mock_open, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from email_manager.models import Email, EmailThread
from email_manager.utils import import_eml_file
from protagonist_manager.models import Protagonist

User = get_user_model()

PAIR_URL = "/api/token/pair"
THREADS_URL = "/api/emails/threads/"
VALID_EMAIL_ADDR = "emailuser@example.com"
VALID_PASSWORD = "StrongPass123!"

# ── Minimal valid EML fixture ─────────────────────────────────────────────────

MINIMAL_EML = b"""\
From: Alice Sender <alice@law.example.com>
To: Bob Recipient <bob@court.example.com>
Cc: charlie@example.com
Subject: Legal Notice Re: Case 2024-001
Date: Mon, 01 Jan 2024 10:00:00 +0000
Message-ID: <legal-notice-unique-001@law.example.com>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

This is the plain-text body of the legal notice.
It contains important evidence information.
"""

MULTIPART_EML = b"""\
From: sender@example.com
To: receiver@example.com
Subject: Multipart Test
Date: Tue, 02 Jan 2024 12:00:00 +0000
Message-ID: <multipart-unique-002@example.com>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset=UTF-8

Plain text body content.
--boundary123
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="evidence.pdf"

(binary attachment data)
--boundary123--
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post_json(client, url, data, token=None):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return client.post(url, data=json.dumps(data), content_type="application/json", **headers)


def _get(client, url, token=None):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return client.get(url, content_type="application/json", **headers)


def _delete(client, url, token=None):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
    return client.delete(url, content_type="application/json", **headers)


def _get_token(client):
    res = _post_json(client, PAIR_URL, {"email": VALID_EMAIL_ADDR, "password": VALID_PASSWORD})
    assert res.status_code == 200, f"Token obtain failed: {res.content}"
    return res.json()["access"]


# ── EML Ingestion Unit Tests ──────────────────────────────────────────────────

class EmlIngestionTest(TestCase):
    """
    Tests the import_eml_file() utility directly.
    File I/O is mocked so no disk writes occur.
    """

    def _upload(self, content: bytes, filename: str = "test.eml"):
        return SimpleUploadedFile(filename, content, content_type="message/rfc822")

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_valid_eml_creates_thread_and_email(self, _mock_file, _mock_dirs):
        """A valid EML must produce exactly one EmailThread and one Email."""
        import_eml_file(self._upload(MINIMAL_EML))
        self.assertEqual(EmailThread.objects.count(), 1)
        self.assertEqual(Email.objects.count(), 1)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_subject_parsed_from_header(self, _mock_file, _mock_dirs):
        """Subject header must be stored on both thread and email."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertEqual(email_obj.subject, "Legal Notice Re: Case 2024-001")
        self.assertEqual(email_obj.thread.subject, "Legal Notice Re: Case 2024-001")

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_sender_parsed_from_header(self, _mock_file, _mock_dirs):
        """From header must be stored in email.sender."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertIn("alice@law.example.com", email_obj.sender)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_recipients_to_parsed_from_header(self, _mock_file, _mock_dirs):
        """To header must be stored in email.recipients_to."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertIn("bob@court.example.com", email_obj.recipients_to)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_date_sent_parsed_from_header(self, _mock_file, _mock_dirs):
        """Date header must be parsed into a datetime on email.date_sent."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertIsNotNone(email_obj.date_sent)
        self.assertEqual(email_obj.date_sent.year, 2024)
        self.assertEqual(email_obj.date_sent.month, 1)
        self.assertEqual(email_obj.date_sent.day, 1)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_message_id_parsed_from_header(self, _mock_file, _mock_dirs):
        """Message-ID must be stored on email.message_id."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertIn("legal-notice-unique-001", email_obj.message_id)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_plain_text_body_extracted(self, _mock_file, _mock_dirs):
        """Plain-text body must be stored in email.body_plain_text."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertIn("plain-text body", email_obj.body_plain_text)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_multipart_eml_body_extracted(self, _mock_file, _mock_dirs):
        """Plain-text part must be extracted from a multipart EML."""
        email_obj = import_eml_file(self._upload(MULTIPART_EML, "multipart.eml"))
        self.assertIn("Plain text body content", email_obj.body_plain_text)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_duplicate_eml_raises_exception(self, _mock_file, _mock_dirs):
        """Uploading the same EML twice must raise an Exception."""
        import_eml_file(self._upload(MINIMAL_EML))
        with self.assertRaises(Exception) as ctx:
            import_eml_file(self._upload(MINIMAL_EML))
        self.assertIn("already exists", str(ctx.exception))

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_eml_linked_to_protagonist(self, _mock_file, _mock_dirs):
        """When protagonist_id is provided, the thread must be linked to that protagonist."""
        protagonist = Protagonist.objects.create(
            first_name="Alice", last_name="Sender", role="Opposing Counsel"
        )
        email_obj = import_eml_file(self._upload(MINIMAL_EML), linked_protagonist=protagonist)
        self.assertEqual(email_obj.thread.protagonist, protagonist)

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_missing_message_id_generates_uuid(self, _mock_file, _mock_dirs):
        """EML without Message-ID must have a UUID-based fallback generated."""
        eml_no_id = b"""\
From: x@example.com
To: y@example.com
Subject: No ID
Date: Mon, 01 Jan 2024 10:00:00 +0000
Content-Type: text/plain

Body text.
"""
        email_obj = import_eml_file(self._upload(eml_no_id, "noid.eml"))
        self.assertTrue(email_obj.message_id.startswith("eml-"))

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_dao_source_set_to_uploaded_eml(self, _mock_file, _mock_dirs):
        """Ingested emails must carry dao_source='uploaded_eml'."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertEqual(email_obj.dao_source, "uploaded_eml")

    @patch("email_manager.utils.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_thread_id_prefixed_with_eml_thread(self, _mock_file, _mock_dirs):
        """Thread.thread_id for EML uploads must start with 'eml-thread-'."""
        email_obj = import_eml_file(self._upload(MINIMAL_EML))
        self.assertTrue(email_obj.thread.thread_id.startswith("eml-thread-"))


# ── Thread API Tests ──────────────────────────────────────────────────────────

class ThreadListAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="emailuser", email=VALID_EMAIL_ADDR, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        protagonist = Protagonist.objects.create(first_name="Marie", last_name="Dupont", role="Witness")
        self.t1 = EmailThread.objects.create(thread_id="thread-001", subject="Re: Contract", protagonist=protagonist)
        self.t2 = EmailThread.objects.create(thread_id="thread-002", subject="Hearing Notice")

    def test_list_requires_auth(self):
        res = _get(self.client, THREADS_URL)
        self.assertEqual(res.status_code, 401)

    def test_list_returns_all_threads(self):
        res = _get(self.client, THREADS_URL, token=self.token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 2)

    def test_list_item_has_required_fields(self):
        res = _get(self.client, THREADS_URL, token=self.token)
        item = res.json()[0]
        for field in ("id", "subject", "saved_at", "updated_at"):
            self.assertIn(field, item, f"Missing field: {field}")

    def test_protagonist_nested_in_list_item(self):
        """The protagonist object must be nested in the thread response (no extra call needed)."""
        res = _get(self.client, THREADS_URL, token=self.token)
        threads_with_protagonist = [t for t in res.json() if t.get("protagonist") is not None]
        self.assertEqual(len(threads_with_protagonist), 1)
        p = threads_with_protagonist[0]["protagonist"]
        self.assertEqual(p["first_name"], "Marie")
        self.assertEqual(p["last_name"], "Dupont")

    def test_protagonist_full_name_resolvable(self):
        """The frontend can construct get_full_name() from first_name + last_name."""
        res = _get(self.client, THREADS_URL, token=self.token)
        p = next(t["protagonist"] for t in res.json() if t.get("protagonist"))
        full_name = f"{p['first_name']} {p.get('last_name') or ''}".strip()
        self.assertEqual(full_name, "Marie Dupont")


class ThreadDetailAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="emailuser", email=VALID_EMAIL_ADDR, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        self.thread = EmailThread.objects.create(thread_id="detail-thread-001", subject="Evidence Thread")
        Email.objects.create(
            thread=self.thread, message_id="msg-001", dao_source="test",
            sender="a@b.com", subject="First", date_sent=datetime(2024, 1, 1, tzinfo=timezone.utc),
            eml_file_path="/tmp/msg-001.eml",
        )
        Email.objects.create(
            thread=self.thread, message_id="msg-002", dao_source="test",
            sender="b@a.com", subject="Second", date_sent=datetime(2024, 1, 2, tzinfo=timezone.utc),
            eml_file_path="/tmp/msg-002.eml",
        )

    def test_detail_returns_thread_and_emails(self):
        res = _get(self.client, f"{THREADS_URL}{self.thread.pk}/", token=self.token)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["id"], self.thread.pk)
        self.assertEqual(len(body["emails"]), 2)

    def test_emails_sorted_by_date_sent(self):
        """Emails must be in chronological order (oldest first)."""
        res = _get(self.client, f"{THREADS_URL}{self.thread.pk}/", token=self.token)
        emails = res.json()["emails"]
        dates = [e["date_sent"] for e in emails]
        self.assertEqual(dates, sorted(dates))

    def test_detail_404_for_missing_thread(self):
        res = _get(self.client, f"{THREADS_URL}99999/", token=self.token)
        self.assertEqual(res.status_code, 404)


class ThreadDeleteAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="emailuser", email=VALID_EMAIL_ADDR, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        self.thread = EmailThread.objects.create(thread_id="del-thread-001", subject="To Be Deleted")
        Email.objects.create(
            thread=self.thread, message_id="del-msg-001", dao_source="test",
            eml_file_path="/tmp/del.eml",
        )

    def test_delete_removes_thread_from_database(self):
        url = f"{THREADS_URL}{self.thread.pk}/"
        res = _delete(self.client, url, token=self.token)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(EmailThread.objects.filter(pk=self.thread.pk).exists())

    def test_delete_cascades_to_emails(self):
        """Deleting a thread must also delete its child Email objects."""
        url = f"{THREADS_URL}{self.thread.pk}/"
        _delete(self.client, url, token=self.token)
        self.assertEqual(Email.objects.filter(thread=self.thread).count(), 0)

    def test_delete_returns_success(self):
        url = f"{THREADS_URL}{self.thread.pk}/"
        res = _delete(self.client, url, token=self.token)
        self.assertEqual(res.json()["success"], True)

    def test_delete_requires_auth(self):
        url = f"{THREADS_URL}{self.thread.pk}/"
        res = _delete(self.client, url)
        self.assertEqual(res.status_code, 401)
