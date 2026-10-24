"""Pluggable embeddings. BGE accepts only an already provisioned local directory."""
import hashlib
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import platform
import re
from typing import Protocol

import numpy as np

QUERY_PREFIX = 'Represent this sentence for searching relevant passages: '


class Embedder(Protocol):
    @property
    def metadata(self) -> dict: ...
    def encode(self, texts: list[str], *, query: bool = False) -> np.ndarray: ...


def compatibility():
    packages = {}
    for module, distribution in [('faiss', 'faiss-cpu'), ('sentence_transformers', 'sentence-transformers'),
                                 ('torch', 'torch'), ('numpy', 'numpy'), ('psutil', 'psutil')]:
        try:
            packages[distribution] = importlib.metadata.version(distribution) if importlib.util.find_spec(module) else None
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = None
    return {'python': platform.python_version(), 'machine': platform.machine(), 'packages': packages,
            'semantic_ready': all(packages[p] for p in ('faiss-cpu', 'sentence-transformers', 'torch'))}


class MockEmbedder:
    """Stable token hashing for contract tests ONLY; not a semantic model/baseline."""
    metadata = {'model': 'mock-token-hash-v1', 'dimension': 64, 'semantic': False,
                'input_template': 'section-newline-text-v1', 'query_prefix': ''}

    def encode(self, texts, *, query=False):
        values = np.zeros((len(texts), 64), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in re.findall(r'[a-z0-9]+', text.lower()) or [text]:
                raw = hashlib.sha256(token.encode()).digest()
                values[row, int.from_bytes(raw[:4], 'big') % 64] += 1 if raw[4] & 1 else -1
            if not np.any(values[row]):
                values[row, 0] = 1
        return values


class LocalBGE:
    def __init__(self, directory):
        directory = Path(directory).expanduser().resolve()
        if not directory.is_dir() or not (directory / 'config.json').is_file():
            raise ValueError('Supply an existing local BGE model directory; downloads are disabled')
        if not compatibility()['semantic_ready']:
            raise RuntimeError('FAISS/sentence-transformers/torch unavailable; no packages installed')
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        from sentence_transformers import SentenceTransformer
        import torch
        torch.manual_seed(0)
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        self.model = SentenceTransformer(str(directory), device='cpu', local_files_only=True, trust_remote_code=False,
                                         model_kwargs={'use_safetensors': True})
        if self.model.get_sentence_embedding_dimension() != 384:
            raise ValueError('Expected BGE-small 384-dimensional embeddings')
        files = hashlib.sha256()
        for path in sorted(p for p in directory.rglob('*') if p.is_file()):
            files.update(str(path.relative_to(directory)).encode())
            with path.open('rb') as source:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    files.update(block)
        self.metadata = {'model': 'BAAI/bge-small-en-v1.5', 'model_files_sha256': files.hexdigest(),
                         'dimension': 384, 'semantic': True, 'device': 'cpu', 'threads': 1,
                         'query_prefix': QUERY_PREFIX, 'input_template': 'section-newline-text-v1',
                         'packages': compatibility()['packages']}

    def encode(self, texts, *, query=False):
        values = [QUERY_PREFIX + text if query else text for text in texts]
        # Never silently truncate a long passage (or question) during encoding.
        lengths = self.model.tokenizer(values, truncation=False, padding=False)['input_ids']
        if any(len(tokens) > min(512, self.model.max_seq_length) for tokens in lengths):
            raise ValueError('BGE token budget exceeded; reduce max_chars or shorten the query')
        return np.asarray(self.model.encode(values, batch_size=16, show_progress_bar=False,
                                            convert_to_numpy=True, normalize_embeddings=False), dtype=np.float32)


def normalize(values, dimension):
    values = np.asarray(values, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != dimension or not np.isfinite(values).all():
        raise ValueError('Invalid embedding shape or non-finite values')
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    if np.any(norms == 0) or not np.isfinite(norms).all():
        raise ValueError('Invalid zero/non-finite embedding norm')
    return np.ascontiguousarray(values / norms, dtype=np.float32)
