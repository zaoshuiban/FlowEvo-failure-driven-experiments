import requests,json,pathlib,concurrent.futures
P=pathlib.Path(__file__).parent
urls={'apps':'https://huggingface.co/api/datasets/codeparrot/apps','contests':'https://huggingface.co/api/datasets/deepmind/code_contests','lcb':'https://huggingface.co/api/datasets/livecodebench/code_generation_lite','pricing':'https://api-docs.deepseek.com/quick_start/pricing/'}
def get(k,u):
 try:
  r=requests.get(u,timeout=45);r.raise_for_status();(P/(k+'_source.json' if k!='pricing' else 'pricing.html')).write_text(r.text);print(k,r.status_code,len(r.content),flush=True)
 except Exception as e:print(k,type(e).__name__,str(e),flush=True)
with concurrent.futures.ThreadPoolExecutor(4) as ex:list(ex.map(lambda kv:get(*kv),urls.items()))
