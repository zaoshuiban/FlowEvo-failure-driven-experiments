import unittest
from copy import deepcopy
import run_alfworld_route_a_independent_confirmation as C


class Tests(unittest.TestCase):
    def data(self):
        return [dict(task=dict(group=str(i),game_sha256='g'+str(i),trajectory_sha256='t'+str(i))) for i in range(48)]

    def test_clean(self):
        self.assertTrue(C.check_isolation(self.data(),dict(malformed=[],protected_games=[]),[]))

    def test_any_source_identity_overlap_blocks(self):
        for field in ('group','game_sha256','trajectory_sha256'):
            r=dict(task=dict(group='other',game_sha256='other',trajectory_sha256='other'))
            r['task'][field]=self.data()[0]['task'][field]
            with self.assertRaises(PermissionError):C.check_isolation(self.data(),dict(malformed=[],protected_games=[r]),[])

    def test_online_reservation_cannot_be_borrowed(self):
        with self.assertRaises(PermissionError):C.check_isolation(self.data(),dict(malformed=[],protected_games=[]),[self.data()[0]])

    def test_missing_or_duplicate_groups_blocks(self):
        for rows in (self.data()[:47],self.data()[:47]+self.data()[:1]):
            with self.assertRaises(PermissionError):C.check_isolation(rows,dict(malformed=[],protected_games=[]),[])

    def test_unparseable_audit_blocks(self):
        with self.assertRaises(PermissionError):C.check_isolation(self.data(),dict(malformed=['receipt'],protected_games=[]),[])

    def test_real_candidate_accepted_not_published(self):
        root=C.ROOT/'runs/alfworld_route_a_targeted_revision_20261117_01'
        _,g=C.require_development(root)
        self.assertEqual(g['code_sha256'],'32feddc3d43c357bf0e84235d3b9d89e2822ca7b5efe06c66b0c74c20f816553')
        self.assertFalse(g['published'])


if __name__=='__main__':unittest.main()
