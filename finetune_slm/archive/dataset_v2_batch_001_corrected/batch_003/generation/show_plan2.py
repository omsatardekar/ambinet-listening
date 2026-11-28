import json,sys,glob,os
p={e['encounter_id']:e for e in json.load(open('plan/scenario_plan.json'))}
done={os.path.basename(f)[6:11] for f in glob.glob('drafts/draft_*.json')}
CX={"symptoms":"S","negative_findings":"N","medications":"M","allergies":"A","vital_signs":"V","physical_examination":"X","review_of_systems":"R","past_medical_history":"H","surgical_history":"Sg","family_history":"F","social_history":"So","clinical_assessment":"D","investigations":"P","follow_up":"Fu"}
skip={x.zfill(5) for x in sys.argv[3].split(',')} if len(sys.argv)>3 else set()
rem=[i for i in sorted(p) if i not in done and i not in skip]
a=int(sys.argv[1]); n=int(sys.argv[2])
for i in rem[a:a+n]:
    e=p[i];t=e['entity_targets']
    s=" ".join(f"{CX[k]}{t[k]}" for k in CX)
    print(f"{i}|{e['specialty'][:12]}|{e['situation']}|{e['kind'][:10]}|{','.join(x[:3] for x in e['extra_speakers']) or '-'}|{','.join(e['special_features']) or '-'}|{e['style']['patient'].split(',')[0][:10]}/{e['style']['doctor'].split(',')[0][:8]}/{e['style']['dialect'][:3]}\n   {s} vit={t['vitals_read_aloud_by'] or '-'}")
