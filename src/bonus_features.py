import networkx as nx

def detect_loops(G, start_node=0):
    # Dominator trees via NetworkX
    dom = nx.immediate_dominators(G, start_node)
    loops = []
    for edge in G.edges:
        u, v = edge
        # Back-edge: v dominates u
        curr = u
        is_back_edge = False
        while curr != start_node:
            if curr == v:
                is_back_edge = True
                break
            curr = dom.get(curr, start_node)
            
        if is_back_edge:
            loops.append((u, v)) # u -> v is a back-edge
    return loops

def taint_analysis(G):
    tainted_vars = set()
    warnings = []
    
    # Topological sort ensures we process the graph flowing downwards
    try:
        nodes = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        nodes = G.nodes # Fallback if there are loops
        
    for n in nodes:
        for instr in G.nodes[n].get('instrs', []):
            
            # 1. SOURCE: scanf marks variables as TAINTED
            if instr.get('type') == 'call' and instr.get('func') == 'scanf':
                defs = instr.get('def', [])
                tainted_vars.update(defs)
                
            # 2. PROPAGATION: If an assignment uses a tainted var, the new var is tainted
            elif instr.get('type') == 'assign':
                uses = instr.get('use', [])
                if any(u in tainted_vars for u in uses):
                    if instr.get('def'):
                        tainted_vars.add(instr['def'])
                        
            # 3. SINK: If printf uses a tainted var, raise a warning!
            elif instr.get('type') == 'call' and instr.get('func') == 'printf':
                uses = instr.get('use', [])
                for u in uses:
                    if u in tainted_vars:
                        warnings.append(f"[!] SECURITY WARNING: Tainted variable '{u}' reached printf in Block {n}!")
                        
    return warnings


def loop_invariant_code_motion(G):
    # 1. Find the back-edge to identify the loop (tail -> header)
    # Assuming Block 0 is the start node.
    dom = nx.immediate_dominators(G, 0)
    
    for u, v in G.edges:
        # If the target (v) dominates the source (u), it's a back-edge
        curr = u
        is_back_edge = False
        while curr != 0 and curr in dom:
            if curr == v:
                is_back_edge = True
                break
            if dom[curr] == curr: 
                break
            curr = dom[curr]
            
        if is_back_edge:
            header = v
            tail = u
            preheader = dom[header]
            
            # 2. Find all variables defined INSIDE the loop
            loop_defs = set()
            for node in [header, tail]:
                for instr in G.nodes[node].get('instrs', []):
                    if instr.get('def'):
                        loop_defs.add(instr['def'])
            
            # 3. Scan the loop body (tail) for invariant instructions
            new_tail_instrs = []
            hoisted_instrs = []
            
            for instr in G.nodes[tail].get('instrs', []):
                if instr['type'] == 'assign':
                    # Check if ANY used variable is redefined inside the loop
                    uses_loop_def = any(use in loop_defs for use in instr.get('use', []))
                    
                    if not uses_loop_def:
                        # It's invariant! We can safely hoist it out of the loop.
                        hoisted_instrs.append(instr)
                    else:
                        new_tail_instrs.append(instr)
                else:
                    new_tail_instrs.append(instr)
                    
            # 4. Move hoisted instructions to the preheader (Block 0)
            if hoisted_instrs:
                G.nodes[preheader]['instrs'].extend(hoisted_instrs)
                G.nodes[tail]['instrs'] = new_tail_instrs
                
    return G