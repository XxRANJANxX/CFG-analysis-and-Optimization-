import networkx as nx

def build_nx_graph(basic_blocks):
    G = nx.DiGraph()
    
    for block in basic_blocks:
        lines = [f"Block {block.id}"]
        lines.append("-" * 15)
        
        for instr in block.instructions:
            if 'code' in instr:
                # FIX: Escape double quotes so Graphviz doesn't crash
                safe_code = instr['code'].replace('"', '\\"')
                lines.append(safe_code)
        
        label_str = "\\n".join(lines)
        
        G.add_node(block.id, 
                   instrs=block.instructions, 
                   label=f'"{label_str}"', 
                   shape="box",
                   style="filled",
                   fillcolor="whitesmoke")
                   
    for block in basic_blocks:
        for succ in block.successors:
            G.add_edge(block.id, succ.id)
            
    return G