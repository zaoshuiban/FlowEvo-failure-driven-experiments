"""Offline deterministic adapter acceptance entry. No API client or key access."""
import argparse,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent/'src'))
from failure_evo import Controller,Budget,Fingerprint
def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',required=True);p.add_argument('--output',required=True);args=p.parse_args();fixture=json.loads(pathlib.Path(args.fixture).read_text());responses=iter(fixture['responses']);checks=iter(fixture['public_checks'])
 context=Fingerprint(**fixture['fingerprint'])
 result=Controller(lambda request:next(responses),lambda task,code:next(checks),context,max_output=fixture.get('max_output',32768)).solve(fixture['task'],Budget(**fixture.get('budget',{})))
 pathlib.Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result['status'],result['budget'])
if __name__=='__main__':main()
