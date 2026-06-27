import unittest
from pycparser import c_parser
from src.core_parser import CFGBuilder

class TestParser(unittest.TestCase):
    def test_basic_block_generation(self):
        # Using CParser directly on a string to avoid needing a temporary file
        code = """
        void main() {
            int a = 5;
            int b = a + 10;
        }
        """
        parser = c_parser.CParser()
        ast = parser.parse(code)
        
        builder = CFGBuilder()
        builder.visit(ast)
        
        # Flatten all instructions from all blocks to verify
        all_instrs = []
        for block in builder.blocks:
            all_instrs.extend(block.instructions)
            
        # Verify block creation and assignment capturing
        self.assertTrue(len(builder.blocks) > 0)
        self.assertTrue(any(i.get('def') == 'a' for i in all_instrs))
        self.assertTrue(any('a' in i.get('use', []) for i in all_instrs if i.get('def') == 'b'))

if __name__ == '__main__':
    unittest.main()