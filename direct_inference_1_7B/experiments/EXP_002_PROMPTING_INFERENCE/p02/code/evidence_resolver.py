"""Backend evidence resolver for P02 v2.2.

The original transcript is the source of truth. A fact carries `refs` = transcript segment ids. The resolver looks each id up and returns the exact
original text, speaker id, role and times. It never invents, repairs, re-cases, truncates or drops a reference: an id that is not a segment id of THIS
transcript is reported as invalid and stays visible; a long list is flagged, never shortened."""
from __future__ import annotations

from dataclasses import dataclass, field

from p02_common import mmss

DEFAULT_MAX_REFS = 4


@dataclass
class ResolvedRef:
    ref: object
    ok: bool
    segment_id: str | None = None
    text: str | None = None
    speaker_id: str | None = None
    role: str | None = None                 # lower case, as in the gold labels
    start_seconds: float | None = None
    end_seconds: float | None = None
    start_timestamp: str | None = None      # MM:SS, rounded down (gold convention)
    end_timestamp: str | None = None
    problem: str | None = None

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("ref", "ok", "segment_id", "text", "speaker_id", "role", "start_seconds", "end_seconds", "start_timestamp", "end_timestamp", "problem")}


@dataclass
class RefFlag:
    kind: str            # invalid_reference | non_string_reference | excessive_references | no_references | duplicate_reference | refs_not_a_list
    location: str
    detail: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "location": self.location, "detail": self.detail}


class EvidenceResolver:
    def __init__(self, transcript: dict, max_refs: int = DEFAULT_MAX_REFS):
        segs = transcript["segments"]
        self.order = [s["segment_id"] for s in segs]
        self.by_id = {s["segment_id"]: s for s in segs}
        self.position = {sid: i for i, sid in enumerate(self.order)}
        self.max_refs = max_refs
        self.encounter_id = transcript.get("encounter_id")

    # --- single reference -------------------------------------------------------------------------------------------
    def resolve(self, ref) -> ResolvedRef:
        if not isinstance(ref, str):
            return ResolvedRef(ref=ref, ok=False, problem="non_string_reference")
        s = self.by_id.get(ref)                       # exact match only: no case folding, no zero padding, no nearest id
        if s is None:
            return ResolvedRef(ref=ref, ok=False, problem="invalid_reference")
        return ResolvedRef(ref=ref, ok=True, segment_id=s["segment_id"], text=s["text"], speaker_id=s["speaker_id"], role=str(s["role"]).lower(),
                           start_seconds=s["start_seconds"], end_seconds=s["end_seconds"],
                           start_timestamp=mmss(s["start_seconds"]), end_timestamp=mmss(s["end_seconds"]))

    # --- the refs of one fact ---------------------------------------------------------------------------------------
    def resolve_fact(self, refs, loc: str) -> tuple[list[ResolvedRef], list[RefFlag]]:
        flags: list[RefFlag] = []
        if refs is None or refs == []:
            return [], [RefFlag("no_references", loc, "the fact cites no transcript segment")]
        if not isinstance(refs, list):
            return [], [RefFlag("refs_not_a_list", loc, f"refs is {type(refs).__name__}, expected a list of segment ids")]
        out = [self.resolve(r) for r in refs]
        for r in out:
            if not r.ok:
                flags.append(RefFlag(r.problem, loc, f"{r.ref!r} is not a segment id of encounter {self.encounter_id}"))
        seen = set()
        for r in refs:
            key = r if isinstance(r, str) else repr(r)
            if key in seen:
                flags.append(RefFlag("duplicate_reference", loc, f"{key} is listed more than once (kept as given)"))
            seen.add(key)
        if len(refs) > self.max_refs:
            flags.append(RefFlag("excessive_references", loc, f"{len(refs)} references, limit {self.max_refs} (all kept)"))
        return out, flags

    # --- for the front end: what to show when a clinician clicks a fact --------------------------------------------
    def evidence_for(self, refs) -> list[dict]:
        """Original segments for the valid refs, in transcript order, exact text/speaker/times. Invalid refs are returned with ok=False, not skipped."""
        res = [self.resolve(r) for r in (refs or [])]
        valid = sorted((r for r in res if r.ok), key=lambda r: self.position[r.segment_id])
        return [r.as_dict() for r in valid] + [r.as_dict() for r in res if not r.ok]

    def speaker_table(self) -> list[dict]:
        """speaker_id -> lower-case role, in order of first appearance."""
        seen, out = set(), []
        for sid in self.order:
            s = self.by_id[sid]
            if s["speaker_id"] not in seen:
                seen.add(s["speaker_id"])
                out.append({"speaker_id": s["speaker_id"], "role": str(s["role"]).lower()})
        return out
