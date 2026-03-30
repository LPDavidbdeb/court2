from django.shortcuts import redirect
from django.conf import settings

class SuperuserRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define path prefixes that are exempt from the superuser check.
        # All django-allauth URLs are under /accounts/.
        self.exempt_prefixes = [
            '/accounts/',
            # The admin site has its own authentication, but we can exempt it too.
            '/admin/',
            # Exempt the cinematic story URL
            '/histoire/cinematique/',
            # Exempt the public document views
            '/pdf/',
            '/email/',
            '/document/',
        ]

    def __call__(self, request):
        # Check if the request path starts with an exempt prefix.
        if any(request.path.startswith(prefix) for prefix in self.exempt_prefixes):
            return self.get_response(request)

        # If user is not authenticated, redirect to login.
        # We use settings.LOGIN_URL, which defaults to '/accounts/login/'.
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        # If user is authenticated but not a superuser, redirect to login.
        # This effectively blocks them from the site.
        if not request.user.is_superuser:
            return redirect(settings.LOGIN_URL)

        # If the user is a superuser, allow the request to proceed.
        response = self.get_response(request)
        return response
