def repair_operator(context):
    code = context['candidate_code']
    if 'intt(' not in code:
        return {'status':'declined','reason':'fixture out of scope'}
    return {'status':'applied','candidate_code':code.replace('intt(', 'int(')}
