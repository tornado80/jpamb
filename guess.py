#!/usr/bin/env python3
""" A very stupid syntatic analysis, that only checks for assertion errors.
"""

import os
import sys, logging

l = logging
l.basicConfig(level=logging.DEBUG)

(name,) = sys.argv[1:]

import re
from pathlib import Path

# Read the method_name
RE = r"(?P<class_name>.+)\.(?P<method_name>.*)\:\((?P<params>[^\s]*)\)(?P<return>[^\s]*)"
if not (i := re.match(RE, name)):
    l.error("invalid method name: %r", name)
    sys.exit(-1)

#l.debug("class_name: %s, method_name: ‰s, params: ‰s, return: ‰s", 
#        str(i["class_name"]), str(i["method_name"]), str(i["params"]), str(i["return"]))

TYPE_LOOKUP = {
    "Z": "boolean",
    "I": "int",
}

srcfile = (Path("src/main/java") / i["class_name"].replace(".", "/")).with_suffix(
    ".java"
)

import tree_sitter
import tree_sitter_java

JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
parser = tree_sitter.Parser(JAVA_LANGUAGE)

with open(srcfile, "rb") as f:
    l.debug("parse sourcefile %s", srcfile)
    tree = parser.parse(f.read())

simple_classname = i["class_name"].split(".")[-1]

# To figure out how to write these you can consult the
# https://tree-sitter.github.io/tree-sitter/playground
class_q = JAVA_LANGUAGE.query(
    f"""
    (class_declaration 
        name: ((identifier) @class-name 
               (#eq? @class-name "{simple_classname}"))) @class
"""
)

for node in class_q.captures(tree.root_node)["class"]:
    break
else:
    l.error(f"could not find a class of name {simple_classname} in {srcfile}")
    sys.exit(-1)

l.debug("Found class %s", node.range)

method_name = i["method_name"]

method_q = JAVA_LANGUAGE.query(
    f"""
    (method_declaration name: 
      ((identifier) @method-name (#eq? @method-name "{method_name}"))
    ) @method
"""
)

for node in method_q.captures(node)["method"]:
    if not (p := node.child_by_field_name("parameters")):
        l.debug(f"Could not find parameteres of {method_name}")
        continue

    params = [c for c in p.children if c.type == "formal_parameter"]

    if len(params) == len(i["params"]) and all(
        (tp := t.child_by_field_name("type")) is not None
        and tp.text is not None
        and TYPE_LOOKUP[tn] == tp.text.decode()
        for tn, t in zip(i["params"], params)
    ):
        break
else:
    l.warning(f"could not find a method of name {method_name} in {simple_classname}")
    sys.exit(-1)

l.debug("Found method %s %s", method_name, node.range)

body = node.child_by_field_name("body")
assert body and body.text
for t in body.text.splitlines():
    l.debug("line: %s", t.decode())

b_expr_query = JAVA_LANGUAGE.query(f"""(binary_expression
  operator: "/"
) @expr""")

division_by_zero = 50

assertion_error = 50

b_expr_capture = b_expr_query.captures(body)

if "expr" in b_expr_capture:
    for node in b_expr_capture["expr"]:
        right = node.child_by_field_name("right")

        # literal zero
        if right.type == "decimal_integer_literal" and right.text == b"0":
            l.debug("Found division by zero")
            division_by_zero = 70

        # variable that is set to zero before hand
        if right.type == "identifier":
            l.debug("right: %s", right.text)
            l.debug("children: %s", p.children)
            for child in p.children:
                if child.type == "formal_parameter" and child.child_by_field_name("name").text == right.text:
                    l.debug("Found division by zero")
                    division_by_zero = max(55, division_by_zero)

assert_q = JAVA_LANGUAGE.query(f"""(assert_statement) @assert""")

assert_capture = assert_q.captures(body)

if "assert" in assert_capture:
    for node in assert_q.captures(body)["assert"]:
        if node.children[1].type == "false":
            l.debug("Found assertion")
            assertion_error = max(70, assertion_error)
        if node.children[1].type == "identifier" or node.children[1].type == "binary_expression":
            l.debug("Found assertion")
            assertion_error = max(55, assertion_error)
else:
    l.debug("Did not find any assertions")

print(f"assertion error;{assertion_error}%")
print(f"divide by zero;{division_by_zero}%")