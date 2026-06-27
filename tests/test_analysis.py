import unittest
import networkx as nx
from src.static_analysis import live_variable_analysis

class TestAnalysis(unittest.TestCase):
    def test_live_variable_analysis(self):
        G = nx.DiGraph()
        
        # Block 0: x = 10
        G.add_node(0, instrs=[{'type': 'assign', 'def': 'x', 'use': []}])
        
        # Block 1: y = x + 5  (uses 'x')
        G.add_node(1, instrs=[{'type': 'assign', 'def': 'y', 'use': ['x']}])
        
        G.add_edge(0, 1)
        
        # Run analysis
        analyzed_G = live_variable_analysis(G)
        
        # 'x' is used in Block 1, so it must be in Block 1's IN set
        self.assertIn('x', analyzed_G.nodes[1]['in'])
        
        # Because 'x' is in Block 1's IN set, it must be in Block 0's OUT set
        self.assertIn('x', analyzed_G.nodes[0]['out'])
        
        # 'y' is defined but never used by any future node, so it shouldn't be live OUT
        self.assertNotIn('y', analyzed_G.nodes[1]['out'])

if __name__ == '__main__':
    unittest.main()