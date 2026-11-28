import json,sys
p={e['encounter_id']:e for e in json.load(open('plan/scenario_plan.json'))}
done=set(json.load(open('plan/done_ids.json')))
import glob,os
done|={os.path.basename(f)[6:11] for f in glob.glob('drafts/draft_*.json')}
rem=[i for i in sorted(p) if i not in done]
n=int(sys.argv[1]) if len(sys.argv)>1 else 12
print(len(rem),'remaining')
for i in rem[:n]:
    e=p[i];t=e['entity_targets']
    z={k:v for k,v in t.items() if k!='vitals_read_aloud_by'}
    print(f"{i} {e['specialty']} | {e['situation']} | {e['kind']} | spk {','.join(e['extra_speakers']) or '-'} | feat {','.join(e['special_features']) or '-'} | turns {e['target_turns']} | {e['style']['patient'].split(',')[0]}/{e['style']['doctor'].split(',')[0]}/{e['style']['dialect'][:5]}")
    print("   ",json.dumps(z,separators=(',',':')).replace('"',''), 'vitals_by',t['vitals_read_aloud_by'])
