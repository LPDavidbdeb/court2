import os
import re
import email
from datetime import datetime, timedelta
from dateutil import parser
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.timezone import make_aware

# Importation conditionnelle de pytz
try:
    import pytz
except ImportError:
    pytz = None

from email_manager.models import Email, EmailThread

# ==========================================
# CONFIGURATION
# ==========================================
SOURCE_DIR = os.path.join(settings.BASE_DIR, 'DL', 'zipper_source')
TARGET_DIR = os.path.join(settings.BASE_DIR, 'DL', 'email', 'reconstructed_thread')

FILE_SEQUENCE = [
    'email.eml',  # 1. Louis (Racine)
    'Re%3A.eml',  # 2. Louis (Réponse à Gap 1)
    'Re%3A-2.eml',  # 3. Louis (Réponse à Gap 2)
    'Re%3A-3.eml'  # 4. Louis (Réponse à Gap 3)
]

# --- CORRECTION MANUELLE DES DATES (Format: AAAA-MM-JJ HH:MM) ---
# Ces dates sont en heure locale de Montréal
FIXED_TIMESTAMPS = {
    # Gap 1 (Élise) -> Répondu par Louis dans Re:.eml
    '<9A7642FF-1F09-4EA8-BBE2-4C0FB9BBCA91@gmail.com>': '2013-06-30 07:38:00',

    # Gap 2 (Élise) -> Répondu par Louis dans Re:-2.eml
    '<BCFAAB51-6B90-43C0-A199-9BE9638CBE18@gmail.com>': '2013-06-30 07:57:00',

    # Gap 3 (Élise) -> Répondu par Louis dans Re:-3.eml
    '<CAMpYBfXZ6guNcULAwCDGWTVy6wdgb1k6AiqVqtXF4FTvJGLwKA@mail.gmail.com>': '2013-06-30 08:34:00'
}


class Command(BaseCommand):
    help = 'Reconstruit le fil Chalet Alexia avec des dates forcées pour la cohérence.'

    def handle(self, *args, **options):
        os.makedirs(TARGET_DIR, exist_ok=True)

        # 1. Création du Thread
        thread, created = EmailThread.objects.get_or_create(
            thread_id="reconstructed-chalet-2013-final",
            defaults={'subject': "Re: Chalet Alexia (Final)"}
        )
        self.stdout.write(self.style.SUCCESS(f"Thread : {thread.subject}"))

        # 2. Boucle sur les fichiers
        for filename in FILE_SEQUENCE:
            source_path = os.path.join(SOURCE_DIR, filename)
            if not os.path.exists(source_path):
                continue

            with open(source_path, 'rb') as f:
                raw_content = f.read()
                msg = email.message_from_bytes(raw_content)

            # Sauvegarde physique unique
            safe_filename = f"imported_{filename.replace('%3A', '_').replace(':', '')}"
            final_file_path = os.path.join(TARGET_DIR, safe_filename)
            if not os.path.exists(final_file_path):
                with open(final_file_path, 'wb+') as dest:
                    dest.write(raw_content)

            # --- Métadonnées Louis ---
            louis_meta = {
                'id': msg.get('Message-ID'),
                'date': parser.parse(msg.get('Date')),
                'subject': msg.get('Subject') or "Re: ",
                'sender': msg.get('From'),
                'to': msg.get('To'),
                'parent_id': msg.get('In-Reply-To')
            }

            # Découpage
            full_body = self.get_body(msg)
            split = self.split_email_body(full_body)
            louis_text = split['current_message']
            quote_header = split['header']
            quoted_history = split['history']

            # --- B. Traitement du Gap (Élise) ---
            if louis_meta['parent_id']:
                parent_id = louis_meta['parent_id']

                if not Email.objects.filter(message_id=parent_id).exists():
                    self.stdout.write(f"  [RECONSTRUCTION] Gap Élise : {parent_id}")

                    # 1. Date : On regarde d'abord dans les FIXES, sinon on parse
                    if parent_id in FIXED_TIMESTAMPS:
                        # Conversion de la string forcée en datetime conscient
                        naive_dt = datetime.strptime(FIXED_TIMESTAMPS[parent_id], '%Y-%m-%d %H:%M:%S')
                        gap_date = self.make_montreal_aware(naive_dt)
                        self.stdout.write(f"    -> Date forcée appliquée : {gap_date}")
                    else:
                        # Fallback parsing (ne devrait pas arriver ici)
                        gap_date, _ = self.parse_quote_header(quote_header)

                    # 2. Expéditeur (extrait du header ou défaut)
                    _, gap_sender = self.parse_quote_header(quote_header)
                    if not gap_sender or gap_sender == "Inconnu":
                        gap_sender = "Élise Ayoub <elise.ayoub@gmail.com>"

                    # 3. Corps
                    gap_body = self.clean_quote_marks(self.split_email_body(quoted_history)['current_message'])

                    # 4. Sujet propre (On reprend simplement le sujet de Louis)
                    clean_subject = louis_meta['subject']

                    # Création Élise
                    Email.objects.create(
                        thread=thread,
                        message_id=parent_id,
                        dao_source='reconstructed_fixed',
                        subject=clean_subject,
                        sender=gap_sender,
                        recipients_to=louis_meta['sender'],
                        date_sent=gap_date,
                        body_plain_text=gap_body,
                        eml_file_path=final_file_path
                    )

            # --- C. Traitement Louis ---
            if not Email.objects.filter(message_id=louis_meta['id']).exists():
                self.stdout.write(f"  [IMPORT] Louis : {louis_meta['id']}")
                Email.objects.create(
                    thread=thread,
                    message_id=louis_meta['id'],
                    dao_source='uploaded_anchor',
                    subject=louis_meta['subject'],
                    sender=louis_meta['sender'],
                    recipients_to=louis_meta['to'],
                    date_sent=louis_meta['date'],
                    body_plain_text=louis_text,
                    eml_file_path=final_file_path
                )

    # ==========================================
    # UTILITAIRES
    # ==========================================
    def make_montreal_aware(self, dt):
        """Force un datetime naïf à être America/Montreal."""
        if pytz:
            montreal_tz = pytz.timezone('America/Montreal')
            return montreal_tz.localize(dt)
        else:
            # Fallback GMT-4
            return make_aware(dt, timezone=timezone(timedelta(hours=-4)))

    def get_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
        return msg.get_payload(decode=True).decode('utf-8', errors='ignore')

    def split_email_body(self, text):
        lines = text.splitlines()
        split_idx = -1
        header_line = ""
        for i, line in enumerate(lines):
            line_s = line.strip()
            if (line_s.startswith("On ") and "wrote:" in line_s) or \
                    (line_s.startswith("Le ") and "crit :" in line_s):
                split_idx = i
                header_line = line_s
                break
        if split_idx != -1:
            return {'current_message': "\n".join(lines[:split_idx]).strip(),
                    'header': header_line,
                    'history': "\n".join(lines[split_idx + 1:]).strip()}
        return {'current_message': text, 'header': None, 'history': None}

    def parse_quote_header(self, header):
        if not header: return None, "Inconnu"
        try:
            if "On " in header:
                parts = re.search(r'On\s+(.*?),\s+at\s+(.*?),\s+(.*?)\s+wrote:', header)
                if parts:
                    return None, parts.group(3)  # On ignore la date parsée ici
            if "Le " in header:
                parts = re.search(r'Le\s+(.*?)[,]\s+(.*?)\s+a\s+crit', header)
                if parts:
                    return None, parts.group(2)
        except:
            pass
        return None, "Inconnu"

    def clean_quote_marks(self, text):
        return '\n'.join([re.sub(r'^[\s>]+', '', line) for line in text.splitlines()]).strip()