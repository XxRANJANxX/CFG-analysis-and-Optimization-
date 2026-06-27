def live_variable_analysis(G):
    # Initialize IN and OUT sets
    for n in G.nodes:
        G.nodes[n]['in'] = set()
        G.nodes[n]['out'] = set()
        
        defs = set()
        uses = set()
        
        for instr in G.nodes[n]['instrs']:
            # Handle 'def' which could be a string or a list
            if 'def' in instr and instr['def']:
                if isinstance(instr['def'], list):
                    defs.update(instr['def'])
                else:
                    defs.add(instr['def'])
                    
            # Handle 'use' which could be a string or a list
            if 'use' in instr and instr['use']:
                if isinstance(instr['use'], list):
                    uses.update(instr['use'])
                else:
                    uses.add(instr['use'])
                    
        G.nodes[n]['def'] = defs
        G.nodes[n]['use'] = uses

    changed = True
    while changed:
        changed = False
        # Backwards traversal
        for n in reversed(list(G.nodes)):
            old_in = G.nodes[n]['in'].copy()
            
            # OUT[n] = U IN[s] for s in successors
            out_set = set()
            for succ in G.successors(n):
                out_set.update(G.nodes[succ]['in'])
            G.nodes[n]['out'] = out_set
            
            # IN[n] = USE[n] U (OUT[n] - DEF[n])
            G.nodes[n]['in'] = G.nodes[n]['use'].union(out_set - G.nodes[n]['def'])
            
            if old_in != G.nodes[n]['in']:
                changed = True
                
    return G