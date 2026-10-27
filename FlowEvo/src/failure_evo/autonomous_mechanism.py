"""V2 typed mechanism proposal; no causal or permission assertion from a model."""
from dataclasses import dataclass,asdict
import json
from .autonomous_generation import GPTCompilerAdapter,SOURCE_CONTRACT
from .contracts import canonical,fingerprint

VERSION='autonomous-executable-mechanism-v2'
TEXT=('failure_pattern','root_cause_hypothesis','transferable_operation','expected_benefit')
LISTS=('source_evidence_ids','applicability_conditions','refusal_conditions','counterexamples','unresolved_uncertainties')
SCHEMA=dict(type='object',additionalProperties=False,required=['decision','suggested_operator_kind',*TEXT,*LISTS],properties={
    'decision':dict(type='string',enum=['PROPOSE','HYPOTHESIS_ONLY','NO_MECHANISM']),
    'suggested_operator_kind':dict(type='string',enum=['code_repair','task_solver']),
    **{k:dict(type='string') for k in TEXT},**{k:dict(type='array',items={'type':'string'}) for k in LISTS}})

def parse_mechanism(value):
    if not isinstance(value,dict) or set(value)!=set(SCHEMA['required']):raise ValueError('mechanism exact fields')
    if value['decision'] not in SCHEMA['properties']['decision']['enum'] or value['suggested_operator_kind'] not in ('code_repair','task_solver'):
        raise ValueError('unknown decision/operator capability')
    if any(not isinstance(value[k],str) or not 1<=len(value[k].strip())<=6000 for k in TEXT):raise ValueError('bounded mechanism text required')
    for k in LISTS:
        if not isinstance(value[k],list) or len(value[k])>32 or any(not isinstance(x,str) or not 1<=len(x.strip())<=2000 for x in value[k]):
            raise ValueError('bounded mechanism list: '+k)
    if not all(value[k] for k in ('source_evidence_ids','applicability_conditions','refusal_conditions','unresolved_uncertainties')):
        raise ValueError('evidence, scope, refusal and uncertainties required')
    return value

@dataclass(frozen=True)
class GeneratorConfig:
    model: str
    model_version: str
    input_microusd_per_million: int
    output_microusd_per_million: int
    price_source: str
    price_checked_at: str
    def __post_init__(self):
        if not self.model.startswith('gpt-') or not self.model_version or not self.price_source or not self.price_checked_at:raise ValueError('explicit GPT model/version/quote required')
        if any(type(v) is not int or v<=0 for v in (self.input_microusd_per_million,self.output_microusd_per_million)):raise ValueError('explicit positive quote required')
    def estimate_microusd(self,input_tokens,output_tokens):
        return (input_tokens*self.input_microusd_per_million+output_tokens*self.output_microusd_per_million+999999)//1000000

class MechanismCompilerAdapter(GPTCompilerAdapter):
    protocol=VERSION
    hypothesis_schema=SCHEMA
    hypothesis_parser=staticmethod(parse_mechanism)
    source_contract=SOURCE_CONTRACT+'''\nSupported kinds, selected by the UNVERIFIED hypothesis:
code_repair: inspect the supplied current program and implement a deterministic transformation.
task_solver: on a public stdio programming task, synthesize a COMPLETE executable
candidate program implementing your learned deterministic algorithm. candidate_code
is the candidate solution, not an instruction to another model. You may receive an
empty candidate_code before native solving. Both kinds use repair_operator(context)
and the same applied/declined/error contract. No direct scalar/JSON answer capability,
no mathematical gold-answer access. Host executes the exact returned program in Linux.
Do not assume a task ID determines applicability. Never use sample-answer lookups.
Document complexity, resources, input/output contract and suggested properties in
applicability/description. If not reliably programmable, decline instead.\n'''
    def __init__(self,*args,config,**kwargs):
        self.config=config
        if kwargs.get('model',config.model)!=config.model:raise ValueError('generator config mismatch')
        kwargs['model']=config.model
        super().__init__(*args,**kwargs)
    def _authorize(self):
        super()._authorize()
        if not self.mock:
            if self.budget.config['token_rate_microusd_per_million']<max(self.config.input_microusd_per_million,self.config.output_microusd_per_million):
                raise ValueError('reservation rate below frozen quote')
    def preflight(self,request):
        if not request.get('discovery',{}).get('evidence'):raise ValueError('admitted failure evidence required')
        if request['phase']!='induction':
            h=parse_mechanism(json.loads(request['specification']))
            if h['decision']!='PROPOSE' or set(h['source_evidence_ids'])!=set(request['evidence_ids']):raise ValueError('hypothesis evidence or decision mismatch')
        # Existing base only copies discovery, hypothesis and bounded public diagnostics.
        req=dict(request)
        if request['phase']=='revision':
            req['source_diagnostics']=request.get('design_feedback',request.get('source_diagnostics',{}))
        body=super().preflight(req)
        if request['phase']=='induction':
            body['input'][0]['content']+=' Return HYPOTHESIS_ONLY for a plausible but not executable conjecture. source_evidence_ids must name exactly the supplied events. suggested_operator_kind must be code_repair or task_solver; neither grants authority.'
        if len(canonical(body).encode())+256>self.max_wire_input_upper:raise ValueError('mechanism wire limit')
        return body
    def __call__(self,request):
        value=super().__call__(request)
        value['generator_config']=asdict(self.config)
        u=value['usage']
        if all(type(u.get(k)) is int and u[k]>=0 for k in ('input_tokens','output_tokens')):
            value['quoted_cost_estimate_microusd']=self.config.estimate_microusd(u['input_tokens'],u['output_tokens'])
        return value
