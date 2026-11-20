"""Plain-text (Markdown) rendering of a normalised note: for copy, download and the saved .md file. Same content as the screen, no extra facts."""
from __future__ import annotations

ND = "Not documented"


def _v(x: str) -> str:
    return x.strip() if x and x.strip() else ND


def _bullets(items: list[str], indent: str = "") -> list[str]:
    return [f"{indent}- {i}" for i in items] if items else [f"{indent}- {ND}"]


def render(note: dict, review: dict | None = None) -> str:
    enc, s, o, a, p, cr = note["encounter"], note["subjective"], note["objective"], note["assessment"], note["plan"], note["clinician_review"]
    L: list[str] = []
    L += ["# SOAP NOTE (DRAFT FOR CLINICIAN REVIEW)", "",
          f"**Note type:** {note['note_type']}  ",
          f"**Encounter:** {_v(enc['encounter_id'])}  |  **Date of service:** {_v(enc['date_of_service'])}  |  **Patient:** {_v(enc['patient_age_sex'])}  ",
          f"**Visit type:** {_v(enc['visit_type'])}  |  **Present:** {', '.join(enc['participants']) or ND}  |  **Informant(s):** {', '.join(enc['informants']) or ND}", ""]

    L += ["## S: SUBJECTIVE", "", f"**Chief complaint (CC):** {_v(s['chief_complaint'])}", "", "**History of present illness (HPI):**", _v(s["hpi"]), ""]
    el = {k: v for k, v in s["hpi_elements"].items() if v}
    if el:
        L += [", ".join(f"{k.capitalize()}: {v}" for k, v in el.items()), ""]
    ros = s["review_of_systems"]
    L += ["**Review of systems (ROS):**"]
    L += [f"- Positive: " + ("; ".join(f"{i['system']}: {i['finding']}" if i["system"] else i["finding"] for i in ros["positive"]) or ND)]
    L += [f"- Negative: " + ("; ".join(f"{i['system']}: {i['finding']}" if i["system"] else i["finding"] for i in ros["negative"]) or ND)]
    if ros["not_reviewed"]:
        L += [f"- Not reviewed: {ros['not_reviewed']}"]
    L += ["", "**Past medical history (PMH):**", *_bullets(s["past_medical_history"]), "", "**Past surgical history (PSH):**", *_bullets(s["past_surgical_history"]), "",
          "**Family history (FH):**", *_bullets(s["family_history"]), "", "**Social history (SH):**", *_bullets(s["social_history"]), "", "**Medications:**"]
    if s["medications"]:
        for m in s["medications"]:
            bits = [x for x in (m["dose"], m["route"], m["frequency"]) if x]
            L.append(f"- {m['name']}" + (f" {' '.join(bits)}" if bits else "") + (f" [{m['status']}]" if m["status"] else "") + (f" ({m['comment']})" if m["comment"] else ""))
    else:
        L.append(f"- {ND}")
    al = s["allergies"]
    L += ["", "**Allergies:**"]
    if al["status"] == "reported":
        L += [f"- {i['substance']}" + (f": {i['reaction']}" if i["reaction"] else " (reaction not documented)") + (f" ({i['comment']})" if i["comment"] else "") for i in al["items"]]
    elif al["status"] == "none_reported":
        L += ["- No known allergies reported"]
    else:
        L += [f"- {ND}"]
    if al["comment"]:
        L += [f"- {al['comment']}"]

    L += ["", "## O: OBJECTIVE", "", "**Vital signs:**"]
    L += [f"- {v['name']}: {v['value']} {v['unit']}".rstrip() + (f" ({v['comment']})" if v["comment"] else "") for v in o["vital_signs"]] or [f"- {ND}"]
    L += ["", "**Physical examination:**"]
    L += [f"- {e['system'] + ': ' if e['system'] else ''}{e['finding']}" for e in o["physical_exam"]] or [f"- {ND}"]
    if o["diagnostics"]:
        L += ["", "**Diagnostics reviewed:**"] + [f"- {d['item']}: {d['result']}" + (f" ({d['comment']})" if d["comment"] else "") for d in o["diagnostics"]]
    if o["comment"]:
        L += ["", o["comment"]]

    L += ["", "## A: ASSESSMENT", "", _v(a["summary"]), ""]
    for pr in a["problems"]:
        head = f"{pr['number']}. {pr['problem']}" + (f" ({pr['status']})" if pr["status"] else "")
        L.append(f"**{head}**")
        if pr["clinician_impression"]:
            L.append(f"   Clinician impression: {pr['clinician_impression']}")
        if pr["reasoning"]:
            L.append(f"   {pr['reasoning']}")
        if pr["icd10_suggestion"]:
            L.append(f"   Suggested ICD-10-CM (requires coder/clinician verification): {pr['icd10_suggestion']['code']} {pr['icd10_suggestion']['description']}".rstrip())
    if not a["problems"]:
        L.append(ND)
    if a["differential"]:
        L += ["", "**Differential:** " + "; ".join(a["differential"])]

    L += ["", "## P: PLAN", ""]
    titles = {pr["number"]: pr["problem"] for pr in a["problems"]}
    for bp in p["by_problem"]:
        L.append(f"**{bp['problem_number']}. {titles.get(bp['problem_number'], 'Problem')}**")
        for label, key in (("Diagnostics", "diagnostics"), ("Treatment", "treatment"), ("Patient education", "patient_education"), ("Referrals", "referrals")):
            if bp[key]:
                L.append(f"   {label}: " + "; ".join(bp[key]))
        if bp["follow_up"]:
            L.append(f"   Follow-up: {bp['follow_up']}")
    if not p["by_problem"]:
        L.append(ND)
    L += ["", "**Return precautions:**", *_bullets(p["return_precautions"]), "", f"**Follow-up:** {_v(p['follow_up'])}"]
    if p["care_coordination"]:
        L += ["", "**Care coordination:**", *_bullets(p["care_coordination"])]

    L += ["", "## CLINICIAN REVIEW", ""]
    verify = list(cr["items_to_verify"]) + list((review or {}).get("system_checks", []))
    if verify:
        L += ["**Items to verify:**"] + [f"- {i['topic']}: {i['reason']}" for i in verify]
    if cr["documentation_gaps"]:
        L += ["", "**Documentation gaps:**", *_bullets(cr["documentation_gaps"])]
    L += ["", f"_{cr['attestation']}_", ""]
    return "\n".join(L)
