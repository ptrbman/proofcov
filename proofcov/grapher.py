from rich import print

from pycparser import c_parser, c_ast

from graphviz import Digraph

## Go through the AST and find all branches (if statements)
## For each one, we save what lines are included in that particular if statement. Then we will
## check if at least one of those are marked, then the branch is checked.
## Let's create the graph immediately. It shoudld be nodes, where each node is a 
# statement according to our grammar.

# Each node has:
# - a line number referring to the source line
# - a copy of the actual line (text)
# - a list of children nodes (for branches, two children: then and else)

# We will work with graphs where each graph has one top node, one bottom node and one or more internal nodes

class Node:
    def __init__(self, line_number, text, target_join=None, is_join=False):
        self.line_number = line_number
        self.text = text
        self.children = []
        self.is_join = is_join
        self.target_join = target_join  # for branches, points to the join node

    def print_recursive(self, indent):
        print(" " * indent + str(self))
        for child in self.children:
            print("\t", self.text)
            child.print_recursive(indent + 2)

    def draw_string(self):
        if self.line_number is not None:
            return f"{self.line_number}: {self.text}"
        else:
            return f"{self.text}"

    def __str__(self):
        return f"Node(line={self.line_number}, text={self.text}, children={len(self.children)})"        

class Graph:
    def __init__(self, top_node, bottom_node):
        # bottom node should be a grandchild of all nodes in graph
        # TODO: make assert to check this
        self.top_node = top_node
        self.bottom_node = bottom_node
     
    def attach(self, other_graph):
        # We keep the join node, so attach this bottom node to the top node of other_graph
        
        # Ensure it is empty
        assert(len(self.bottom_node.children) == 0)
        self.bottom_node.children = [other_graph.top_node]
        return Graph(self.top_node, other_graph.bottom_node) 
    
   
    def all_nodes(self):
        nodes = []
        visited = set()

        def collect(node):
            node_id = id(node)
            if node_id not in visited:
                visited.add(node_id)
                if not node.is_join:
                    nodes.append(node)
                for child in node.children:
                    collect(child)

        collect(self.top_node)
        return nodes    

    def all_branch_nodes(self):
        all_nodes = self.all_nodes()
        branch_nodes = [n for n in all_nodes if n.target_join is not None]
        return branch_nodes
    
    def print(self):
        self.top_node.print_recursive(0)
        
    def draw(self, filename):
        dot = Digraph(comment="Control Flow Graph", format=filename.split('.')[-1])
        visited = set()

        def add_node(node):
            node_id = str(id(node))  # unique identifier
            if node_id not in visited:
                visited.add(node_id)
                dot.node(node_id, node.draw_string())
                if node.target_join:
                    join_id = str(id(node.target_join))
                    dot.edge(node_id, join_id, style='dashed')
                for child in node.children:
                    child_id = str(id(child))
                    dot.edge(node_id, child_id)
                    add_node(child)

        add_node(self.top_node)
        # format adds extension automatically, so we just give the name without extension
        outfile = filename.rsplit('.', 1)[0]
        dot.render(outfile, view=False, cleanup=True)  # view=True opens the file automatically


def astvalue_to_string(astvalue):
    if isinstance(astvalue, c_ast.ID):
        return astvalue.name
    elif isinstance(astvalue, c_ast.Constant):
        return astvalue.value
    elif isinstance(astvalue, c_ast.BinaryOp):
        left = astvalue_to_string(astvalue.left)
        right = astvalue_to_string(astvalue.right)
        return f"({left} {astvalue.op} {right})"
    elif isinstance(astvalue, c_ast.UnaryOp):
        assert(astvalue.op == '!')
        return f"!{astvalue_to_string(astvalue.expr)}"
    else:
        raise Exception("Unsupported AST value type in astvalue_to_string:", type(astvalue))
    
def make_graph(ast) -> Graph:
    if isinstance(ast, c_ast.FileAST):
        ext = ast.ext
        assert(len(ext) == 1)
        g = make_graph(ext[0])
        return g
    
    elif isinstance(ast, c_ast.FuncDef):
        decl = ast.decl
        assert(decl.name == "main")
        body = make_graph(ast.body) 
        assert(body is not None)
        return body
    
    elif isinstance(ast, c_ast.Compound):
        block_items = ast.block_items
        cur_g = None
        for b in block_items:
            g = make_graph(b)
            if g is not None:
                if not cur_g: # First node!
                    cur_g = g 
                else:
                    cur_g = cur_g.attach(g)
                
        return cur_g
    elif isinstance(ast, c_ast.Decl):
        return None
    elif isinstance(ast, c_ast.If):
        s = f'if ({astvalue_to_string(ast.cond)})'
        join_node = Node(line_number=None, text="JOIN", is_join=True)
        if_node = Node(line_number=ast.coord.line, text=s, target_join=join_node)
        
        # We need a join node
        join_graph = Graph(join_node, join_node)
         
        # Then branch
        then_graph = make_graph(ast.iftrue)
        assert(then_graph is not None)
        then_graph.attach(join_graph)
        
        # Else branch
        if ast.iffalse is not None:
            else_graph = make_graph(ast.iffalse)
            else_graph.attach(join_graph)
            if_node.children = [then_graph.top_node, else_graph.top_node]
        else:
            if_node.children = [then_graph.top_node, join_node]
     
        g = Graph(if_node, join_node)
        # Store all nodes in g into if_node
        if_node.nodes = g.all_nodes()
        return g
    elif isinstance(ast, c_ast.FuncCall):
        s = f'{ast.name.name}{", ".join([astvalue_to_string(arg) for arg in ast.args.exprs])}'
        n = Node(line_number=ast.coord.line, text=s)
        return Graph(n, n)
    elif isinstance(ast, c_ast.Assignment):
        s = f'{ast.lvalue.name} {ast.op} {astvalue_to_string(ast.rvalue)}'
        n = Node(line_number=ast.coord.line, text=s)
        g = Graph(n, n)
        return g
    else:
        raise Exception("Unsupported AST node in find_branches:", type(ast))
    
    
    
    
