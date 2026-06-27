from flask import Flask, render_template, jsonify, request
from src.core_parser import CFGBuilder
from src.graph_builder import build_nx_graph
from src.static_analysis import live_variable_analysis
from src.optimizer import (dead_code_elimination, remove_unreachable_code,
                            update_graph_labels, constant_folding_propagation)
from src.bonus_features import loop_invariant_code_motion, taint_analysis

import networkx as nx
from networkx.drawing.nx_pydot import to_pydot
from pycparser import parse_file
import os
import glob
import uuid
import base64
import copy
import traceback
from pathlib import Path

app = Flask(__name__)

BASE_DIR      = os.path.dirname(__file__)
DATASETS_BASE = os.path.join(BASE_DIR, 'datasets')
OUTPUT_DIR    = os.path.join(BASE_DIR, 'output', 'tmp')
os.makedirs(OUTPUT_DIR, exist_ok=True)
FAKE_LIBC_DIR = os.path.join(BASE_DIR, 'fake_libc_include')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_code_string(code_str: str):
    """Write user code to a temp file and parse it with pycparser."""
    tmp_c = os.path.join(OUTPUT_DIR, f'_usr_{uuid.uuid4().hex}.c')
    try:
        with open(tmp_c, 'w', encoding='utf-8') as f:
            f.write(code_str)

        # 1st attempt: no preprocessor (works for simple C without #include)
        try:
            ast = parse_file(tmp_c, use_cpp=False)
        except Exception:
            ast = _parse_with_cpp(tmp_c)

        builder = CFGBuilder()
        builder.visit(ast)
        return builder.blocks
    finally:
        if os.path.exists(tmp_c):
            os.remove(tmp_c)


def _parse_file_path(filepath: str):
    """Parse an existing dataset file."""
    try:
        ast = parse_file(filepath, use_cpp=False)
    except Exception:
        ast = _parse_with_cpp(filepath)
    builder = CFGBuilder()
    builder.visit(ast)
    return builder.blocks


def _parse_with_cpp(filepath: str):
    """Parse a C file through the preprocessor without system headers."""
    cpp_args = ['-nostdinc', f'-I{FAKE_LIBC_DIR}']
    return parse_file(filepath, use_cpp=True, cpp_args=cpp_args)


def _graph_to_b64(G) -> str:
    """Render graph to PNG via pydot/Graphviz and return base64 string."""
    tmp_png = os.path.join(OUTPUT_DIR, f'_g_{uuid.uuid4().hex}.png')
    try:
        pg = to_pydot(G)
        pg.set_graph_defaults(
            bgcolor='white',
            fontcolor='#0f172a',
            color='#94a3b8',
            penwidth='1.0'
        )
        pg.set_node_defaults(
            style='filled',
            fillcolor='#f8fafc',
            fontcolor='#0f172a',
            fontname='Courier',
            fontsize='10',
            color='#334155',
            penwidth='1.3',
            shape='box'
        )
        pg.set_edge_defaults(
            color='#0f172a',
            fontcolor='#0f172a',
            penwidth='1.4',
            arrowsize='0.8',
            arrowhead='normal'
        )
        pg.write_png(tmp_png)
        with open(tmp_png, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    finally:
        if os.path.exists(tmp_png):
            os.remove(tmp_png)


def _s(val):
    """Serialize a set/list to a sorted list for JSON."""
    if val is None:
        return []
    if isinstance(val, set):
        return sorted(val)
    return sorted(val) if val else []


def _capture_instrs(G):
    """Snapshot: {node_id: [code strings]} for diff tracking."""
    return {
        n: [i.get('code', '') for i in G.nodes[n].get('instrs', [])]
        for n in G.nodes
    }


def _diff_instrs(before_snap, after_snap, label):
    """Return list of change dicts between two instruction snapshots."""
    changes = []
    for n in before_snap:
        b_list = before_snap[n]
        a_list = after_snap.get(n, [])
        # Changed lines (same length, different content)
        for bi, ai in zip(b_list, a_list):
            if bi.strip() != ai.strip() and bi.strip() and ai.strip():
                changes.append({'block': n, 'before': bi.strip(), 'after': ai.strip()})
        # Lines that disappeared (dead code / eliminated)
        removed = [x for x in b_list if x not in a_list and x.strip()]
        for r in removed:
            changes.append({'block': n, 'removed': r.strip()})
    return changes


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/datasets')
def api_datasets():
    pattern = os.path.join(DATASETS_BASE, '**', '*.c')
    files = sorted(glob.glob(pattern, recursive=True))
    result = []
    for f in files:
        rel = os.path.relpath(f, DATASETS_BASE).replace('\\', '/')
        category = rel.split('/')[0] if '/' in rel else 'general'
        result.append({
            'path': rel,
            'name': Path(f).stem,
            'category': category,
            'size': os.path.getsize(f),
        })
    return jsonify(result)


@app.route('/api/datasets/<path:filepath>')
def api_dataset_content(filepath):
    full = os.path.join(DATASETS_BASE, filepath.replace('/', os.sep))
    if not os.path.exists(full):
        return jsonify({'error': 'File not found'}), 404
    with open(full, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({'content': content})


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json(force=True)
    code     = data.get('code', '').strip()
    filepath = data.get('filepath', '').strip()   # optional – for dataset files

    if not code and not filepath:
        return jsonify({'success': False, 'error': 'No code or filepath provided'}), 400

    try:
        # ── 1. Parse ──────────────────────────────────────────────────────
        if filepath:
            full = os.path.join(DATASETS_BASE, filepath.replace('/', os.sep))
            blocks = _parse_file_path(full)
        else:
            blocks = _parse_code_string(code)

        G = build_nx_graph(blocks)
        nodes_before = G.number_of_nodes()
        edges_before = G.number_of_edges()
        instrs_before = sum(len(G.nodes[n]['instrs']) for n in G.nodes)

        # ── 2. BEFORE image ───────────────────────────────────────────────
        before_b64 = _graph_to_b64(copy.deepcopy(G))

        # ── 3. Live-variable analysis ─────────────────────────────────────
        G = live_variable_analysis(G)

        live_var_data = []
        for n in sorted(G.nodes):
            nd = G.nodes[n]
            live_var_data.append({
                'block':        n,
                'instructions': [i.get('code', '') for i in nd.get('instrs', [])],
                'use':          _s(nd.get('use')),
                'def':          _s(nd.get('def')),
                'in':           _s(nd.get('in')),
                'out':          _s(nd.get('out')),
            })

        # ── 4. Optimisations (tracked step by step) ───────────────────────
        snap0 = _capture_instrs(G)

        G = constant_folding_propagation(G)
        snap_cf = _capture_instrs(G)

        G = loop_invariant_code_motion(G)
        snap_licm = _capture_instrs(G)

        G = dead_code_elimination(G)
        snap_dce = _capture_instrs(G)

        nodes_pre_unreachable = set(G.nodes)
        G = remove_unreachable_code(G)
        nodes_post_unreachable = set(G.nodes)

        optimizations = {
            'constant_folding': _diff_instrs(snap0,    snap_cf,   'cf'),
            'licm':             _diff_instrs(snap_cf,  snap_licm, 'licm'),
            'dead_code':        _diff_instrs(snap_licm, snap_dce, 'dce'),
            'unreachable_removed': [
                f'Block {n}' for n in sorted(nodes_pre_unreachable - nodes_post_unreachable)
            ],
        }

        # ── 5. Taint analysis ─────────────────────────────────────────────
        taint_warnings = taint_analysis(G)

        # ── 6. AFTER image ────────────────────────────────────────────────
        G = update_graph_labels(G)
        after_b64 = _graph_to_b64(G)

        nodes_after  = G.number_of_nodes()
        edges_after  = G.number_of_edges()
        instrs_after = sum(len(G.nodes[n]['instrs']) for n in G.nodes)

        return jsonify({
            'success':              True,
            'before_image':         before_b64,
            'after_image':          after_b64,
            'live_variable_analysis': live_var_data,
            'optimizations':        optimizations,
            'taint_warnings':       taint_warnings,
            'stats': {
                'nodes_before':      nodes_before,
                'nodes_after':       nodes_after,
                'edges_before':      edges_before,
                'edges_after':       edges_after,
                'instrs_before':     instrs_before,
                'instrs_after':      instrs_after,
                'instrs_eliminated': instrs_before - instrs_after,
                'blocks_removed':    nodes_before - nodes_after,
            },
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error':   str(e),
            'detail':  traceback.format_exc(),
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
