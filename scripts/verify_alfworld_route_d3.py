"""Verify delivered prompts and Worker contexts against recorded public prefixes."""
import run_alfworld_route_d3 as D


def main():
    checked_models=checked_workers=checked_entries=0
    selection=D.A.read(D.OUT/'selection.private.json')
    for i,task in enumerate(selection['tasks']):
        case=D.A.read(D.OUT/f'native/{i:02d}/case.private.json')
        guidance,directives=D.C.guidance(case['skills'])
        starts=[]
        for arm in 'GHF':
            folder=D.OUT/f'pairs/{i:02d}/{arm}'
            result=D.A.read(folder/'result.json')
            start=D.A.read(folder/'start.private.json')
            starts.append(start)
            assert result['start_sha256']==D.A.digest(start)
            prefix=[];state={};obs=case['initial']['observation'];commands=case['initial']['commands'];worker_indices=[]
            for record in result['records']:
                n=record['step'];worker_path=folder/'workers'/f'{n:02d}.json'
                if worker_path.exists():
                    receipt=D.A.read(worker_path)
                    context=D.C.context_view(case['goal'],obs,commands,D.public_history(case['initial'],prefix),state)
                    assert D.A.digest(context)==receipt['context_sha256']
                    assert receipt['code_sha256']==D.SHA
                    state=receipt['result'].get('state',{})
                    worker_indices.append(n);checked_workers+=1
                if record['request']:
                    wire=D.A.read(D.OUT/'requests'/record['request']['request_id']/'request.private.json')
                    if arm=='G':
                        user=D.C._build_step_user(case['goal'],obs,commands,[s['action'] for s in prefix],[s['observation'] for s in prefix],guidance)
                    else:user=D.full_user(case['goal'],obs,commands,case['initial'],prefix,guidance)
                    expected=dict(model='deepseek-flash',messages=[dict(role='system',content=D.C._build_system(directives)),dict(role='user',content=user)],
                        max_tokens=1024,temperature=0,thinking={'type':'disabled'},reasoning_effort='none',stream=False)
                    assert wire==expected
                    checked_models+=1
                assert record['before_observation']==obs and record['legal_before']==commands
                prefix.append(record['feedback']);obs=prefix[-1]['observation'];commands=prefix[-1]['commands']
            if worker_indices:
                gate=D.A.read(folder/'Entry.json');anchor=gate['anchor']
                assert worker_indices[0]==anchor+1 and D.entry(case['goal'],prefix[:anchor])[0]==anchor
                assert D.entry(case['goal'],prefix[:anchor-1])[0] is None
                assert D.A.digest(prefix[:anchor])==gate['public_prefix_sha256']
                # A Worker decline/error can only be the last invocation of this episode.
                assert all(D.A.read(folder/'workers'/f'{n:02d}.json')['result']['status']=='applied' for n in worker_indices[:-1])
                checked_entries+=1
        assert starts[0]==starts[1]==starts[2]
    result=dict(passed=True,model_requests_exactly_match_frozen_arm_configuration=checked_models,
        worker_contexts_exactly_match_public_prefix_and_state=checked_workers,first_placement_once_only_entries=checked_entries,
        initial_states_equal=len(selection['tasks']),full_history_not_truncated=True,other_arm_results_not_in_context=True)
    D.A.commit(D.REPORT/'Runtime_Input_Validation.json',result)
    print(result)


if __name__=='__main__':main()
