from ninja import NinjaAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(
    title="Court Headless V2 API",
    version="2.0.0",
    description="Refactored API for Court Monolith using Django Ninja",
)

# Phase 2.2: Add JWT authentication endpoints
api.register_controllers(NinjaJWTDefaultController)

# Delayed imports to prevent circular dependencies
@api.get("/status")
def health_check(request):
    return {"status": "ok", "version": "2.0.0"}

def register_routers():
    from case_manager.api import router as case_router
    from document_manager.api import router as document_router
    from pdf_manager.api import router as pdf_router
    from email_manager.api import router as email_router
    from events.api import router as events_router
    from protagonist_manager.api import router as protagonist_router
    from photos.api import router as photos_router
    from users.api import router as users_router

    api.add_router("/cases", case_router)
    api.add_router("/documents", document_router)
    api.add_router("/pdfs", pdf_router)
    api.add_router("/emails", email_router)
    api.add_router("/events", events_router)
    api.add_router("/protagonists", protagonist_router)
    api.add_router("/photos", photos_router)
    api.add_router("/users", users_router)

register_routers()
