"""Small exact product-filtered cosine index, without mutable serving APIs."""
import hashlib
import io
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .corpus import Corpus, LABEL_FIELDS, canonical, digest, document_key, external_output
from .embeddings import Embedder, normalize

INDEX_VERSION = 'product-flat-ip-v1'


class RetrievalIndex:
    def __init__(self, corpus: Corpus, vectors, embedding_metadata, *, engine='faiss'):
        # Revalidate mutable nested metadata before trusting the positional mapping.
        self.corpus = Corpus.model_validate_json(corpus.model_dump_json())
        self.metadata = dict(embedding_metadata)
        if (type(self.metadata.get('dimension')) is not int or not 1 <= self.metadata['dimension'] <= 4096
                or not isinstance(self.metadata.get('model'), str) or not self.metadata['model']
                or type(self.metadata.get('semantic')) is not bool
                or self.metadata.get('input_template') != 'section-newline-text-v1'):
            raise ValueError('Invalid embedding metadata')
        self.vectors = np.asarray(vectors)
        if (self.vectors.shape != (len(corpus.chunks), self.metadata['dimension'])
                or self.vectors.dtype != np.float32 or not np.isfinite(self.vectors).all()
                or not np.allclose(np.linalg.norm(self.vectors, axis=1), 1, atol=1e-5)):
            raise ValueError('Invalid normalized index vectors or mapping length')
        self.vectors.flags.writeable = False
        if engine not in ('faiss', 'numpy-test'):
            raise ValueError('Unknown engine')
        self.engine = engine
        self._faiss = None
        if engine == 'faiss':
            import faiss
            faiss.omp_set_num_threads(1)
            self._faiss = faiss
        self.engine_version = self._faiss.__version__ if self._faiss else np.__version__
        documents = {document_key(d): d for d in corpus.documents}
        self._products = {p.product_id: p for p in corpus.products}
        self._rows = {}
        for row, chunk in enumerate(corpus.chunks):
            self._rows.setdefault(documents[chunk.document_key].product_id, []).append(row)
        self._indexes = {}

    @classmethod
    def build(cls, corpus, embedder: Embedder, *, engine='faiss'):
        inputs = [chunk.section + '\n' + chunk.text for chunk in corpus.chunks]
        dimension = embedder.metadata['dimension']
        vectors = normalize(embedder.encode(inputs), dimension) if inputs else np.empty((0, dimension), dtype=np.float32)
        return cls(corpus, vectors, embedder.metadata, engine=engine)

    def search(self, question, *, confirmed_product_id, embedder: Embedder, k=5, timings=None, sections=None):
        """Offline evaluation supplies an exact ID, NEVER a name or model-selected ID.

        This is not a session authorization API. No HTTP endpoint calls it.
        """
        if confirmed_product_id not in self._products:
            raise ValueError('Product was not explicitly included in the sample')
        if type(k) is not int or not 1 <= k <= 100 or not isinstance(question, str) or not question.strip():
            raise ValueError('Invalid query or k')
        if embedder.metadata != self.metadata:
            raise ValueError('Query embedder does not match the indexed model/version')
        rows = self._rows.get(confirmed_product_id, [])
        cache_key = confirmed_product_id
        if sections is not None:
            if (not isinstance(sections, (tuple, list)) or not sections
                    or any(section not in LABEL_FIELDS for section in sections)
                    or len(set(sections)) != len(sections)):
                raise ValueError('Invalid explicit section filter')
            cache_key = (confirmed_product_id, tuple(sorted(sections)))
            rows = [row for row in rows if self.corpus.chunks[row].section in sections]
        if not rows:
            if timings is not None:
                timings.update(query_embedding_seconds=0.0, ranking_seconds=0.0)
            return []
        started = perf_counter()
        query = normalize(embedder.encode([question], query=True), self.metadata['dimension'])
        encoded = perf_counter()
        # Product membership is selected BEFORE vector ranking. Do not retrieve
        # global top-k and discard foreign products: that loses valid evidence.
        if self.engine == 'faiss':
            if cache_key not in self._indexes:
                product_index = self._faiss.IndexFlatIP(self.metadata['dimension'])
                product_index.add(np.ascontiguousarray(self.vectors[rows]))
                self._indexes[cache_key] = product_index
            scores, positions = self._indexes[cache_key].search(query, len(rows))
            ranked = [(rows[int(pos)], float(score)) for pos, score in zip(positions[0], scores[0])]
        else:
            ranked = list(zip(rows, (self.vectors[rows] @ query[0]).tolist()))
        # All eligible passages are scored; chunk ID supplies a stable tie-break.
        ranked.sort(key=lambda pair: (-pair[1], self.corpus.chunks[pair[0]].chunk_id))
        if timings is not None:
            timings.update(query_embedding_seconds=encoded - started, ranking_seconds=perf_counter() - encoded)
        return [{'chunk_id': self.corpus.chunks[row].chunk_id, 'score': score} for row, score in ranked[:k]]

    def save(self, directory):
        directory = external_output(directory)
        if directory.exists():
            raise FileExistsError('Refusing to overwrite an existing index')
        corpus = canonical(self.corpus.model_dump(mode='json'))
        stream = io.BytesIO()
        np.save(stream, self.vectors, allow_pickle=False)
        vectors = stream.getvalue()
        description = {'version': INDEX_VERSION, 'engine': self.engine, 'embedding': self.metadata,
                       'engine_version': self.engine_version,
                       'numpy_version': np.__version__,
                       'corpus_sha256': hashlib.sha256(corpus).hexdigest(),
                       'vectors_sha256': hashlib.sha256(vectors).hexdigest()}
        description['index_id'] = digest(description)
        directory.mkdir(parents=True)
        for name, data in [('corpus.json', corpus), ('vectors.npy', vectors), ('manifest.json', canonical(description))]:
            with (directory / name).open('xb') as output:
                output.write(data)
            (directory / name).chmod(0o444)
        return description

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        if (directory / 'manifest.json').stat().st_size > 1_000_000:
            raise ValueError('Index manifest exceeds experiment bounds')
        manifest = json.loads((directory / 'manifest.json').read_bytes())
        expected_keys = {'version', 'engine', 'engine_version', 'embedding', 'numpy_version',
                         'corpus_sha256', 'vectors_sha256', 'index_id'}
        if (not isinstance(manifest, dict) or set(manifest) != expected_keys
                or not isinstance(manifest.get('embedding'), dict)
                or manifest.get('version') != INDEX_VERSION or manifest.get('index_id') != digest(
                {k: v for k, v in manifest.items() if k != 'index_id'})):
            raise ValueError('Invalid index manifest/version')
        for name, key in [('corpus.json', 'corpus_sha256'), ('vectors.npy', 'vectors_sha256')]:
            path = directory / name
            if path.stat().st_size > 20_000_000 or hashlib.sha256(path.read_bytes()).hexdigest() != manifest[key]:
                raise ValueError('Index artifact checksum/size mismatch')
        corpus = Corpus.model_validate_json((directory / 'corpus.json').read_bytes())
        # Read-only portable vectors, not pickle or an untrusted FAISS binary.
        # Each exact product's IndexFlatIP is reconstructed lazily on first query.
        vectors = np.load(directory / 'vectors.npy', mmap_mode='r', allow_pickle=False)
        index = cls(corpus, vectors, manifest['embedding'], engine=manifest['engine'])
        if manifest.get('engine_version') != index.engine_version:
            raise ValueError('Index engine version differs from recorded build')
        return index
