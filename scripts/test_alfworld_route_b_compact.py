import copy
import unittest
from alfworld_.route_b_compact_projection import encode,decode,prepare,validate
from test_alfworld_route_b_b0 import cohort

class CompactTests(unittest.TestCase):
    def test_lossless_literals_unicode_and_repetition(self):
        p={'goal':'$0','steps':['重复原文','重复原文'],'value':[None,True,False,0,1,2.5,{'a':'Nothing happens.'}]}
        self.assertEqual(decode(encode(p)),p)
    def test_bad_reference_unused_table_and_relabel_rejected(self):
        p=encode({'x':'original'})
        for ref in ('$999','$01','literal'):
            bad=copy.deepcopy(p);bad['data']['x']=ref
            with self.assertRaises(ValueError):decode(bad)
        bad=copy.deepcopy(p);bad['strings'].append('extra')
        with self.assertRaises(ValueError):decode(bad)
        c=cohort();result=prepare(c);result['wires']['F']['messages'][1]['content']='changed'
        with self.assertRaises(PermissionError):validate(result,c)
    def test_scarce_strata_symmetric_no_duplication(self):
        c=cohort();c['episodes'][0]['task']['task_type']='scarce';c['episodes'][4]['task']['task_type']='scarce'
        r=prepare(c);s=next(s for s in r['strata'] if s['task_type']=='scarce')
        self.assertEqual(s['status'],'SCARCE_EXPLORATORY_ONLY');self.assertEqual(s['per_arm_selected'],1)
        self.assertFalse(r['full_quota_coverage'])
        for a in ('S','F'):self.assertEqual(len(r['selection'][a]),len(set(r['selection'][a])))
        self.assertEqual(len(r['selection']['S']),len(r['selection']['F']))
        self.assertEqual(r['inputs']['T']['examples'],[])
    def test_zero_source_stays_blocked(self):
        c=cohort();c['episodes'][0]['task']['task_type']='S_only';r=prepare(c)
        self.assertEqual(next(s['status'] for s in r['strata'] if s['task_type']=='S_only'),'BLOCKED_NO_PAIRED_SOURCE')
    def test_capacity_no_resampling_or_removal(self):
        a=prepare(cohort());b=prepare(cohort(),max_wire_bytes=1)
        self.assertFalse(b['byte_limit_passed']);self.assertEqual(a['selection'],b['selection'])
        self.assertEqual(a['inputs'],b['inputs'])
    def test_same_encoding_system_and_settings_for_all_arms(self):
        r=prepare(cohort());w=list(r['wires'].values())
        for x in w:self.assertEqual(x['messages'][0],w[0]['messages'][0])
        for a in 'TSF':
            import json
            self.assertEqual(decode(json.loads(r['wires'][a]['messages'][1]['content'])),r['inputs'][a])
        self.assertNotIn('PRIVATE_SUFFIX',str(r['inputs']['F']))

if __name__=='__main__':unittest.main()
