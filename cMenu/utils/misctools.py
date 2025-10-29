import ast

def show_fns(path_:str):
    """Parse a Python file and extract information about functions and classes.
    
    Analyzes the abstract syntax tree (AST) of a Python file to extract
    function and class definitions, including their signatures and line numbers.
    
    Args:
        path_ (str): Path to the Python file to analyze.
    
    Returns:
        dict: Dictionary with 'classes' and 'functions' keys containing lists
            of string representations of the classes and functions found.
    """
    dividerchar = '\u23FA'
    
    # open file as ast (abstract syntax tree)
    with open(path_) as file:
        node = ast.parse(file.read())

    # 
    def show_fninfo(functionNode:ast.FunctionDef):
        """Format function information as a string.
        
        Args:
            functionNode (ast.FunctionDef): AST node representing a function.
        
        Returns:
            str: Formatted string with function signature and line numbers.
        """
        function_rep = ''
        function_rep = functionNode.name + '('

        for arg in functionNode.args.args:
            function_rep += arg.arg + ','

        function_rep = function_rep.rstrip(function_rep[-1])
        rNode = functionNode.returns
        rtype = ''
        if isinstance(rNode, ast.BinOp):
            # this is a union type
            if isinstance(rNode.left, ast.Name):
                rtype += f'{rNode.left.id}'
            elif isinstance(rNode.left, ast.Constant):
                rtype += f'{rNode.left.value}'
            else:
                rtype += f'{rNode.left}' # type: ignore
            rtype += ' | '
            if isinstance(rNode.right, ast.Name):
                rtype += f'{rNode.right.id}'
            elif isinstance(rNode.right, ast.Constant):
                rtype += f'{rNode.right.value}'
            else:
                rtype += f'{rNode.right}' # type: ignore
        elif isinstance(rNode, ast.Subscript):
            rtype = f'{rNode.value.id}' # type: ignore
        elif isinstance(rNode, ast.Attribute):
            rtype = f'{rNode.value}' # type: ignore
        elif isinstance(rNode, ast.Constant):
            rtype = f'{rNode.value}'
        elif isinstance(rNode, ast.Name):
            rtype = f'{rNode.id}'
        #endif rNode type
        function_rep += f') -> {rtype} {dividerchar} lines {functionNode.lineno} to {functionNode.end_lineno}'
        return function_rep
    
    def show_clsinfo(classNode:ast.ClassDef):
        """Format class information as a string.
        
        Args:
            classNode (ast.ClassDef): AST node representing a class.
        
        Returns:
            str: Formatted string with class name, bases, and line numbers.
        """
        class_rep = f'class {classNode.name}('
        for base in classNode.bases:
            class_rep += base.id + ',' # type: ignore
        class_rep = class_rep.rstrip(class_rep[-1])
        class_rep += f') {dividerchar} lines {classNode.lineno} to {classNode.end_lineno}'
        return class_rep

    # get all fns and classes
    result = {'classes':[], 'functions':[]}
    functions = [n for n in node.body if isinstance(n, ast.FunctionDef)]
    classes = [n for n in node.body if isinstance(n, ast.ClassDef)]

    for function in functions:
        result['functions'].append(f'def {show_fninfo(function)}')

    for class_ in classes:
        result['classes'].append(f'class {class_.name}({[NN.id for NN in class_.bases]}) {dividerchar} lines {class_.lineno} to {class_.end_lineno}') # type: ignore
        methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
        for method in methods:
            result['classes'].append(f'    def {class_.name}.{show_fninfo(method)}')

    return result
    # print(', '.join(result))
    # This prints expected output
    # fo(x), A.fun(self,y), A._bo(self,y), A.NS(y,z), B.foo(self,z), B._bar(self,t)
def pretty_show_fns(path_:str):
    """Parse a Python file and return a formatted string of functions and classes.
    
    Args:
        path_ (str): Path to the Python file to analyze.
    
    Returns:
        str: Formatted string containing all classes and functions found in the file,
            organized by category with headers.
    """
    result = show_fns(path_)

    result_str = ''

    result_str += ' CLASSES: \n----------\n'
    for c in result['classes']:
        result_str += f'{c}\n'
    result_str += '\n'

    result_str += ' FUNCTIONS: \n------------\n'
    for c in result['functions']:
        result_str += f'{c}\n'
    
    return result_str

