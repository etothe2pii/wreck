import sys
from Cfg import TreeNode

'''
to_graphvis will take in a tree node and a destination file name and make a 
dot compatible file. 

With dot installed invoke as 

dot -Tpng [input] >> [output]

for a png or 

dot -Tsvp [input] >> [output]

for an svg
'''

def to_graphviz(node, output_file):
    output = open(output_file, "w")
    output.write("digraph Parse{\n")
    output.write("\n")
    stack = [node]
    numbers = [1]
    output.write("\t " + str(numbers[0]) + " [label=\"" + stack[0].name + "\"];\n")
    current_number = 1
    while(len(stack) != 0):
        for child in stack[0].children:
            current_number += 1
            if(child.name == "\\"):
                output.write("\t " + str(current_number) + " [label=\"" + child.name + "\\\"];\n")
                output.write("\t " + str(numbers[0]) + " -> " + str(current_number) + ";\n")
            else:
                output.write("\t " + str(current_number) + " [label=\"" + child.name + "\"];\n")
                output.write("\t " + str(numbers[0]) + " -> " + str(current_number) + ";\n")
            stack.append(child)
            numbers.append(current_number)
        stack.pop(0)
        numbers.pop(0)

    output.write("}")
    output.close()
