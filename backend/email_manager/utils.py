import os
import datetime
import email
import uuid
from dateutil import parser

from django.db import transaction
from django.conf import settings

from DAL.gmailDAO import GmailDAO, ThreadNotFoundError
from DAL.EmailFileDAO import EmlFileDAO
from protagonist_manager.models import Protagonist
from .models import Email, EmailThread

def import_eml_file(eml_file, linked_protagonist=None):
    raw_eml_content = eml_file.read()
    msg = email.message_from_bytes(raw_eml_content)
    subject = msg.get('Subject', '(No Subject)')
    message_id = msg.get('Message-ID')
    if not message_id:
        message_id = f"eml-{uuid.uuid4()}@local.host"

    if Email.objects.filter(message_id=message_id).exists():
        existing_email = Email.objects.get(message_id=message_id)
        raise Exception(f"Email already exists in thread '{existing_email.thread.subject}'.")

    save_dir = os.path.join(settings.BASE_DIR, 'DL', 'email', 'uploaded_eml')
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    eml_filename = f"{timestamp}_{eml_file.name}"
    file_path = os.path.join(save_dir, eml_filename)
    with open(file_path, 'wb+') as destination:
        destination.write(raw_eml_content)

    body_plain_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and 'attachment' not in str(part.get('Content-Disposition')):
                body_plain_text = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                break
    else:
        body_plain_text = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')

    with transaction.atomic():
        new_thread = EmailThread.objects.create(
            thread_id=f"eml-thread-{message_id}",
            protagonist=linked_protagonist,
            subject=subject,
        )
        email_obj = Email.objects.create(
            thread=new_thread,
            message_id=message_id,
            dao_source='uploaded_eml',
            subject=subject,
            sender=msg.get('From'),
            recipients_to=msg.get('To'),
            recipients_cc=msg.get('Cc'),
            recipients_bcc=msg.get('Bcc'),
            date_sent=parser.parse(msg.get('Date')) if msg.get('Date') else None,
            body_plain_text=body_plain_text,
            eml_file_path=file_path,
        )
    return email_obj

def search_gmail(form_data):
    protagonist_id = form_data['protagonist_id']
    manual_participant_email = form_data['manual_participant_email']
    date_sent_str = form_data['date_sent'].strftime('%Y/%m/%d')
    email_excerpt = form_data.get('email_excerpt', '').strip()

    participant_email = manual_participant_email
    selected_protagonist = None
    if protagonist_id:
        try:
            selected_protagonist = Protagonist.objects.get(pk=protagonist_id)
            if selected_protagonist.emails.exists():
                participant_email = selected_protagonist.emails.first().email_address
        except Protagonist.DoesNotExist:
            return {'status': 'error', 'message': 'Selected protagonist not found.'}

    if not participant_email:
        return {'status': 'error', 'message': 'Please select a protagonist or enter an email.'}

    dao = GmailDAO()
    if not dao.connect():
        return {'status': 'error', 'message': 'Could not connect to Gmail API.'}

    all_thread_ids = dao.get_thread_ids_by_participant_and_date(participant_email, date_sent_str)
    if not all_thread_ids:
        return {'status': 'not_found', 'message': 'No email threads found for that participant and date.'}

    saved_thread_ids = set(EmailThread.objects.filter(thread_id__in=all_thread_ids).values_list('thread_id', flat=True))
    new_thread_ids = [tid for tid in all_thread_ids if tid not in saved_thread_ids]

    if not new_thread_ids:
        return {'status': 'not_found', 'message': 'No new, unsaved threads were found. All matching threads for that date have already been saved.'}

    for thread_id in new_thread_ids:
        raw_messages = dao.get_raw_thread_messages(thread_id)
        if not raw_messages: continue

        parsed_messages = [EmlFileDAO.parse_raw_message_data(msg) for msg in raw_messages]
        if not parsed_messages: continue

        email_thread_obj = {
            'id': thread_id,
            'messages': parsed_messages,
            'subject': parsed_messages[0]['headers'].get('Subject', '(No Subject)')
        }

        if not email_excerpt:
            return {
                'status': 'success',
                'thread': email_thread_obj,
                'selected_protagonist': selected_protagonist
            }
        else:
            match_found = any(email_excerpt.lower() in msg.get('body_plain_text', '').lower() for msg in parsed_messages)
            if match_found:
                return {
                    'status': 'success',
                    'thread': email_thread_obj,
                    'selected_protagonist': selected_protagonist
                }

    return {'status': 'not_found', 'message': 'Found new threads, but none contained the specified text.'}

def save_gmail_thread(thread_id, protagonist_id=None):
    if EmailThread.objects.filter(thread_id=thread_id).exists():
        raise Exception(f"Thread (ID: {thread_id}) has already been saved.")

    dao = GmailDAO()
    if not dao.connect():
        raise Exception("Could not connect to Gmail API.")

    raw_messages = dao.get_raw_thread_messages(thread_id)
    if not raw_messages:
        raise ThreadNotFoundError(f"Could not retrieve thread data for ID: {thread_id}.")

    linked_protagonist = Protagonist.objects.filter(pk=protagonist_id).first()

    first_email_data = EmlFileDAO.parse_raw_message_data(raw_messages[0])
    with transaction.atomic():
        new_thread = EmailThread.objects.create(
            thread_id=thread_id,
            protagonist=linked_protagonist,
            subject=first_email_data['headers'].get('Subject', '(No Subject)'),
        )

        for raw_msg in raw_messages:
            email_data = EmlFileDAO.parse_raw_message_data(raw_msg)
            date_sent_dt = parser.parse(email_data['headers'].get('Date')) if email_data['headers'].get('Date') else None

            Email.objects.create(
                thread=new_thread,
                message_id=email_data['id'],
                dao_source='gmail',
                subject=email_data['headers'].get('Subject'),
                sender=email_data['headers'].get('From'),
                recipients_to=email_data['headers'].get('To'),
                recipients_cc=email_data['headers'].get('Cc'),
                recipients_bcc=email_data['headers'].get('Bcc'),
                date_sent=date_sent_dt,
                body_plain_text=email_data['body_plain_text'],
            )
    return new_thread
