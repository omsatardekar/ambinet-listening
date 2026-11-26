"""Deterministic repair of the few malformed model outputs (no dependencies).

parse_with_repair(text) -> (obj | None, notes)   notes lists every repair applied ([] = parsed as generated).
Only a few repair rules (R1 to R5), all learned from the 6 invalid outputs of the 973-encounter test run; each is applied only at the exact place json reports an error:
  R1  a key started but never written:        ..."description":"text","}      ->  ..."description":"text"}
  R2  a list not closed before the next key:  "related_entities":["a","reported_by":"x"  ->  "related_entities":["a"],"reported_by":"x"
  R5  one extra closing brace left by R1
  R3  a quote mix-up inside a string:         "Scabies','reported_by":"x"      ->  "Scabies","reported_by":"x"
Fields the model skipped stay absent and are filled with their default by expand() (so the repaired record has empty values there, and `notes`
is returned so the caller can flag the record for review). If the text is still not valid after the rules: return (None, notes) -> regenerate once, then fail with clinician review.
"""
import json, re

def _try(t):
    try: return json.loads(t), None
    except json.JSONDecodeError as e: return None, e

def _close(t):
    st, ins = [], False
    esc = False
    for c in t:
        if ins:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': ins = False
        elif c == '"': ins = True
        elif c in "{[": st.append("}" if c == "{" else "]")
        elif c in "}]" and st: st.pop()
    return t + "".join(reversed(st))

def parse_with_repair(text, max_fixes=12, _dedupe=True):
    notes = []
    t = text.strip()
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i: t = t[i:j + 1]
    t0 = t
    for _ in range(max_fixes + 1):
        obj, err = _try(t)
        if err is None: return obj, notes
        p = err.pos
        # R1: dangling ,"} or ,"}}], (a key opened and closed by the following brackets)
        m = re.search(r',"[}\]\[{,]+"$', t[max(0, p - 24): p]) if err.msg.startswith("Expecting ':'") else None
        if m:
            k = max(0, p - 24) + m.start(); t = t[:k] + m.group()[2:] + t[p:]; notes.append(f"R1 dangling key at {k}"); continue
        # R1b: same, at the very end of the text (key never closed, output stopped early): drop it and close the open brackets (R4)
        m = re.search(r',"[}\]\[{,]*$', t)
        if m and err.msg.startswith("Unterminated string"):
            t = _close(t[:m.start()] + t[m.start() + 2:]); notes.append("R1b dangling key at end; brackets closed"); continue
        # R5: one closing brace too many before the list close (left over after R1):  "}}],  ->  "}],
        if err.msg.startswith("Expecting ','") and t[p:p + 2] == "}]":
            t = t[:p] + t[p + 1:]; notes.append(f"R5 extra brace at {p}"); continue
        # R3: ',' written where "," belongs, inside a string, shortly before the error
        k = t.rfind("','", max(0, p - 120), p + 1)
        if k >= 0 and err.msg.startswith("Expecting ','"):
            t = t[:k] + '","' + t[k + 3:]; notes.append(f"R3 quote mix-up at {k}"); continue
        # R7: a key written as the value of the previous key:  "duration":"reported_by":"patient"  ->  "reported_by":"patient"  (the empty field stays absent)
        if err.msg.startswith("Expecting ','") and p < len(t) and t[p] == ":":
            m = re.search(r'([,{])"[a-z_]+":("[a-z_]+")$', t[max(0, p - 60): p])
            if m:
                k = max(0, p - 60) + m.start()
                t = t[:k] + m.group(1) + t[k + len(m.group(0)) - len(m.group(2)):]; notes.append(f"R7 key written as value at {k}"); continue
        # R2: a key written inside a list: the error sits at the ':' after the key string; close the list before that key
        if err.msg.startswith("Expecting ','") and p < len(t) and t[p] == ":":
            ks = t.rfind('"', 0, p - 1)           # opening quote of the key string (closing quote is at p-1)
            if ks > 0 and t[ks - 1] == ",":
                t = t[:ks - 1] + '],' + t[ks:]; notes.append(f"R2 list closed before key at {ks}"); continue
        break
    obj, err = _try(t)
    if err is None: return obj, notes
    # R6 (only when everything above failed): repetition loop. The model sometimes repeats one list item until the token limit. Drop every item that is an
    # exact copy of an earlier item (same text, same evidence), cut the unfinished last item, close the open brackets.
    fixed = _dedupe_and_close(t0) if _dedupe else None
    if fixed is not None:
        obj, n2 = parse_with_repair(fixed, max_fixes, _dedupe=False)      # the other rules may still be needed on the shortened text
        if obj is not None: return obj, notes + ["R6 repeated items removed; unfinished tail cut; brackets closed"] + n2
    return None, notes + ["unrepaired: " + err.msg]


def _dedupe_and_close(t):
    """Split the text into flat items {...} (no nested braces) and drop exact repeats. Returns repaired text or None."""
    seen, out, pos, last_end = set(), [], 0, 0
    pieces = []
    for m in re.finditer(r"\{[^{}]*\}", t):          # flat objects only; list items of the compact format are flat
        pieces.append(m)
    if len(pieces) < 4: return None
    res, cursor, dropped = [], 0, 0
    for m in pieces:
        item = m.group()
        if item in seen:
            res.append(t[cursor:m.start()]); cursor = m.end(); dropped += 1
            if t[cursor:cursor + 1] == ",": cursor += 1
        else:
            seen.add(item)
    if not dropped: return None
    res.append(t[cursor:])
    t2 = "".join(res)
    for _ in range(4):
        t2 = re.sub(r",\s*$", "", t2)
        cand = re.sub(r",(\s*[\]}])", chr(92) + "1", _close(t2))
        try:
            json.loads(cand); return cand
        except json.JSONDecodeError:
            k = t2.rfind("}")                    # cut an unfinished tail back to the last complete object
            if k < 0: return None
            t2 = t2[:k + 1]
    return cand
