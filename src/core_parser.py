import os

from pycparser import c_ast, parse_file, c_generator


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FAKE_LIBC_DIR = os.path.join(BASE_DIR, 'fake_libc_include')

class BasicBlock:
    def __init__(self, block_id):
        self.id = block_id
        self.instructions = []
        self.successors = []

    def add_instruction(self, instr):
        self.instructions.append(instr)

class CFGBuilder(c_ast.NodeVisitor):
    def __init__(self):
        self.blocks = []
        self.current_block = BasicBlock(0)
        self.blocks.append(self.current_block)
        self.block_counter = 1
        self.gen = c_generator.CGenerator() # ast to c ka converter

    def _new_block(self):
        block = BasicBlock(self.block_counter)
        self.block_counter += 1
        self.blocks.append(block)
        return block
    
    def visit_FuncCall(self, node):
        func_name = node.name.name if isinstance(node.name, c_ast.ID) else str(node.name)
        code_str = self.gen.visit(node) + ";"
        
        uses = []
        defs = []
        
        if node.args:
            for expr in node.args.exprs:
                # If it's an address-of operator (like &user_input in scanf), it's a definition
                if isinstance(expr, c_ast.UnaryOp) and expr.op == '&':
                    if isinstance(expr.expr, c_ast.ID):
                        defs.append(expr.expr.name)
                else:
                    uses.extend(self._extract_uses(expr))
        
        self.current_block.add_instruction({
            'type': 'call',
            'func': func_name,
            'def': defs,
            'use': uses,
            'code': code_str
        })

    def _extract_uses(self, node):
        uses = []
        if isinstance(node, c_ast.ID):
            uses.append(node.name)
        elif isinstance(node, c_ast.BinaryOp):
            uses.extend(self._extract_uses(node.left))
            uses.extend(self._extract_uses(node.right))
        return uses

    def visit_Decl(self, node):
        if node.init:
            lval = node.name
            # If it's a simple constant, use an empty list for 'use'
            # If it's a variable or expression, extract them
            uses = self._extract_uses(node.init) if not isinstance(node.init, c_ast.Constant) else []
            code_str = self.gen.visit(node)
            self.current_block.add_instruction({
                'type': 'assign', 
                'def': lval, 
                'use': uses, 
                'code': code_str
            })

    def visit_Assignment(self, node):
        lval = node.lvalue.name if isinstance(node.lvalue, c_ast.ID) else str(node.lvalue)
        uses = self._extract_uses(node.rvalue)
        code_str = self.gen.visit(node)
        self.current_block.add_instruction({'type': 'assign', 'def': lval, 'use': uses, 'code': code_str})

    def visit_If(self, node):
        uses = self._extract_uses(node.cond)
        code_str = f"if ({self.gen.visit(node.cond)})"
        self.current_block.add_instruction({'type': 'branch', 'use': uses, 'code': code_str})
        
        true_block = self._new_block()
        false_block = self._new_block()
        merge_block = self._new_block()

        self.current_block.successors.extend([true_block, false_block])
        
        self.current_block = true_block
        self.visit(node.iftrue)
        self.current_block.successors.append(merge_block)

        self.current_block = false_block
        if node.iffalse:
            self.visit(node.iffalse)
        self.current_block.successors.append(merge_block)

        self.current_block = merge_block

    def visit_While(self, node):
        cond_block = self._new_block()
        body_block = self._new_block()
        exit_block = self._new_block()

        # 1. Current block jumps to condition check
        self.current_block.successors.append(cond_block)
        
        # 2. Condition block
        self.current_block = cond_block
        uses = self._extract_uses(node.cond)
        code_str = f"while ({self.gen.visit(node.cond)})"
        self.current_block.add_instruction({'type': 'branch', 'use': uses, 'code': code_str})
        
        # True goes to body, False goes to exit
        self.current_block.successors.extend([body_block, exit_block])
        
        # 3. Loop Body
        self.current_block = body_block
        self.visit(node.stmt)
        # End of body loops back to condition
        self.current_block.successors.append(cond_block)
        
        # 4. Set current block to exit so the rest of the code continues from there
        self.current_block = exit_block
        
    def visit_Return(self, node):
        uses = self._extract_uses(node.expr) if node.expr else []
        code_str = self.gen.visit(node)
        self.current_block.add_instruction({'type': 'return', 'use': uses, 'code': code_str})
        
        # FIX: A return terminates the basic block!
        # Anything parsed after this in the same scope gets pushed 
        # to a new block with NO incoming edges.
        disconnected_block = self._new_block()
        self.current_block = disconnected_block

def parse_c_file(filepath):
    ast = parse_file(filepath, use_cpp=True, cpp_args=['-nostdinc', f'-I{FAKE_LIBC_DIR}'])
    builder = CFGBuilder()
    builder.visit(ast)
    return builder.blocks