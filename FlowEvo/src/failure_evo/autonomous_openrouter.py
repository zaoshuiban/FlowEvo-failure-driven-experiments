"""Single-send GPT transport through OpenRouter; unchanged mechanism contract."""
import json,os,urllib.request
from .autonomous_mechanism import MechanismCompilerAdapter
from .contracts import canonical

class OpenRouterMechanismAdapter(MechanismCompilerAdapter):
    provider_origin='GPT_VIA_OPENROUTER'
    def preflight(self,request):
        if not self.mock and not os.environ.get('OPENROUTER_API_KEY'):
            raise PermissionError('OPENROUTER_API_KEY unavailable before reservation')
        base=super().preflight(request)
        schema=base['text']['format']
        body=dict(model='openai/'+self.model,messages=base['input'],max_tokens=request['max_tokens'],
            response_format=dict(type='json_schema',json_schema={k:v for k,v in schema.items() if k!='type'}),
            reasoning=dict(effort='medium'),stream=False,
            provider=dict(only=['openai'],allow_fallbacks=False,require_parameters=True))
        if len(canonical(body).encode())+256>self.max_wire_input_upper:raise ValueError('final OpenRouter wire limit')
        return body
    def _post(self,body):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        request=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=canonical(body).encode(),
            headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY'],'Content-Type':'application/json'})
        with urllib.request.build_opener(NoRedirect).open(request,timeout=min(300,self.budget.remaining_seconds)) as response:
            return json.load(response)
    def _normalize_response(self,raw):
        usage=raw.get('usage',{});choices=raw.get('choices',[]);choice=choices[0] if len(choices)==1 else {}
        # Preserve raw provider identity. Do not silently accept a routed other model.
        if raw.get('model') not in ('openai/'+self.model,'openai/'+self.config.model_version,self.model,self.config.model_version):
            raise ValueError('provider returned an unfrozen model')
        return dict(model=self.model,id=raw.get('id'),
            status='completed' if choice.get('finish_reason')=='stop' else 'incomplete',
            usage=dict(input_tokens=usage.get('prompt_tokens'),output_tokens=usage.get('completion_tokens'),total_tokens=usage.get('total_tokens')),
            output=[dict(type='message',content=[dict(type='output_text',text=choice.get('message',{}).get('content',''))])])
