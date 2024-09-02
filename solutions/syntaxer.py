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
RE = r"(?P<class_name>.+)\.(?P<method_name>.*)\:\((?P<params>.*)\)(?P<return>.*)"
if not (i := re.match(RE, name)):
    l.error("invalid method name: %r", name)
    sys.exit(-1)

TYPE_LOOKUP = {
    "Z": "boolean",
    "I": "int",
}

import tree_sitter
import tree_sitter_java as tsjava

#JAVA_LANGUAGE = tree_sitter_languages.get_language("java")

JAVA_LANGUAGE = tree_sitter.Language(tsjava.language())


parser = tree_sitter.Parser(JAVA_LANGUAGE)
#parser.set_language(JAVA_LANGUAGE)


srcfile = (Path("src/main/java") / i["class_name"].replace(".", "/")).with_suffix(
    ".java"
)

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

for node, t in class_q.captures(tree.root_node):
    if t == "class":
        break
else:
    l.error(f"could not find a class of name {simple_classname} in {srcfile}")
    sys.exit(-1)

l.debug("Found class %s", node)

method_name = i["method_name"]

method_q = JAVA_LANGUAGE.query(
    f"""
    (method_declaration name: 
      ((identifier) @method-name (#eq? @method-name "{method_name}"))
    ) @method
"""
)

for node, t in method_q.captures(node):
    if not (t == "method" and (p := node.child_by_field_name("parameters"))):
        continue

    params = [c for c in p.children if c.type == "formal_parameter"]

    if len(params) == len(i["params"]) and all(
        (tp := t.child_by_field_name("type")) and TYPE_LOOKUP[tn] == tp.text.decode()
        for tn, t in zip(i["params"], params)
    ):
        break
else:
    l.warning(f"could not find a method of name {method_name} in {simple_classname}")
    sys.exit(-1)

l.debug("Found method %s", node)

assert_q = JAVA_LANGUAGE.query(f"""(assert_statement) @assert""")

for node, t in assert_q.captures(node):
    if t == "assert":
        break
else:
    l.debug("Did not find any assertions")
    print("assertion error;20%")
    sys.exit(0)

l.debug("Found assertion")
print("assertion error;80%")
sys.exit(0)
