from ninja import Router, Schema
from ninja_jwt.authentication import JWTAuth

router = Router(tags=["Users"])


class UserMeSchema(Schema):
    email: str
    first_name: str
    last_name: str


@router.get("/me", response=UserMeSchema, auth=JWTAuth())
def get_me(request):
    """Returns the authenticated user's profile."""
    u = request.user
    return UserMeSchema(
        email=u.email,
        first_name=u.first_name or "",
        last_name=u.last_name or "",
    )
