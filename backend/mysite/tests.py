"""
JWT Authentication Test Suite — Account Module Phase 1
Tests the email-based NinjaJWT token endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import Client
import json

User = get_user_model()

TOKEN_PAIR_URL = "/api/token/pair"
TOKEN_REFRESH_URL = "/api/token/refresh"
TOKEN_VERIFY_URL = "/api/token/verify"
STATUS_URL = "/api/status"

VALID_EMAIL = "testuser@example.com"
VALID_PASSWORD = "StrongPass123!"


def _post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")


class JWTObtainTokenTest(TestCase):
    """Tests for POST /api/token/pair"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
        )

    # --- Positive cases ---

    def test_valid_credentials_return_access_and_refresh_tokens(self):
        """Valid email/password must issue both access and refresh JWTs."""
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": VALID_EMAIL, "password": VALID_PASSWORD})
        self.assertEqual(res.status_code, 200, msg=f"Response body: {res.content}")
        body = res.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)

    def test_access_token_is_non_empty_string(self):
        """Issued access token must be a non-empty JWT string."""
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": VALID_EMAIL, "password": VALID_PASSWORD})
        self.assertEqual(res.status_code, 200)
        access = res.json()["access"]
        self.assertIsInstance(access, str)
        self.assertGreater(len(access), 20)
        # A JWT has 3 dot-separated segments
        self.assertEqual(access.count("."), 2, "Access token must be a valid JWT (3 segments)")

    # --- Negative cases ---

    def test_wrong_password_is_rejected(self):
        """Wrong password must be rejected (4xx)."""
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": VALID_EMAIL, "password": "WrongPassword!"})
        self.assertIn(res.status_code, [401, 400])

    def test_nonexistent_user_is_rejected(self):
        """Unknown email must be rejected (4xx)."""
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": "ghost@example.com", "password": "anything"})
        self.assertIn(res.status_code, [401, 400])

    def test_missing_email_field_returns_error(self):
        """Payload missing 'email' must return a validation error."""
        res = _post_json(self.client, TOKEN_PAIR_URL, {"password": VALID_PASSWORD})
        self.assertIn(res.status_code, [400, 422])

    def test_missing_password_field_returns_error(self):
        """Payload missing 'password' must return a validation error."""
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": VALID_EMAIL})
        self.assertIn(res.status_code, [400, 422])

    def test_inactive_user_is_rejected(self):
        """Deactivated user account must be rejected (4xx)."""
        self.user.is_active = False
        self.user.save()
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": VALID_EMAIL, "password": VALID_PASSWORD})
        self.assertIn(res.status_code, [401, 400])


class JWTRefreshTokenTest(TestCase):
    """Tests for POST /api/token/refresh"""

    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username="refreshuser",
            email="refreshuser@example.com",
            password=VALID_PASSWORD,
        )
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": "refreshuser@example.com", "password": VALID_PASSWORD})
        self.assertEqual(res.status_code, 200, msg=f"setUp token obtain failed: {res.content}")
        self.refresh_token = res.json()["refresh"]

    def test_valid_refresh_token_issues_new_access_token(self):
        """A valid refresh token must produce a new access token."""
        res = _post_json(self.client, TOKEN_REFRESH_URL, {"refresh": self.refresh_token})
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())

    def test_invalid_refresh_token_is_rejected(self):
        """A tampered/invalid refresh token must be rejected (4xx)."""
        res = _post_json(self.client, TOKEN_REFRESH_URL, {"refresh": "this.is.not.valid"})
        self.assertIn(res.status_code, [401, 400])


class JWTVerifyTokenTest(TestCase):
    """Tests for POST /api/token/verify"""

    def setUp(self):
        self.client = Client()
        User.objects.create_user(
            username="verifyuser",
            email="verifyuser@example.com",
            password=VALID_PASSWORD,
        )
        res = _post_json(self.client, TOKEN_PAIR_URL, {"email": "verifyuser@example.com", "password": VALID_PASSWORD})
        self.assertEqual(res.status_code, 200)
        self.access_token = res.json()["access"]

    def test_valid_token_verifies_successfully(self):
        """A freshly-issued access token must pass verification."""
        res = _post_json(self.client, TOKEN_VERIFY_URL, {"token": self.access_token})
        self.assertEqual(res.status_code, 200)

    def test_invalid_token_fails_verification(self):
        """A garbage token must fail verification."""
        res = _post_json(self.client, TOKEN_VERIFY_URL, {"token": "garbage.token.value"})
        self.assertIn(res.status_code, [401, 400])


class JWTPublicEndpointTest(TestCase):
    """Tests for public/protected endpoint behaviour."""

    def setUp(self):
        self.client = Client()

    def test_health_check_returns_ok(self):
        """/api/status must return 200 with status=ok (no auth required)."""
        res = self.client.get(STATUS_URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")
