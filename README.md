# CFG Project

This project builds a Control Flow Graph (CFG) from C programs, runs static analysis, applies compiler-style optimizations, and generates before/after graph visualizations.

It is designed as a compact analysis pipeline for experimenting with:

- CFG construction from C ASTs
- Live variable analysis
- Dead code elimination
- Constant folding and propagation
- Unreachable code removal
- Loop-invariant code motion (LICM)
- Basic taint analysis for simple source-to-sink security checks

## What The Pipeline Does

For each `.c` file under `datasets/`, the pipeline in `main.py` performs:

1. Parse C source with `pycparser`.
2. Build a directed CFG using `networkx`.
3. Save a `BEFORE` CFG image to `output/`.
4. Run live-variable dataflow analysis.
5. Apply optimizations in this order:
	 - constant folding/propagation
	 - loop-invariant code motion
	 - dead code elimination
	 - unreachable code removal
6. Run taint analysis (tracks `scanf` input reaching `printf`).
7. Regenerate labels and save an `AFTER` CFG image.

## Project Structure

```
cfg_project/
|-- main.py
|-- requirements.txt
|-- datasets/
|   |-- codenet/
|   `-- sv_comp/
|-- output/
|-- src/
|   |-- core_parser.py
|   |-- graph_builder.py
|   |-- static_analysis.py
|   |-- optimizer.py
|   `-- bonus_features.py
`-- tests/
		|-- test_parser.py
		`-- test_analysis.py
```

## Module Overview

- `src/core_parser.py`: AST visitor that creates basic blocks and instruction metadata (`def`, `use`, instruction `type`, and `code`).
- `src/graph_builder.py`: Converts basic blocks into a `networkx.DiGraph` with Graphviz-safe labels.
- `src/static_analysis.py`: Live-variable analysis (`in`/`out` sets) over CFG nodes.
- `src/optimizer.py`: Constant folding/propagation, dead code elimination, unreachable code removal, and label refresh.
- `src/bonus_features.py`: Loop analysis/LICM and taint analysis.
- `main.py`: Orchestrates end-to-end processing for all dataset files.

## Requirements

- Python 3.9+
- Graphviz installed on your system (required by `pydot` to write PNG files)

Python dependencies are in `requirements.txt`:

- `pycparser`
- `networkx`
- `pydot`

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

If PNG generation fails, ensure Graphviz is installed and available in your PATH.

## Run

Execute the full pipeline on all C files in `datasets/`:

```bash
python main.py
```

Expected behavior:

- The script discovers `datasets/**/*.c` recursively.
- For each file, it prints progress and taint-analysis warnings (if any).
- It writes two CFG images per input file into `output/`:
	- `<name>_BEFORE.png`
	- `<name>_AFTER.png`

## Testing

Run unit tests:

```bash
python -m unittest discover -s tests -v
```

Current tests cover:

- basic instruction extraction and block generation
- live-variable analysis behavior on a simple CFG

## Notes And Limitations

- The parser targets a simplified subset of C and uses `pycparser` conventions.
- Constant folding uses expression evaluation for arithmetic-like RHS forms and is intentionally lightweight.
- Taint analysis is flow-oriented but simple: it treats `scanf` as a source and `printf` as a sink.
- LICM is implemented for identifiable loop back-edges and is intentionally conservative.

## Example Datasets

The repository includes sample C programs under:

- `datasets/codenet/`
- `datasets/sv_comp/`

These are used by default when you run `main.py`.