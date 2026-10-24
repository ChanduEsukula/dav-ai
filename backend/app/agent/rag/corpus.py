"""Admitted label extraction and lossless, section-aware passage construction."""
from contextlib import closing
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.agent.briefing import LABEL_FIELDS, validate_card
from app.agent.research_contracts import LabelRecord, ReleaseInfo
from app.agent.source_tools import get_drug_label_evidence
from app.db.pharma.release_connection import connect_release, release_database_path, EXPECTED_SHA256
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository

VERSION = 'label-passages-v1'
# Deliberate coverage: same-brand strengths, other drug classes, related
# combination formulations, and an exact product with no admitted label.
SAMPLE_NDCS = ('0002-0152', '0002-0243', '0002-1433', '58151-155',
               '71297-240', '81964-003', '0597-0152', '0009-0029')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)


class Document(Contract):
    product_id: str = Field(min_length=1)
    formulation_id: str = Field(min_length=1)
    product_ndcs: list[str] = Field(min_length=1)
    package_ndcs: list[str]
    brand_names: list[str]
    strength: str | None
    dosage_form: str | None
    routes: list[str]
    active_ingredients: list[str]
    source_id: str = Field(min_length=1)
    source_snapshot_date: str
    release: ReleaseInfo
    label: LabelRecord

    @field_validator('source_snapshot_date')
    @classmethod
    def valid_date(cls, value):
        date.fromisoformat(value)
        return value

    @model_validator(mode='after')
    def valid_sections(self):
        if date.fromisoformat(self.label.effective_date) > date.fromisoformat(self.source_snapshot_date):
            raise ValueError('Label is newer than its source snapshot')
        for field, section in LABEL_FIELDS.items():
            state = self.label.section_states.get(section)
            text = getattr(self.label, field)
            if ((state and state.state == 'READY' and (not text or state.text != text))
                    or (text is not None and (not state or state.state != 'READY'))):
                raise ValueError('Label text must match its admitted READY section')
        return self


class Chunk(Contract):
    chunk_id: str
    document_key: str
    section: str
    ordinal: int = Field(ge=0)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)


def document_key(document):
    # Includes exact product, formulation, label version, provenance and release.
    return digest(document.model_dump(mode='json'))


def chunk_id(key, section, ordinal, start, end, text):
    return digest([VERSION, key, section, ordinal, start, end, text])


def split_section(text, max_chars):
    """Offsets partition the original text exactly, including all whitespace."""
    if not 128 <= max_chars <= 4000:
        raise ValueError('max_chars must be between 128 and 4000')
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            paragraphs = list(re.finditer(r'\n[ \t]*\n', text[start:end]))
            if paragraphs:
                end = start + paragraphs[-1].end()
            else:
                spaces = list(re.finditer(r'\s+', text[start:end]))
                if spaces:
                    end = start + spaces[-1].end()
        yield start, end, text[start:end]
        start = end


def make_chunks(documents, max_chars=750):
    chunks = []
    for document in sorted(documents, key=document_key):
        key = document_key(document)
        for section in LABEL_FIELDS:  # fixed section order, not dictionary input order
            text = getattr(document.label, section)
            if text is None:
                continue
            for ordinal, (start, end, value) in enumerate(split_section(text, max_chars)):
                chunks.append(Chunk(chunk_id=chunk_id(key, section, ordinal, start, end, value),
                                    document_key=key, section=section, ordinal=ordinal,
                                    start=start, end=end, text=value))
    return chunks


class Product(Contract):
    product_id: str
    formulation_id: str
    product_ndcs: list[str]
    brand_names: list[str]
    label_coverage: dict


class Corpus(Contract):
    version: str = VERSION
    release_artifact_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    max_chars: int = Field(ge=128, le=4000)
    products: list[Product] = Field(max_length=50)
    documents: list[Document] = Field(max_length=100)
    chunks: list[Chunk] = Field(max_length=500)

    @model_validator(mode='after')
    def validate_mapping(self):
        if self.version != VERSION:
            raise ValueError('Unsupported corpus version')
        products = {p.product_id: p for p in self.products}
        if len(products) != len(self.products):
            raise ValueError('Duplicate product')
        keys = [document_key(d) for d in self.documents]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate document')
        releases = {d.release.model_dump_json() for d in self.documents}
        if len(releases) > 1:
            raise ValueError('Mixed releases')
        for doc in self.documents:
            product = products.get(doc.product_id)
            if not product or (product.formulation_id, product.product_ndcs) != (doc.formulation_id, doc.product_ndcs):
                raise ValueError('Document product binding mismatch')
        expected = make_chunks(self.documents, self.max_chars)
        if self.chunks != expected:
            raise ValueError('Chunk text, identity, ordering or source mapping mismatch')
        return self


def extract_sample(ndcs=SAMPLE_NDCS, max_chars=750):
    """Uses existing consumer admission and card validation; never raw label search."""
    if not 1 <= len(ndcs) <= 50 or not 128 <= max_chars <= 4000:
        raise ValueError('Bounded sample requires 1–50 NDCs and max_chars between 128 and 4000')
    repo = FrozenPharmaReleaseRepository()
    documents, products = [], []
    for ndc in ndcs:
        candidates = [p for p in repo.search(ndc, limit=100) if ndc in p['product_ndcs']]
        if len(candidates) != 1:
            raise ValueError(f'Offline sample requires one exact stored product for {ndc}')
        product = candidates[0]
        result = get_drug_label_evidence(product['product_id'], repository=repo)
        card = validate_card('labels', 'offline-sample-not-a-session', {}, product, result)
        products.append(Product(product_id=product['product_id'], formulation_id=product['formulation_id'],
                                product_ndcs=product['product_ndcs'], brand_names=product['brand_names'],
                                label_coverage=result['evidence']['coverage']))
        for label in card.records:
            with closing(connect_release()) as con:
                source = con.execute('SELECT source_id FROM labels WHERE label_id=?', (label.id,)).fetchone()
            if source is None:
                raise ValueError('Missing source identifier')
            documents.append(Document(product_id=product['product_id'], formulation_id=product['formulation_id'],
                                      product_ndcs=product['product_ndcs'], package_ndcs=product['package_ndcs'],
                                      strength=product['strength'], dosage_form=product['dosage_form'],
                                      routes=product['routes'], active_ingredients=product['active_ingredients'],
                                      brand_names=product['brand_names'], source_id=source['source_id'],
                                      source_snapshot_date=card.source_snapshot_date, release=card.release, label=label))
    chunks = make_chunks(documents, max_chars)
    if not 200 <= len(chunks) <= 500:
        raise ValueError(f'Sample has {len(chunks)} passages; adjust explicit selection/max_chars for 200–500')
    return Corpus(release_artifact_sha256=EXPECTED_SHA256, max_chars=max_chars, products=sorted(products, key=lambda p: p.product_id),
                  documents=sorted(documents, key=document_key), chunks=chunks)


def external_output(path):
    """Keep derived pharmaceutical text out of the repository and frozen release."""
    path = Path(path).expanduser().resolve()
    repo = Path(__file__).resolve().parents[4]
    if path.is_relative_to(repo) or path.is_relative_to(release_database_path().parent):
        raise ValueError('Artifacts must be outside the repository and frozen release')
    return path


def save_corpus(corpus, path):
    path = external_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(canonical(corpus.model_dump(mode='json')))


def load_corpus(path):
    if Path(path).stat().st_size > 20_000_000:
        raise ValueError('Corpus exceeds the bounded experiment size')
    return Corpus.model_validate_json(Path(path).read_bytes())
