import sys
from Cfg import *
from to_graphviz import * 

class L_dest:
    def __init__(self, size, accepting):
        self.destination = []
        self.accepting = accepting 
        for i in range(size):
            self.destination.append(False)
        
    def add_state(self):
        self.destination.append(False)
        
    def add_lambda(self, state):
        self.destination[state] = True
    
    def get_state(self, state):
        return self.destination[state]
    
    def accepting(self):
        return self.accepting
    
class L_table:
    
    def __init__(self):
        self.table = [L_dest(2, False), L_dest(2, True)]
        self.size = 2

    def add_state(self):
        self.size += 1 
        for t in self.table:
            t.add_state()
        self.table.append(L_dest(self.size, False))
    
    def add_lambda(self, source, destination):
        self.table[source].add_lambda(destination)
        
class T_dest:
    def __init__(self, length, accepting):
        self.destination = []
        self.accepting = accepting

        for i in range(length):
            self.destination.append(-1)

    def add_state(self):
        #self.destination.append(-1)
        return

    def add_transition(self, start, end):
        self.destination[start] = end 

    def get_state(self, state):
        return self.destination[state]

    def accepting(self):
        return self.accepting

class T_table:

    def __init__(self, symbols):
        self.symbols = {}
        self.table = [T_dest(len(symbols), False), T_dest(len(symbols), True)]
        self.size = 2

        for i in range(len(symbols)):
            self.symbols[symbols[i]] = i

    def add_state(self):
        self.size += 1
        for t in self.table:
            t.add_state()
        self.table.append(T_dest(len(symbols), False))

    def add_transition(self, symbol, src, dest):
        self.table[src].add_transition(self.symbols[symbol],dest)

class LT_tables:

    def __init__(self, symbols):
        self.l_table = L_table()
        self.t_table = T_table(symbols)
        self.symbols = symbols
        self.last_state = 1
        self.transitions  = 0
        
    def add_state(self):
        self.l_table.add_state()
        self.t_table.add_state()
        self.last_state += 1
        return self.last_state

    def add_transition(self, symbol, src, dest):
        self.t_table.add_transition(symbol, src, dest)
        self.transitions += 1

    def add_lambda(self, src, dest):
        self.l_table.add_lambda(src, dest)
        self.transitions += 1

    def write (self, output_file, lambda_symbol):
        output_file.write(str(self.transitions + 1) + " " + lambda_symbol)
        
        for symbol in self.symbols:
            output_file.write( " " + force_escape(symbol))
        output_file.write("\n")

        index = 0
        while index <= self.last_state:
            for i in range(len(self.t_table.table[index].destination)):
                if self.t_table.table[index].destination[i] != -1:
                    
                    if(self.t_table.table[index].accepting):
                        output_file.write("+ ")
                    else:
                        output_file.write("- ")


                    output_file.write(str(index) + " " + str(self.t_table.table[index].destination[i]) + " " + force_escape(self.symbols[i]) + "\n")

            for i in range(0, len(self.l_table.table[index].destination)):
                if self.l_table.table[index].destination[i]:
                    if(self.l_table.table[index].accepting):
                        output_file.write("+ ")
                    else:
                        output_file.write("- ")
                    output_file.write(str(index))
                    output_file.write(" ")
                    output_file.write(str(i))
                    output_file.write(" ")
                    output_file.write(lambda_symbol + "\n")
            index +=1
        output_file.write("+ 1 1")



class SqNode:

    def __init__(self, children):
        self.name = "SEQ"
        self.children = children.copy()

    def nodeFunction(self, src, dest, lt_table):
        for child in self.children:
            child_dest = lt_table.add_state()
            child.nodeFunction(src,child_dest, lt_table)
            src = lt_table.add_state()
            lt_table.add_lambda(child_dest, src)

        lt_table.add_lambda(src, dest)


class AltNode:
    def __init__(self, children):
        self.name = "ALT"
        self.children = children.copy()

    def nodeFunction(self, src, dest, lt_table):
        for child in self.children:
            child.nodeFunction(src,dest, lt_table)


class KleeneNode:
    def __init__(self, children):
        self.name = "KLEENE"
        self.children = children.copy()

    def nodeFunction(self, src, dest, lt_table):
        lt_table.add_lambda(src, dest)

        for child in self.children:
            child.nodeFunction(src,src, lt_table)

class SymbolNode:
    def __init__(self, symbol):
        self.name = symbol
        self.symbol = symbol
        self.children = []


    def nodeFunction(self, src, dest, lt_table):
        lt_table.add_transition(self.symbol, src, dest)

class LambdaNode:
    def __init__(self):
        self.name = "lambda"
        self.children = []

    def nodeFunction(self, src, dest, lt_table):
        lt_table.add_lambda(src, dest)

def force_escape(character):

    if(len(character) == 3):
        return character
    if(len(character) == 2):
        character = character[1:]

    hex_char = str(hex(ord(character)))[2:]
    if(len(hex_char) == 1):
        hex_char = "0"+ hex_char

    return "x" + hex_char

def cst_to_ast (root_node, symbols):

    if(root_node.name == "ALT" or root_node.name == "SEQ"):
        new_children = []
        for i in range(len( root_node.children)):
            new_children =  new_children + cst_to_ast(root_node.children[i], symbols)
        
        
        if len(new_children) > 1:
            i = 0
            while i < len(new_children) and len(new_children) != 1:
                if(new_children[i].name == "lambda"):
                    new_children.pop(i)
                    i -= 1
                i += 1
        if len(new_children) == 1:
            return new_children
        if root_node.name == "ALT":
            return [AltNode(new_children)]
        else:
            if (len(new_children) == 0):
                return [SqNode([LambdaNode()])]
            else:
                return [SqNode(new_children)]


    
    elif(root_node.name == "ATOM"):
        new_children = []
        if len(root_node.children[0].children) == 2 and len(root_node.children[0].children[1].children) == 2 :
            if(symbols.index(root_node.children[0].children[1].children[1].name) <  symbols.index(root_node.children[0].children[0].name)):
                sys.exit(3)

            for s in symbols[ symbols.index(root_node.children[0].children[0].name):symbols.index(root_node.children[0].children[1].children[1].name) + 1]:
                new_children = new_children + [SymbolNode(s)]

            new_children = [AltNode(new_children.copy())]

        else:
            new_children = cst_to_ast(root_node.children[0], symbols)

        if(root_node.children[1].children[0].name == "kleene"):

            return [KleeneNode(new_children)]

        elif(root_node.children[1].children[0].name == "plus"):

            return [SqNode(new_children + [KleeneNode(new_children)])]

        else:
            return new_children

    elif(root_node.name == "dot"):
        new_children = []

        for s in symbols:
            new_children.append(SymbolNode(s))

        return[AltNode(new_children)]
    
    elif(root_node.children != []):
        children_out = [] 
        for i in range(len(root_node.children)):

            children_out = children_out + cst_to_ast(root_node.children[i], symbols )
        
        return children_out
    #elif(root_node.name == "lambda"):
     #   return [LambdaNode()]
    elif(root_node.name in symbols):
        return [SymbolNode(root_node.name)]
    else:
        return []
    
def force_char(s):
    if(len(s) == 1):
        return s
    else:
        return bytearray.fromhex(s[1:]).decode()

    





if __name__ == '__main__':

    input_file = open(sys.argv[1], "r")
    output_file = open(sys.argv[2], "w")
    lines = input_file.readlines()
    tmp_symbols = lines[0]
    input_src =  lines[1:]
    input_file.close()

    output_file.write(tmp_symbols + "\n")

    forbidden_symbols = ["+", "|", "(", ")", "*", "."]
    symbols = []
    
    index = 0
    while(index < len(tmp_symbols)):
        if(tmp_symbols[index] == "x"):
            symbols.append(force_char(tmp_symbols[index:index+3]))
            index += 3
        elif(not (tmp_symbols[index] == " " or tmp_symbols[index] == "\n" or tmp_symbols == "\t")):
            symbols.append(tmp_symbols[index])
            index += 1
        else:
            index += 1
   
    
    escaped_symbols = []

    for s in symbols:
        escaped_symbols.append( force_escape(s))

    for i in range(len(symbols)):
        if symbols[i] in forbidden_symbols :
            symbols[i] = "\\" + symbols[i]
    print(symbols)
    for i in range(len(input_src)):
        input_src[i] = input_src[i].split()

        output_file.write(input_src[i][1] + ".tt " + input_src[i][1])
        if(len(input_src[i]) == 3):
            output_file.write(" " + input_src[i][2] + "\n")
        else:
            output_file.write("\n")

    output_file.close()
    
    cfg = CFG()
    cfg = cfg.from_file("llre.cfg")
    lambda_char = "x00"
    while(lambda_char in escaped_symbols):
        lambda_char = int(lambda_char[1:])
        lambda_char += 1
        if(lambda_char > 9):
            lambda_char = "x" + str(lambda_char)
        else:
            lambda_char = "x0" + str(lambda_char)

    for expression in input_src: 
        root_node = cfg.parse_tree(expression[0], symbols)
        to_graphviz(root_node, expression[1] + ".dot")
        root_node = cst_to_ast(root_node, symbols)[0]
        to_graphviz(root_node, expression[1] + "ast.dot")
        table = LT_tables(symbols)

        root_node.nodeFunction(0,1,table)
                
        token_file = open(expression[1] + ".nfa", "w")

        table.write(token_file, lambda_char)

        token_file.close()

        
        
        
        
    


