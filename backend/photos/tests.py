"""
Photo Documents API Test Suite — Phase 2
Tests cover: list, detail, inline description edit, AI analyze, and clear analysis.
The Gemini API call is mocked so tests run without network access.
"""
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from photos.models import PhotoDocument

User = get_user_model()

PAIR_URL = "/api/token/pair"
DOCS_LIST_URL = "/api/photos/documents/"
VALID_EMAIL = "photouser@example.com"
VALID_PASSWORD = "StrongPass123!"


def _post_json(client, url, data, token=None):
    headers = {}
    if token:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **headers,
    )


def _get(client, url, token=None):
    headers = {}
    if token:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.get(url, content_type="application/json", **headers)


def _patch_json(client, url, data, token=None):
    headers = {}
    if token:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.patch(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **headers,
    )


def _delete(client, url, token=None):
    headers = {}
    if token:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.delete(url, content_type="application/json", **headers)


def _get_token(client):
    """Obtain a JWT access token for testing."""
    res = _post_json(client, PAIR_URL, {"email": VALID_EMAIL, "password": VALID_PASSWORD})
    assert res.status_code == 200, f"Token obtain failed: {res.content}"
    return res.json()["access"]


class PhotoDocumentListTest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="photouser", email=VALID_EMAIL, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        PhotoDocument.objects.create(title="Doc Alpha", description="First document")
        PhotoDocument.objects.create(title="Doc Beta", description="Second document")

    def test_list_requires_auth(self):
        """List endpoint must reject unauthenticated requests."""
        res = _get(self.client, DOCS_LIST_URL)
        self.assertEqual(res.status_code, 401)

    def test_list_returns_all_documents(self):
        """Authenticated list must return all documents."""
        res = _get(self.client, DOCS_LIST_URL, token=self.token)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(len(body), 2)

    def test_list_item_has_required_fields(self):
        """Each list item must include id, title, description, photo_count, created_at."""
        res = _get(self.client, DOCS_LIST_URL, token=self.token)
        item = res.json()[0]
        for field in ("id", "title", "description", "photo_count", "created_at"):
            self.assertIn(field, item, f"Missing field: {field}")

    def test_list_pagination_limit(self):
        """Limit query param must restrict the number of returned items."""
        res = _get(self.client, DOCS_LIST_URL + "?limit=1", token=self.token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)


class PhotoDocumentDetailTest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="photouser", email=VALID_EMAIL, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        self.doc = PhotoDocument.objects.create(
            title="Detail Doc",
            description="<p>Some HTML description</p>",
            ai_analysis="Previous analysis",
        )
        self.url = f"/api/photos/documents/{self.doc.pk}/"

    def test_detail_requires_auth(self):
        res = _get(self.client, self.url)
        self.assertEqual(res.status_code, 401)

    def test_detail_returns_correct_document(self):
        res = _get(self.client, self.url, token=self.token)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["id"], self.doc.pk)
        self.assertEqual(body["title"], "Detail Doc")

    def test_detail_has_photos_list(self):
        res = _get(self.client, self.url, token=self.token)
        self.assertIn("photos", res.json())
        self.assertIsInstance(res.json()["photos"], list)

    def test_detail_404_for_missing_document(self):
        res = _get(self.client, "/api/photos/documents/99999/", token=self.token)
        self.assertEqual(res.status_code, 404)


class PhotoDocumentDescriptionUpdateTest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="photouser", email=VALID_EMAIL, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        self.doc = PhotoDocument.objects.create(title="Editable Doc", description="Original")
        self.url = f"/api/photos/documents/{self.doc.pk}/description/"

    def test_patch_updates_description(self):
        new_html = "<p><strong>Updated content</strong></p>"
        res = _patch_json(self.client, self.url, {"description": new_html}, token=self.token)
        self.assertEqual(res.status_code, 200)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.description, new_html)

    def test_patch_requires_auth(self):
        res = _patch_json(self.client, self.url, {"description": "x"})
        self.assertEqual(res.status_code, 401)


class PhotoDocumentAnalyzeTest(TestCase):
    """
    Tests for POST /api/photos/documents/{id}/analyze/
    The Gemini API call is mocked to avoid network access.
    """

    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="photouser", email=VALID_EMAIL, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        self.doc = PhotoDocument.objects.create(title="AI Doc", description="Content to analyze")

    def _analyze_url(self):
        return f"/api/photos/documents/{self.doc.pk}/analyze/"

    def _make_mock_analyze(self):
        """Returns a side_effect function that simulates analyze_document_content."""
        def mock_analyze(document_object, persona_key="forensic_clerk"):
            document_object.ai_analysis = f"Mocked analysis [{persona_key}]"
            document_object.save(update_fields=["ai_analysis"])
            return True
        return mock_analyze

    @patch("photos.api.analyze_document_content")
    def test_analyze_forensic_clerk_persona(self, mock_fn):
        """forensic_clerk persona must be accepted and produce analysis."""
        mock_fn.side_effect = self._make_mock_analyze()
        res = _post_json(self.client, self._analyze_url(), {"persona": "forensic_clerk"}, token=self.token)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("forensic_clerk", body["analysis"])
        _, kwargs = mock_fn.call_args
        self.assertEqual(kwargs.get("persona_key"), "forensic_clerk")

    @patch("photos.api.analyze_document_content")
    def test_analyze_official_scribe_persona(self, mock_fn):
        """official_scribe persona must be accepted and forwarded to the service."""
        mock_fn.side_effect = self._make_mock_analyze()
        res = _post_json(self.client, self._analyze_url(), {"persona": "official_scribe"}, token=self.token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")
        _, kwargs = mock_fn.call_args
        self.assertEqual(kwargs.get("persona_key"), "official_scribe")

    @patch("photos.api.analyze_document_content")
    def test_analyze_summary_clerk_persona(self, mock_fn):
        """summary_clerk persona must be accepted and forwarded to the service."""
        mock_fn.side_effect = self._make_mock_analyze()
        res = _post_json(self.client, self._analyze_url(), {"persona": "summary_clerk"}, token=self.token)
        self.assertEqual(res.status_code, 200)
        _, kwargs = mock_fn.call_args
        self.assertEqual(kwargs.get("persona_key"), "summary_clerk")

    @patch("photos.api.analyze_document_content")
    def test_invalid_persona_falls_back_to_forensic_clerk(self, mock_fn):
        """Unknown persona must silently fall back to 'forensic_clerk'."""
        mock_fn.side_effect = self._make_mock_analyze()
        res = _post_json(self.client, self._analyze_url(), {"persona": "unknown_persona"}, token=self.token)
        self.assertEqual(res.status_code, 200)
        _, kwargs = mock_fn.call_args
        self.assertEqual(kwargs.get("persona_key"), "forensic_clerk")

    @patch("photos.api.analyze_document_content")
    def test_analysis_result_is_persisted_to_database(self, mock_fn):
        """The analysis text must be saved to the PhotoDocument.ai_analysis field."""
        mock_fn.side_effect = self._make_mock_analyze()
        _post_json(self.client, self._analyze_url(), {"persona": "forensic_clerk"}, token=self.token)
        self.doc.refresh_from_db()
        self.assertIn("forensic_clerk", self.doc.ai_analysis)

    def test_analyze_requires_auth(self):
        """Analyze endpoint must reject unauthenticated requests."""
        res = _post_json(self.client, self._analyze_url(), {"persona": "forensic_clerk"})
        self.assertEqual(res.status_code, 401)

    @patch("photos.api.analyze_document_content", return_value=False)
    def test_failed_analysis_returns_error_status(self, _mock_fn):
        """Service failure must return status=error in the response."""
        res = _post_json(self.client, self._analyze_url(), {"persona": "forensic_clerk"}, token=self.token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "error")


class PhotoDocumentClearAnalysisTest(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_user(username="photouser", email=VALID_EMAIL, password=VALID_PASSWORD)
        self.token = _get_token(self.client)
        self.doc = PhotoDocument.objects.create(
            title="Clear Doc",
            ai_analysis="Analysis to be cleared",
        )
        self.url = f"/api/photos/documents/{self.doc.pk}/analyze/"

    def test_delete_clears_analysis_field(self):
        """DELETE must empty the ai_analysis field."""
        res = _delete(self.client, self.url, token=self.token)
        self.assertEqual(res.status_code, 200)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.ai_analysis, "")

    def test_delete_returns_success_status(self):
        res = _delete(self.client, self.url, token=self.token)
        self.assertEqual(res.json()["status"], "success")

    def test_delete_requires_auth(self):
        res = _delete(self.client, self.url)
        self.assertEqual(res.status_code, 401)
