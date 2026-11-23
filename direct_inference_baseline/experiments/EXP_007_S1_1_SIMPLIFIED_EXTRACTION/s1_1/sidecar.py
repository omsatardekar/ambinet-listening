"""Model-visible transcript rendering and the per-encounter SIDECAR for S1.1.
The original transcript files are never modified. The sidecar keeps, for every model-visible line (in order): the original segment id, speaker id, role, times and the label shown to the model,
so that facts can later be traced back to the original segments. Roles are never inferred: UNKNOWN stays unknown and is flagged; two speakers sharing a role are flagged as ambiguous.
Pure library (no I/O)."""
from __future__ import annotations

SIDECAR_VERSION = "S1.1-sidecar-1.0.0"
ROLE_LABEL = {"DOCTOR": "doctor", "PATIENT": "patient", "NURSE": "nurse", "CAREGIVER": "caregiver", "FAMILY_MEMBER": "family_member", "CLINICAL_STAFF": "clinical_staff", "UNKNOWN": "unknown"}


def build_sidecar(inp: dict) -> dict:
    segs = inp["segments"]
    roles_by_role: dict[str, set] = {}
    for s in segs:
        roles_by_role.setdefault(s["role"], set()).add(s["speaker_id"])
    flags = []
    ambiguous = sorted(r for r, sp in roles_by_role.items() if len(sp) > 1)
    for r in ambiguous:
        flags.append({"kind": "ambiguous_role", "role": r, "speaker_ids": sorted(roles_by_role[r])})
    unmapped = sorted({s["role"] for s in segs if s["role"] not in ROLE_LABEL})
    for r in unmapped:
        flags.append({"kind": "unmapped_role", "role": r})
    n_unknown = sum(1 for s in segs if s["role"] == "UNKNOWN")
    if n_unknown:
        flags.append({"kind": "role_unavailable", "role": "UNKNOWN", "segments": n_unknown})
    lines = [{"line_index": i, "segment_id": s["segment_id"], "speaker_id": s["speaker_id"], "role": s["role"], "label": ROLE_LABEL.get(s["role"]), "start_seconds": s["start_seconds"],
              "end_seconds": s["end_seconds"]} for i, s in enumerate(segs)]
    return {"version": SIDECAR_VERSION, "encounter_id": inp.get("encounter_id"), "n_lines": len(lines), "roles_present": sorted({ROLE_LABEL.get(s["role"], s["role"]) for s in segs}),
            "speaker_to_role": {sp: r for r, sps in roles_by_role.items() for sp in sps}, "flags": flags, "lines": lines}


def render_r1(inp: dict) -> str:
    """R1: 'role: text' per line; no segment ids, no speaker ids, no times. Raises if a role has no label (never guessed)."""
    out = []
    for s in inp["segments"]:
        lab = ROLE_LABEL.get(s["role"])
        if lab is None:
            raise ValueError(f"role {s['role']!r} has no model-visible label; not guessed")
        out.append(f"{lab}: {s['text']}")
    return "\n".join(out)
