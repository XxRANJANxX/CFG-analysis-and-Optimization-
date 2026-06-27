from src.core_parser import parse_c_file
from src.graph_builder import build_nx_graph
from src.static_analysis import live_variable_analysis
from src.optimizer import dead_code_elimination, remove_unreachable_code, update_graph_labels, constant_folding_propagation
from src.bonus_features import loop_invariant_code_motion, taint_analysis

import networkx as nx
from networkx.drawing.nx_pydot import to_pydot #graph to png converter
import os
import glob
from pathlib import Path

def save_visualizations(G, output_prefix):#Converts a NetworkX graph to a Pydot object and saves it as a PNG image for visualization
    pydot_graph = to_pydot(G) 
    pydot_graph.write_png(f"{output_prefix}.png")

def process_file(input_file):
    """Process a single C file through the entire pipeline."""
    print(f"\n{'='*60}")
    print(f"Processing: {input_file}")
    print(f"{'='*60}")
    
    # Get filename without extension for output naming
    filename = Path(input_file).stem
    
    try:
        # 1. Parse and build graph
        blocks = parse_c_file(input_file)
        G = build_nx_graph(blocks)
        
        # Save before optimization
        save_visualizations(G, f"output/{filename}_BEFORE")
        
        # 2. Analyze
        G = live_variable_analysis(G)
        
        # 3. Optimize (ORDER MATTERS HERE!)
        G = constant_folding_propagation(G)  # Fold constants first
        G = loop_invariant_code_motion(G)    # Hoist loop invariants
        G = dead_code_elimination(G)         # Nuke dead code (including folded vars)
        G = remove_unreachable_code(G)       # Drop disconnected blocks
        
        # 4. Security Scan
        security_warnings = taint_analysis(G)
        print(f"\n--- Taint Analysis Results for {filename} ---")
        if security_warnings:
            for warning in security_warnings:
                print(warning)
        else:
            print("No security vulnerabilities found.")
        print("------------------------------\n")
        
        # 5. Rebuild text labels and save after optimization
        G = update_graph_labels(G)
        save_visualizations(G, f"output/{filename}_AFTER")
        
        print(f"✓ Successfully processed {filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing {input_file}: {e}")
        return False

def main():
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Find all C files in datasets directory recursively
    c_files = glob.glob("datasets/**/*.c", recursive=True)
    
    if not c_files:
        print("No C files found in datasets directory!")
        return
    
    print(f"\nFound {len(c_files)} C files to process\n")
    
    # Process each file
    successful = 0
    for c_file in sorted(c_files):
        if process_file(c_file):
            successful += 1
    
    print(f"\n{'='*60}")
    print(f"Processing Complete: {successful}/{len(c_files)} files succeeded")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()