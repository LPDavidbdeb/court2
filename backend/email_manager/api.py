from typing import List
from ninja import Router
from .schemas import (
    EmailThreadSchema, 
    EmailThreadDetailSchema, 
    EmailSchema, 
    EmailCreateSchema,
    EmailQuoteSchema
)
from .services import (
    list_threads_service,
    get_thread_service,
    delete_thread_service,
    list_emails_service,
    get_email_service,
    create_email_service,
    update_email_service,
    delete_email_service,
    list_quotes_service
)

router = Router(tags=["Emails"])

@router.get("/threads", response=List[EmailThreadSchema])
def list_threads(request):
    return list_threads_service()

@router.get("/threads/{thread_id}", response=EmailThreadDetailSchema)
def get_thread(request, thread_id: int):
    return get_thread_service(thread_id)

@router.delete("/threads/{thread_id}")
def delete_thread(request, thread_id: int):
    delete_thread_service(thread_id)
    return {"success": True}

@router.get("/emails", response=List[EmailSchema])
def list_emails(request):
    return list_emails_service()

@router.get("/emails/{email_id}", response=EmailSchema)
def get_email(request, email_id: int):
    return get_email_service(email_id)

@router.post("/emails", response=EmailSchema)
def create_email(request, data: EmailCreateSchema):
    return create_email_service(data.dict())

@router.put("/emails/{email_id}", response=EmailSchema)
def update_email(request, email_id: int, data: EmailCreateSchema):
    return update_email_service(email_id, data.dict())

@router.delete("/emails/{email_id}")
def delete_email(request, email_id: int):
    delete_email_service(email_id)
    return {"success": True}

@router.get("/emails/{email_id}/quotes", response=List[EmailQuoteSchema])
def list_email_quotes(request, email_id: int):
    return list_quotes_service(email_id=email_id)
