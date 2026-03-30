import os
import re
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db.models import Q  # <--- Important pour capturer les NULLs
from document_manager.models import Document, DocumentSource


class Command(BaseCommand):
    help = 'Lie les fichiers PDF aux Documents en faisant correspondre le nom de fichier au Titre.'

    def add_arguments(self, parser):
        parser.add_argument(
            'source_dir',
            type=str,
            help='Le chemin absolu du dossier contenant vos PDF sources'
        )

    def handle(self, *args, **options):
        source_dir = options['source_dir']

        if not os.path.isdir(source_dir):
            self.stderr.write(self.style.ERROR(f"Dossier introuvable : {source_dir}"))
            return

        self.stdout.write(self.style.SUCCESS(f"🔍 Scan du dossier : {source_dir}"))

        # --- CORRECTION ICI ---
        # On capture NULL (None) OU Vide ('')
        documents_to_link = Document.objects.filter(
            source_type=DocumentSource.REPRODUCED
        ).filter(
            Q(file_source__isnull=True) | Q(file_source='')
        )

        if not documents_to_link.exists():
            self.stdout.write(self.style.WARNING("Aucun document REPRODUCED manquant de fichier source."))
            return

        self.stdout.write(f"Trouvé {documents_to_link.count()} documents à traiter.")

        linked_count = 0
        missing_count = 0

        # Mappage insensible à la casse des fichiers du dossier
        dir_files = {f.lower(): f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))}

        for doc in documents_to_link:
            title = doc.title.strip()

            # Stratégie 1 : Correspondance Exacte
            candidate_1 = f"{title}.pdf".lower()

            # Stratégie 2 : Nettoyage (espaces -> underscores, suppression ponctuation)
            # "L'Affidavit" devient "LAffidavit.pdf" -> attention aux apostrophes qui disparaissent
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
            candidate_2 = f"{safe_title.replace(' ', '_')}.pdf".lower()

            found_filename = None

            if candidate_1 in dir_files:
                found_filename = dir_files[candidate_1]
            elif candidate_2 in dir_files:
                found_filename = dir_files[candidate_2]

            if found_filename:
                full_path = os.path.join(source_dir, found_filename)
                try:
                    with open(full_path, 'rb') as f:
                        doc.file_source.save(found_filename, File(f), save=True)

                    self.stdout.write(self.style.SUCCESS(f"✅ Lié : '{doc.title}' -> {found_filename}"))
                    linked_count += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"❌ Erreur pour '{doc.title}': {e}"))
            else:
                # Affichage pour débogage
                self.stdout.write(self.style.WARNING(f"⚠️  Non trouvé : '{doc.title}'"))
                self.stdout.write(f"    (Cherché : '{candidate_1}' OU '{candidate_2}')")
                missing_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nTraitement terminé."))
        self.stdout.write(f"- Liés avec succès : {linked_count}")
        self.stdout.write(f"- Manquants : {missing_count}")