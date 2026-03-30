
from dataclasses import dataclass
from typing import Callable, List, Optional, Type

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from ai_services.services import generate_embeddings_batch
from document_manager.models import Statement, Document
from email_manager.models import Quote as EmailQuote, Email
from pdf_manager.models import Quote as PdfQuote, PDFDocument
from events.models import Event
from photos.models import PhotoDocument


@dataclass
class ModelConfig:
    model: Type
    text_getter: Callable[[object], Optional[str]]
    label: str


class Command(BaseCommand):
    help = (
        "Backfill embedding vectors for all evidence sources and fragments."
    )

    def add_arguments(self, parser):
        parser.add_argument("--chunk-size", type=int, default=250)
        parser.add_argument("--batch-size", type=int, default=32)
        parser.add_argument(
            "--only-missing",
            action="store_true",
            default=True,
            help="Process only rows where embedding is NULL (default behavior).",
        )

    def handle(self, *args, **options):
        chunk_size = options["chunk_size"]
        batch_size = options["batch_size"]
        only_missing = options["only_missing"]

        configs = [
            # --- SOURCE MODELS (New) ---
            ModelConfig(
                model=Email,
                text_getter=lambda obj: getattr(obj, "body_plain_text", None),
                label="email_manager.Email",
            ),
            ModelConfig(
                model=Event,
                text_getter=lambda obj: getattr(obj, "explanation", None),
                label="events.Event",
            ),
            ModelConfig(
                model=PDFDocument,
                text_getter=lambda obj: getattr(obj, "ai_analysis", None),
                label="pdf_manager.PDFDocument",
            ),
            ModelConfig(
                model=PhotoDocument,
                text_getter=lambda obj: (getattr(obj, "ai_analysis", "") or getattr(obj, "description", "")),
                label="photos.PhotoDocument",
            ),
            ModelConfig(
                model=Document,
                text_getter=lambda obj: f"{getattr(obj, 'title', '')}\n{getattr(obj, 'solemn_declaration', '')}".strip() or None,
                label="document_manager.Document",
            ),
            # --- FRAGMENT MODELS (Existing) ---
            ModelConfig(
                model=EmailQuote,
                text_getter=lambda obj: getattr(obj, "quote_text", None),
                label="email_manager.Quote",
            ),
            ModelConfig(
                model=PdfQuote,
                text_getter=lambda obj: getattr(obj, "quote_text", None),
                label="pdf_manager.Quote",
            ),
            ModelConfig(
                model=Statement,
                text_getter=lambda obj: getattr(obj, "text", None),
                label="document_manager.Statement",
            ),
        ]

        for cfg in configs:
            self._process_model(
                cfg=cfg,
                chunk_size=chunk_size,
                batch_size=batch_size,
                only_missing=only_missing,
            )

        self.stdout.write(self.style.SUCCESS("Embedding backfill completed."))

    def _process_model(
        self,
        cfg: ModelConfig,
        chunk_size: int,
        batch_size: int,
        only_missing: bool,
    ) -> None:
        qs = cfg.model.objects.all().order_by("pk")
        if only_missing:
            qs = qs.filter(embedding__isnull=True)

        total = qs.count()
        self.stdout.write(f"Processing {cfg.label}: {total} rows")

        buffer: List[object] = []
        pbar = tqdm(total=total, desc=cfg.label, unit="row")

        for obj in qs.iterator(chunk_size=chunk_size):
            buffer.append(obj)
            if len(buffer) >= batch_size:
                self._embed_and_update(cfg, buffer)
                pbar.update(len(buffer))
                buffer.clear()

        if buffer:
            self._embed_and_update(cfg, buffer)
            pbar.update(len(buffer))
            buffer.clear()

        pbar.close()

    def _embed_and_update(self, cfg: ModelConfig, rows: List[object]) -> None:
        texts = [cfg.text_getter(row) for row in rows]
        embeddings = generate_embeddings_batch(texts)

        to_update = []
        for row, emb in zip(rows, embeddings):
            if emb is not None:
                row.embedding = emb
                to_update.append(row)

        if to_update:
            with transaction.atomic():
                cfg.model.objects.bulk_update(to_update, ["embedding"], batch_size=len(to_update))
