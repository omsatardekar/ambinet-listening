import json,sys
i=sys.argv[1]; R=sys.argv[2] if len(sys.argv)>2 else '.'
inp=json.load(open(f"{R}/output/inputs/encounter_{i}.json",encoding='utf-8'))
bp=json.load(open(f"{R}/scenario_blueprints/blueprint_{i}.json",encoding='utf-8'))
print(bp['spec'],bp['profile'],bp['complexity'],bp['combo'],bp['features'],bp['style'],'noise',bp.get('noise_level'),'plan',bp['plan_mode'],'assess',bp['assess_mode'])
for s in inp['segments']: print(s['segment_id'][3:],s['speaker_id'][-1],s['role'][:3],s['start_seconds'],s['text'])
