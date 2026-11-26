"""Compiles the DRAFT S1.1 JSON schema (subset: object/array/string/enum/minLength/required) into a COMPACT EBNF grammar (no free whitespace, fixed key order,
optional keys omitted rather than written empty). Reason: the JSON-schema grammar allows unlimited whitespace and the 0.6B model looped on tabs (see feasibility results).
compile_schema(schema, max_items=None, prefix_consumed=False):
  max_items: cap every list at this many items (nested optional chain; no {m,n} syntax needed)
  prefix_consumed: the answer already begins with '{"chief_complaint":"' (supplied in the assistant turn); the grammar then starts INSIDE the chief_complaint string"""
import json
from pathlib import Path

ROLE_FIRST_KEY = "chief_complaint"


def compile_schema(schema, max_items=None, prefix_consumed=False):
    rules = {}

    def q(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

    def val(sc, name):
        t = sc["type"]
        if t == "string":
            if "enum" in sc:
                return "(" + " | ".join(q('"' + e + '"') for e in sc["enum"]) + ")"
            return "str1" if sc.get("minLength", 0) >= 1 else "str"
        if t == "array":
            rid = name + "_item"
            rules[rid] = val(sc["items"], name + "_i")
            if not max_items:
                return f'("[" ({rid} ("," {rid})*)? "]")'
            # nested optional chain: [] | [item] | [item,item] ... up to max_items
            for k in range(max_items, 1, -1):
                tail = f'("," {rid} {name}_n{k + 1})?' if k < max_items else ""
                rules[f"{name}_n{k}"] = tail if k < max_items else ""
            # build chain explicitly: n2 .. n_max (n_max is empty), item then n2
            chain = {}
            for k in range(max_items, 1, -1):
                chain[k] = "" if k == max_items else f'("," {rid} {name}_n{k + 1})?'
            for k, v in chain.items():
                rules[f"{name}_n{k}"] = v if v else '""'
            return f'("[" ({rid} {name}_n2)? "]")'
        if t == "object":
            parts, first = [], True
            for k, sub in sc["properties"].items():
                piece = f'{q(chr(34) + k + chr(34) + ":")} {val(sub, name + "_" + k)}'
                if k in sc.get("required", []):
                    parts.append(piece if first else f'"," {piece}')
                    first = False
                else:
                    parts.append(f'("," {piece})?')
            return '"{" ' + " ".join(parts) + ' "}"'
        raise ValueError(t)

    root = val(schema, "r")
    if prefix_consumed:
        # drop the leading '"{" "\"chief_complaint\":" str1' and continue inside the string: body chars, closing quote, then the rest
        head = '"{" "\\"chief_complaint\\":" str1 '
        assert root.startswith(head), root[:80]
        root = '[^"\\\\\\n\\r\\t]+ "\\"" ' + root[len(head):]
    rules["root"] = root
    rules["str"] = '"\\"" [^"\\\\\\n\\r\\t]* "\\""'
    rules["str1"] = '"\\"" [^"\\\\\\n\\r\\t]+ "\\""'
    return "\n".join(f"{k} ::= {v}" for k, v in [("root", rules.pop("root"))] + list(rules.items()))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    sc = json.loads((here / "S1_1_output_schema.json").read_text(encoding="utf-8"))
    for name, kw in (("S1_1_output_grammar.ebnf", {}), ("S1_1_output_grammar_G2_cap20.ebnf", {"max_items": 20}), ("S1_1_output_grammar_G3_cap20_prefix.ebnf", {"max_items": 20, "prefix_consumed": True})):
        g = compile_schema(sc, **kw)
        (here / name).write_text(g, encoding="utf-8")
        print(name, len(g), "bytes,", g.count("\n") + 1, "rules")
