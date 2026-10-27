"""Fetch a maintained list of FDA pages; no automatic discovery or generated text."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import httpx

from app.db.pharma.ingestion_run_repository import IngestionRunRepository
from app.db.pharma.safety_repository import SafetyRepository
from app.services.pharma.normalization import normalize_name
from app.services.pharma.safety_records import SOURCES, date

CONFIG = Path(__file__).resolve().parents[2] / 'config/safety_communications.json'


def official_url(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname not in ('www.fda.gov', 'fda.gov') or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Only HTTPS FDA URLs are allowed')
    if not p.path.startswith(('/drugs/', '/safety/')):
        raise ValueError('Expected an official pharmaceutical FDA page')
    return url


class FDAArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.in_heading = False
        self.skipped = 0
        self.title = []
        self.body = []
        self.metadata = {}
        self.json_scripts = []
        self.json_current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.metadata[attrs.get('property') or attrs.get('name', '')] = attrs.get('content', '')
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json_current = []
        if tag == 'main':
            self.in_main = True
        if tag in ('script', 'style', 'nav', 'aside'):
            self.skipped += 1
        if self.in_main and tag == 'h1':
            self.in_heading = True
        if self.in_main and tag in ('p', 'h1', 'h2', 'h3', 'li', 'br', 'div'):
            self.body.append('\n')

    def handle_endtag(self, tag):
        if tag == 'script' and self.json_current is not None:
            self.json_scripts.append(''.join(self.json_current))
            self.json_current = None
        if tag in ('script', 'style', 'nav', 'aside'):
            self.skipped = max(0, self.skipped - 1)
        if tag == 'h1':
            self.in_heading = False
        if tag == 'main':
            self.in_main = False

    def handle_data(self, data):
        if self.json_current is not None:
            self.json_current.append(data)
        if self.in_main and not self.skipped:
            self.body.append(data)
            if self.in_heading:
                self.title.append(data)

    def result(self):
        title = ' '.join(''.join(self.title).split()) or self.metadata.get('og:title')
        body = '\n'.join(' '.join(line.split()) for line in ''.join(self.body).splitlines() if line.strip())
        if not title or len(body) < 100:
            raise ValueError('FDA article content could not be extracted')
        published = self.metadata.get('article:published_time')
        modified = self.metadata.get('article:modified_time')
        for script in self.json_scripts:
            try:
                data = json.loads(script)
                nodes = data if isinstance(data, list) else [data]
                for node in nodes:
                    if isinstance(node, dict):
                        published = published or node.get('datePublished')
                        modified = modified or node.get('dateModified')
            except (ValueError, TypeError):
                pass
        published_date = date(published)
        if published_date is None:
            # FDA prints an explicit "M-D-YYYY FDA Drug Safety Communication" heading.
            match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s+(?:FDA\s+)?Drug Safety Communication', body, re.I)
            if match:
                try:
                    published_date = datetime(int(match[3]), int(match[1]), int(match[2])).date()
                except ValueError:
                    pass
        updated = None
        if modified:
            try:
                updated = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                pass
        return title, body, published_date, updated


class CommunicationClient:
    def __init__(self, http):
        self.http = http

    async def fetch(self, url):
        # Validate every redirect before issuing it; never follow to an arbitrary host.
        for _ in range(5):
            official_url(url)
            response = await self.http.get(url, follow_redirects=False)
            if response.is_redirect:
                url = str(response.url.join(response.headers['location']))
                continue
            response.raise_for_status()
            if 'text/html' not in response.headers.get('content-type', ''):
                raise ValueError('Expected FDA HTML')
            return response.text, str(response.url)
        raise ValueError('Too many redirects')


async def ingest_communications(*, config=CONFIG, client=None, repository=None):
    entries = json.loads(Path(config).read_text())['communications']
    for entry in entries:
        official_url(entry['url'])
        if entry.get('scope') != 'generic' or not entry.get('names'):
            raise ValueError('Each curated communication needs explicit generic context names')
    repository = repository or SafetyRepository()
    drugs = repository.catalog()
    if not drugs:
        raise ValueError('Ingest the NDC catalog first')
    runs = IngestionRunRepository()
    run_id = runs.start(SOURCES['communications'][0], {'drug_ids': [str(d['id']) for d in drugs],
        'urls': [e['url'] for e in entries], 'scope': 'Maintained official-URL collection; generic context, not a finding about a specific NDC.'})
    counts = dict(fetched=0, inserted=0, updated=0, unresolved=0, failed=0)
    coverage = {}
    async def process(fetcher):
        for entry in entries:
            url = entry['url']
            scoped_drugs = [d for d in drugs if any(
                normalize_name(name) in d['normalized_names'] or
                normalize_name(name) in [normalize_name(i) for i in d['active_ingredients']]
                for name in entry['names'])]
            try:
                html, canonical = await fetcher.fetch(url)
                official_url(canonical)
                parser = FDAArticleParser()
                parser.feed(html)
                title, body, published, updated = parser.result()
                links = []
                for name in entry['names']:
                    n = normalize_name(name)
                    if not re.search(r'(?<!\w)' + re.escape(n) + r'(?!\w)', normalize_name(body)):
                        continue
                    # Explicit editorial collection scope allows generic context on multiple products.
                    for d in drugs:
                        if n in d['normalized_names'] or n in [normalize_name(i) for i in d['active_ingredients']]:
                            links.append((d['id'], 'name', name))
                record = dict(title=title, communication_type='FDA pharmaceutical safety communication',
                    published_date=published, body_text=body, source=SOURCES['communications'][0],
                    source_record_id=url, source_url=canonical, source_updated_at=updated,
                    ingestion_run_id=run_id, raw_json={'html': html, 'scope': 'generic context', 'configured_names': entry['names']})
            except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
                counts['failed'] += 1
                coverage[url] = {'status': 'failed', 'error': type(exc).__name__, 'drug_ids': [str(d['id']) for d in scoped_drugs]}
                continue
            counts['fetched'] += 1
            action = repository.upsert('communications', record, links)
            counts[action] += 1
            counts['unresolved'] += not bool(links)
            coverage[url] = {'status': 'succeeded', 'fetched': 1, 'truncated': False,
                             'drug_ids': [str(d['id']) for d in scoped_drugs]}
    try:
        if client is not None:
            await process(client)
        else:
            async with httpx.AsyncClient(timeout=30, headers={'User-Agent': 'DavAI-Portfolio/1.0 (public pharmaceutical source ingestion)'}) as http:
                await process(CommunicationClient(http))
    except Exception as exc:
        runs.finish(run_id, status='failed', counts=counts, coverage=coverage, error_summary=type(exc).__name__)
        raise
    status = 'partial' if counts['failed'] and counts['fetched'] else ('failed' if counts['failed'] else 'succeeded')
    runs.finish(run_id, status=status, counts=counts, coverage=coverage)
    return {'source': SOURCES['communications'][0], 'run_id': str(run_id), 'status': status, 'counts': counts}
