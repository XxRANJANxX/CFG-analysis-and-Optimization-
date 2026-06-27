import networkx as nx
import re

def constant_folding_propagation(G):
    for n in G.nodes:
        constants = {}  # Tracks {variable_name: constant_value}
        
        for instr in G.nodes[n]['instrs']:
            if instr['type'] == 'assign':
                code_str = instr.get('code', '')
                
                if '=' in code_str:
                    lhs, rhs = code_str.split('=', 1)
                    rhs = rhs.strip().rstrip(';')
                    
                    # 1. Constant Propagation: Replace known variables in the RHS
                    for var, val in constants.items():
                        # Regex \b ensures we only match whole words 
                        rhs = re.sub(rf'\b{var}\b', str(val), rhs)
                        
                    # 2. Constant Folding: Safely evaluate the math
                    try:
                        # Evaluates basic math like '42 + 8'
                        folded_val = eval(rhs, {"__builtins__": None}, {})
                        if isinstance(folded_val, (int, float)):
                            rhs = str(folded_val)
                            # Store for future propagation
                            constants[instr['def']] = folded_val 
                    except Exception:
                        # If it's not math, check if it's just a raw number
                        if rhs.isdigit():
                            constants[instr['def']] = int(rhs)
                        else:
                            constants.pop(instr['def'], None)
                            
                    # Update the C code string for the visual graph
                    instr['code'] = f"{lhs}= {rhs};"
                    
            elif instr['type'] == 'return':
                code_str = instr.get('code', '')
                ret_expr = code_str.replace('return ', '').rstrip(';')
                
                # Propagate constants into the return statement
                for var, val in constants.items():
                    ret_expr = re.sub(rf'\b{var}\b', str(val), ret_expr)
                
                # Fold the return statement if possible
                try:
                    folded_val = eval(ret_expr, {"__builtins__": None}, {})
                    ret_expr = str(folded_val)
                except:
                    pass
                    
                instr['code'] = f"return {ret_expr};"
                
    return G

# ... keep dead_code_elimination and update_graph_labels as they are ...
def dead_code_elimination(G):
    for n in G.nodes:
        # Start with the variables live at the EXIT of this block
        current_live = G.nodes[n].get('out', set()).copy()
        optimized_instrs = []
        
        # Traverse instructions backwards to track local liveness correctly
        for instr in reversed(G.nodes[n]['instrs']):
            if instr['type'] == 'assign':
                # If the variable being defined is NOT in our live set, it's dead. Drop it.
                if instr.get('def') in current_live:
                    optimized_instrs.insert(0, instr)
                    # Once we hit the definition, it's no longer 'live' above this line
                    current_live.discard(instr.get('def'))
                    # But the variables used to define it ARE now live
                    current_live.update(instr.get('use', []))
            else:
                optimized_instrs.insert(0, instr)
                
                # If the function call defines something (like scanf defining user_input),
                # it is no longer 'live' above this line
                if 'def' in instr and instr['def']:
                    defs = instr['def'] if isinstance(instr['def'], list) else [instr['def']]
                    for d in defs:
                        current_live.discard(d)
                        
                # The variables passed to the function (like printf uses) become live
                current_live.update(instr.get('use', []))
                
        G.nodes[n]['instrs'] = optimized_instrs
    return G

def remove_unreachable_code(G, start_node_id=0):
    reachable = set(nx.dfs_preorder_nodes(G, source=start_node_id))
    unreachable = set(G.nodes) - reachable
    G.remove_nodes_from(unreachable)
    return G

def update_graph_labels(G):
    """Regenerates the Graphviz string labels based on the optimized instructions."""
    for n in G.nodes:
        lines = [f"Block {n}"]
        lines.append("-" * 15)
        for instr in G.nodes[n]['instrs']:
            if 'code' in instr:
                # FIX: Escape double quotes for the AFTER image too
                safe_code = instr['code'].replace('"', '\\"')
                lines.append(safe_code)
        
        label_str = "\\n".join(lines)
        G.nodes[n]['label'] = f'"{label_str}"'
    return G