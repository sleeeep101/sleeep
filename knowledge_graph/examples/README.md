# Knowledge Graph — Public Example

`public_graph.json` contains **1,127 paper nodes** and **83,815 semantic relations** extracted from a geography/GIS/remote-sensing reading corpus. All local file paths, note paths, and block content have been redacted (`<LOCAL_PATH>`). The graph preserves:

- Paper-level metadata: title, authors, year, DOI, topics, summary
- Method-level extraction: methods used, transferability notes, credibility assessment
- Entity types: Paper, Method, Dataset, StudyArea, Term, Concept
- Relations: semantic similarity, method-paper links, cross-entity links, innovation links

## Usage

From the workflow root:

```powershell
# Query the bundled graph by keyword or topic
python -m knowledge_graph query "gully erosion" --graph-file knowledge_graph/examples/public_graph.json
python -m knowledge_graph query "RUSLE soil erosion" --graph-file knowledge_graph/examples/public_graph.json

# Coverage statistics
python -m knowledge_graph stats --graph-file knowledge_graph/examples/public_graph.json

# Visualize a subgraph (opens in browser)
python -m knowledge_graph viz "ephemeral gully" --graph-file knowledge_graph/examples/public_graph.json
```

## Privacy

- All `fulltext_path`, `note_path`, and `block_content` fields have been removed.
- Any residual local paths have been replaced with `<LOCAL_PATH>`.
- The default build pipeline (`python -m knowledge_graph build`) never reads Personal-Brain, desktop notes, or contact files unless `--include-private-sources` is explicitly passed.
- See [`knowledge_graph/隐私来源策略.md`](../隐私来源策略.md) for the privacy source policy.

## Building Your Own

```powershell
# Build from academic-workflow paper corpus
python -m knowledge_graph build

# Build including private sources (explicit opt-in)
python -m knowledge_graph build --include-private-sources
```

The bundled graph is a **read-only reference dataset**. To maintain your own research knowledge graph, build from your local paper corpus and keep the resulting `kg_data.json` outside version control.
