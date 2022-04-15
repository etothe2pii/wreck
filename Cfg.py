from sys import argv
from re import match
from typing import Optional
import sys


class ParseTableConflict(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ParseError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Token:
    def __init__(self, token_type='', src_value='') -> None:
        self.token_type: str = token_type
        self.src_value: str = src_value

    def __str__(self) -> str:
        ret = self.token_type
        if self.src_value != "":
            ret += " SRC: " + self.src_value
        return ret


class TreeNode:
    def __init__(self, name="", children=None, parent=None) -> None:
        self.name: str = name
        # children can be a TreeNode or list of token and data
        self.children: list[TreeNode | Token]
        if children is None:
            self.children = []
        else:
            self.children = children

        self.parent: Optional[TreeNode] = parent

    def __str__(self, level=0) -> str:
        ret = self.name + '\n'
        for child in self.children:
            ret += '  ' * (level+1)
            if isinstance(child, TreeNode):
                ret += child.__str__(level+1)
            else:
                ret += str(child) + '\n'
        return ret

def peek_line(file):
    pos = file.tell()
    data = file.readline()
    file.seek(pos)
    return data



class CFG:
    '''
    rule_list contains a list of rules.  For each rule, the first element is
    the non_terminal name and the rest of the elements are the sequence
    of terminals or non_terminals that make up the rule.  non_terminals and
    terminals are represented as strings.  lambda is represented as 'lambda'
    '''
    def __init__(self):
        self.rule_list = []
        self.non_terminals = set()
        self.terminals = set()
        self.start_symbol = ''
        
    @classmethod
    def from_file(cls, filename):
        '''reads in cfg from file and initialized all member variables'''
        cfg = cls()
        with open(filename) as f:
            tokens = ' '.join(f.readlines()).split()
            cur_rule = []
            i = 0
            while i < len(tokens):
                if i < len(tokens)-1 and tokens[i+1] == "->":
                    cfg.rule_list.append(cur_rule) if cur_rule else None
                    cur_rule = [tokens[i]]
                    cfg.non_terminals.add(tokens[i])
                    i += 2
                elif tokens[i] == '|':
                    cfg.rule_list.append(cur_rule)
                    cur_rule = [cur_rule[0]]
                    i += 1
                else:
                    if match('[A-Z]', tokens[i]):
                        cfg.non_terminals.add(tokens[i])
                    else:
                        cfg.terminals.add(tokens[i])
                    if tokens[i] == "$":
                        cfg.start_symbol = cur_rule[0]


                    cur_rule.append(tokens[i])
                    i += 1

            cfg.rule_list.append(cur_rule)       
        
        return cfg

    def followSet(self, A, T):
        if A in T:
            return (set(), T)

        T = T.copy()
        T.add(A)

        F = set()

        rules_with_A = (rule for rule in self.rule_list if A in rule[1:])
        for p in rules_with_A:
            rhs = p[1:]
            pi = rhs[rhs.index(A)+1:]
            if len(pi) > 0:
                G, I = self.firstSet(pi, set())
                F = F.union(G)

            if len(pi) == 0 or (all(x in self.non_terminals for x in pi) and all(self.derivesToLambda(x, []) for x in pi)):
                G, I = self.followSet(p[0], T)
                F = F.union(G)


        return F, T

    def derivesToLambda(self, L, T):
        T = T.copy()
        if L == 'lambda':
            return True
        elif L in self.terminals:
            return False

        L_rules = (rule for rule in self.rule_list if rule[0] == L)
        for p in L_rules:
            if p in T:
                continue
            if p == [L, 'lambda']:
                return True
            if any(x in self.terminals for x in p[1:]):
                continue

            all_derive_to_lambda = True

            for X in (N for N in p[1:] if N in self.non_terminals):
                T.append(p)
                all_derive_to_lambda = self.derivesToLambda(X, T)
                T.pop()
                if not all_derive_to_lambda:
                    break

            if all_derive_to_lambda:
                return True

        return False


    def print_rules(self):
        for i, rule in enumerate(self.rule_list):
            print(f'({i})  {rule[0]} -> {" ".join(rule[1:])}')

    def firstSet(self, XB, T: set):
        if XB[0] in self.terminals:
            return {XB[0]},T

        F = set()

        if not(XB[0] in T):
            T.add(XB[0])

            for rule in self.rule_list:
                if rule[0] == XB[0]:
                    R = rule[1:]
                    G,I = self.firstSet(R, T)
                    F = F.union(G)
        
        if (self.derivesToLambda(XB[0], []) and len(XB[1:]) > 0):
            G,I = self.firstSet(XB[1:],T)
            F = F.union(G)
        
        return F,T

    def predictSet(self, rule):
        predict, ignore = self.firstSet(rule[1:], set())

        derives = False
        for character in rule[1:]:
            if self.derivesToLambda(character, []):
                derives = True
            else:
                derives = False
                break

        
        if derives:
            follow, ignore = self.followSet(rule[0], set())
            predict = predict.union(follow)

        if 'lambda' in predict:
            predict.remove('lambda')
            
        return predict

    # helper method to return all production rules whose LHS is some given nonterminal
    def productions(self, nonterm):
        prods = []

        for rule in self.rule_list:
            if rule[0] == nonterm:
                prods.append(rule)
        return prods

    # LL(1) Parse table
    # row and column labels occur in the order that nonterminals and terminals are stored in self.non_terminals and self.terminals
    def parseTable(self):
        table = dict()    
        
        for A in self.non_terminals:
            table[A] = dict()
            for p in self.productions(A):
                for a in self.predictSet(p):
                    if a in table[A]:
                        raise ParseTableConflict(f'rule {A}')
                    table[A][a] = self.rule_list.index(p)

        return table
    '''
    def parse_tree(self, file_name: str, sdt_map: dict):
        parse_table = self.parseTable()
        root = TreeNode(name='root')
        current_node = root
        stack = []
        stack.append(self.start_symbol)
        with open(file_name) as file:
            while len(stack) > 0:
                print(stack)
                if stack[-1] == 'lambda':
                    stack.pop()
                    current_node.children.append(Token(token_type='lambda'))
                elif stack[-1] in self.terminals:
                    if stack[-1] == '$':
                        assert file.readline() == ''
                        token_and_data = ['$']
                    else:
                        token_and_data = file.readline().split()
                    print(stack)
                    print("TOKEN AND DATA: " + str(token_and_data))
                    token = Token(token_type=token_and_data[0])
                    if len(token_and_data) == 2:
                        token.src_value = token_and_data[1]
                    if token.token_type != stack[-1]:
                        raise ParseError(f'Expected {stack[-1]}, got {token.token_type}')
                    assert token.token_type == stack[-1]
                    current_node.children.append(token)
                    stack.pop()
                elif stack[-1] in self.non_terminals:
                    if peek_line(file) == '':
                        token = '$'
                    else:
                        token = peek_line(file).split()[0]
                    rule = parse_table[stack[-1]][token]

                    new_node = TreeNode()
                    new_node.parent = current_node
                    new_node.name = stack[-1]

                    current_node.children.append(new_node)
                    current_node = new_node

                    stack.pop()
                    stack.append((-1, new_node.name))
                    for item in reversed(self.rule_list[rule][1:]):
                        stack.append(item)
                elif stack[-1][0] == -1:
                    if stack[-1][1] in sdt_map:
                        sdt_proc = sdt_map[stack[-1][1]]
                        sdt_proc(current_node)
                    assert(current_node.parent is not None)
                    current_node = current_node.parent
                    stack.pop()
        return root.children[0]

    '''
    def parse_tree(self, input_string, symbols):
        table = self.parseTable()
        root = TreeNode(name='root')
        current_node = root
        
        input_stack = []
        rule_stack = [self.start_symbol]
        escaped = False

        for i in range(len(input_string)):
            if input_string[i] == "\\":
                if(input_string[i+1] == "n"):
                    input_stack.append('\n')
                    escaped = True
                elif(input_string[i+1] == "s"):
                    input_stack.append(" ")
                    escaped = True
                elif(input_string[i+1] == "\\"):
                    input_stack.append('\\')
                    escaped = False
            elif (not escaped):
                if(input_string[i] == "|"):
                    input_stack.append("pipe")
                elif(input_string[i] == "("):
                    input_stack.append("open")
                elif(input_string[i] == ")"):
                    input_stack.append("close")
                elif(input_string[i] == "*"):
                    input_stack.append("kleene")
                elif(input_string[i] == "+"):
                    input_stack.append("plus")
                elif(input_string[i] == "-"):
                    input_stack.append("dash")
                elif(input_string[i] == "."):
                    input_stack.append("dot")
                elif(input_string[i] in symbols):
                    input_stack.append(input_string[i])
                else:
                    print("EXITING WITH ERROR CODE 2")
                    sys.exit(2)
            elif(escaped):
                escaped = False

        input_stack.append("$")
        print(table)
        while(not len(rule_stack) == 0):
            if(rule_stack[0] == "endofproduction"):
                current_node = current_node.parent
                rule_stack.pop(0)
            elif(len(input_stack) == 0 ):
                sys.exit(2)
            elif((input_stack[0] in symbols and rule_stack[0] == "char") or rule_stack[0] == input_stack[0]):
                current_node.children.append(TreeNode(name = input_stack[0],parent = current_node))
                rule_stack.pop(0)
                input_stack.pop(0)
            elif(rule_stack[0] == "lambda"):
                current_node.children.append(TreeNode(name = "lambda", parent = current_node))
                rule_stack.pop(0)
            elif(len(input_stack) == 1 and rule_stack[0] != input_stack[0] and not rule_stack[0] in table):
                sys.exit(2)
            elif((input_stack[0] in symbols and "char" in table[rule_stack[0]].keys()) or input_stack[0] in table[rule_stack[0]].keys()):
                if input_stack[0] in symbols:
                    rule_number = table[rule_stack[0]]["char"]
                else:
                    rule_number = table[rule_stack[0]][input_stack[0]]
                
                tmp_node = TreeNode(name = rule_stack[0], parent = current_node)
                current_node.children.append(tmp_node)
                current_node = tmp_node
                rule_stack.pop(0)
                tmp_stack = []
                for i in range(1, len(self.rule_list[rule_number])):
                    tmp_stack.append(self.rule_list[rule_number][i])
                tmp_stack.append("endofproduction")
                rule_stack = tmp_stack + rule_stack
            else:
                print("EXIT 2")
                sys.exit(2)
                




        return current_node.children[0]



        


def flip_flop(node: TreeNode):
    new_children = []
    new_children.append(node.children[1])
    new_children.append(node.children[2])
    new_children.append(node.children[0])
    node.children = new_children

def flatten(node: TreeNode):
    if node.children[0] == 'f':
        node.parent.children[-1] = 'f'
    elif node.parent.name == 'B':
        my_children = node.children
        node.parent.children.pop()
        node.parent.children += my_children

        

if __name__ == '__main__':
    cfg = CFG.from_file(argv[1])
    #for N in cfg.non_terminals:
    #    print(f'{N}:\n\tderivesToLambda: {cfg.derivesToLambda(N, [])}\n\tfirstSet: {cfg.firstSet(N, set())[0]}\n\tfollowSet: {cfg.followSet(N, set())[0]}')

    #print(cfg.rule_list)
    #print(cfg.non_terminals)
    #print(cfg.terminals)

    #for rule in cfg.rule_list:
    #    print(f'{rule[0]}: {cfg.predictSet(rule)}')
    #print(cfg.parseTable())
    sdt_map = {'A': flip_flop, 'B': flatten}

    print(cfg.parse_tree(argv[2], sdt_map), end='')

    
    #print(cfg.predictSet(cfg.rule_list[0]))
