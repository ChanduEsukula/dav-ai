"""Offline-only experiment commands; never installs packages or downloads models."""
import argparse
import json
from pathlib import Path
from time import perf_counter

from .corpus import SAMPLE_NDCS, canonical, digest, document_key, external_output, extract_sample, load_corpus, save_corpus
from .embeddings import LocalBGE, MockEmbedder, compatibility
from .evaluation import Annotations, SQLBaseline, evaluate, exact_product
from .index import RetrievalIndex


def write_json(path, value):
    path = external_output(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as output:
        output.write(canonical(value))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check')
    sample = commands.add_parser('sample')
    sample.add_argument('--out', required=True)
    sample.add_argument('--ndcs', nargs='+', default=SAMPLE_NDCS)
    sample.add_argument('--max-chars', type=int, default=750)
    build = commands.add_parser('build')
    build.add_argument('--corpus', required=True)
    build.add_argument('--out', required=True)
    build.add_argument('--embedding', choices=['bge', 'mock'], default='bge')
    build.add_argument('--engine', choices=['faiss', 'numpy-test'], default='faiss')
    build.add_argument('--model-dir')
    query = commands.add_parser('query')
    query.add_argument('--index', required=True)
    query.add_argument('--ndc', required=True)
    query.add_argument('--question', required=True)
    query.add_argument('--model-dir')
    evaluation = commands.add_parser('evaluate')
    evaluation.add_argument('--corpus', required=True)
    evaluation.add_argument('--annotations', default=str(Path(__file__).with_name('questions_v1.json')))
    evaluation.add_argument('--index')
    evaluation.add_argument('--model-dir')
    evaluation.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'check':
            print(json.dumps(compatibility(), indent=2))
        elif args.command == 'sample':
            started = perf_counter()
            corpus = extract_sample(args.ndcs, args.max_chars)
            save_corpus(corpus, args.out)
            print(json.dumps({'passages': len(corpus.chunks), 'documents': len(corpus.documents),
                              'products': len(corpus.products), 'corpus_sha256': digest(corpus.model_dump(mode='json')),
                              'extraction_seconds': perf_counter() - started}))
        elif args.command == 'build':
            corpus = load_corpus(args.corpus)
            if args.embedding == 'bge' and args.engine != 'faiss':
                raise ValueError('Semantic experiment requires FAISS; numpy-test is contract testing only')
            embedder = LocalBGE(args.model_dir or '') if args.embedding == 'bge' else MockEmbedder()
            started = perf_counter()
            index = RetrievalIndex.build(corpus, embedder, engine=args.engine)
            manifest = index.save(args.out)
            print(json.dumps({'index_id': manifest['index_id'], 'semantic': embedder.metadata['semantic'],
                              'build_seconds': perf_counter() - started,
                              'artifact_bytes': sum(p.stat().st_size for p in Path(args.out).iterdir())}))
        elif args.command == 'query':
            index = RetrievalIndex.load(args.index)
            embedder = LocalBGE(args.model_dir or '') if index.metadata['semantic'] else MockEmbedder()
            product = exact_product(index.corpus, args.ndc)
            timings = {}
            hits = index.search(args.question, confirmed_product_id=product.product_id, embedder=embedder, timings=timings)
            chunks = {c.chunk_id: c for c in index.corpus.chunks}
            documents = {document_key(d): d for d in index.corpus.documents}
            def evidence(hit):
                chunk = chunks[hit['chunk_id']]
                document = documents[chunk.document_key]
                source = {key: getattr(document, key) for key in (
                    'product_id', 'formulation_id', 'product_ndcs', 'source_id', 'source_snapshot_date')}
                source.update({key: getattr(document.label, key) for key in (
                    'id', 'label_set_id', 'label_version', 'effective_date', 'selection_status', 'source_record_id', 'source_url')})
                source['release_id'] = document.release.release_id
                return {**hit, **chunk.model_dump(), 'source': source}
            print(json.dumps({'semantic': embedder.metadata['semantic'], 'timings': timings,
                              'hits': [evidence(hit) for hit in hits]}, indent=2))
        elif args.command == 'evaluate':
            corpus = load_corpus(args.corpus)
            annotations = Annotations.model_validate_json(Path(args.annotations).read_bytes())
            native = SQLBaseline(corpus)
            lexical = SQLBaseline(corpus, keyword_sections=True)
            retrievers = {'sql_native_first5': lambda case, _: native.search(case),
                          'sql_keyword_sections': lambda case, _: lexical.search(case)}
            index = None
            if args.index:
                index = RetrievalIndex.load(args.index)
                if not index.metadata['semantic'] or index.engine != 'faiss':
                    raise ValueError('Mock/numpy-test results must not enter the semantic comparison')
                if index.corpus != corpus:
                    raise ValueError('Evaluation corpus differs from indexed corpus')
                embedder = LocalBGE(args.model_dir or '')
                def semantic(case, timings):
                    product = exact_product(corpus, case.ndc)
                    return [hit['chunk_id'] for hit in index.search(case.question,
                        confirmed_product_id=product.product_id, embedder=embedder, timings=timings)]
                retrievers['faiss_bge'] = semantic
            report = evaluate(corpus, annotations, retrievers)
            report.update(corpus_sha256=digest(corpus.model_dump(mode='json')),
                          annotations_sha256=digest(annotations.model_dump(mode='json')),
                          environment=compatibility(),
                          semantic_status='measured' if index else 'not_run_dependencies_or_local_model_not_provisioned',
                          index_bytes=sum(p.stat().st_size for p in Path(args.index).iterdir()) if index else None)
            write_json(args.out, report)
            print(json.dumps({name: value['summary'] for name, value in report['results'].items()}, indent=2))
            print('Semantic status:', report['semantic_status'])
    except (ValueError, OSError, ImportError, KeyError) as exc:
        parser.exit(2, f'Offline experiment stopped: {exc}\n')


if __name__ == '__main__':
    main()
