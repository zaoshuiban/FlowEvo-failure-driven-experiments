"""Explicit DeepSeek variant; same v2 mechanism/code contracts and host checks."""
from dataclasses import dataclass
from .autonomous_generation import DeepSeekCompilerAdapter
from .autonomous_mechanism import GeneratorConfig,MechanismCompilerAdapter
from .contracts import canonical
from .model_api import configured_api_key

@dataclass(frozen=True)
class DeepSeekMechanismConfig(GeneratorConfig):
    def __post_init__(self):
        if self.model!='deepseek-flash' or not self.model_version or not self.price_source or not self.price_checked_at:
            raise ValueError('explicit DeepSeek model/version/quote required')
        if any(type(v) is not int or v<=0 for v in (self.input_microusd_per_million,self.output_microusd_per_million)):
            raise ValueError('explicit positive quote required')

class DeepSeekMechanismAdapter(MechanismCompilerAdapter):
    provider_origin='DEEPSEEK'
    def _authorize(self):
        DeepSeekCompilerAdapter._authorize(self)
        if not self.mock and self.budget.config['token_rate_microusd_per_million']<max(self.config.input_microusd_per_million,self.config.output_microusd_per_million):
            raise ValueError('reservation rate below frozen quote')
    def preflight(self,request):
        if not self.mock and not configured_api_key():raise PermissionError('DEEPSEEK_API_KEY unavailable before reservation')
        base=super().preflight(request)
        messages=base['input']
        messages[0]['content']+='\nRequired JSON schema: '+canonical(base['text']['format']['schema'])
        body=dict(model=self.model,messages=messages,max_tokens=request['max_tokens'],
            thinking={'type':'disabled'},reasoning_effort='none',temperature=0,stream=False,
            response_format={'type':'json_object'})
        if len(canonical(body).encode())+256>self.max_wire_input_upper:raise ValueError('final DeepSeek wire limit')
        return body
    _post=DeepSeekCompilerAdapter._post
    _normalize_response=DeepSeekCompilerAdapter._normalize_response
