# Academic Workflow

Publicly shareable scaffolding for geography research workflows: reading, GIS figures, writing, group meetings, topic design, knowledge graphs, and reproducible project setup.

## Start here

1. Use `04_SCI三区论文项目/_project_template` as the starting point for a new reproducible project.
2. Run `python 07_方法与代码库/project_quality_gate.py --project <your-project>` before sharing code or results.
3. Keep your own raw data, personal notes, credentials, generated graph exports, and local research corpus outside version control. The root `.gitignore` covers the workflow's known local locations but does not remove files already tracked by Git.

## Synthetic GIS example

The project template includes a standard-library-only synthetic terrain/erosion example. It contains no local or real research data and is intended only to verify installation and the project structure.

## License

MIT. See `LICENSE`.

## Build a public copy

Local research materials may remain anywhere. For sharing, use `scripts/build_public_release.py` to create a separate, path-screened copy; it never deletes, moves, or rewrites the source directory. Run `--dry-run` first, then provide a non-existent release directory; use its explicit path-redaction option only for the new public copy. See [`scripts/README.md`](scripts/README.md) for the exclusions and commands.

## Attribution

The reproducible-project boundary is informed by [The Turing Way reproducible-project-template](https://github.com/the-turing-way/reproducible-project-template) and [mahesh-panchal/academic-project-template](https://github.com/mahesh-panchal/academic-project-template); the content here was written for this workflow and does not copy their documentation or code.
