import json,sys,glob,os
p={e['encounter_id']:e for e in json.load(open('plan/scenario_plan.json'))}
for i in sys.argv[1:]:
    e=p[i.zfill(5)]; t=e['entity_targets']
    print(i,"|",e['specialty'],"|",e['situation'],"|",e['kind'],"| extra:",e['extra_speakers'],"| turns",e['target_turns'],"| age",e['patient_age'])
    print("  T:",{k:v for k,v in t.items() if v not in (0,'none',None)}, "zeros:",[k for k,v in t.items() if v in (0,'none','not_discussed')])
    print("  F:",e['special_features'],e['feature_notes'])
    print("  S:",e['style'])
