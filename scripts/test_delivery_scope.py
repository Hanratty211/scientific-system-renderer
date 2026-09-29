"""Small regression suite for preserving system-level requests."""
import unittest
from validate_delivery_scope import validate


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.contract={'requested_views':['architecture'],'system_boundary':'Source to core to output',
                       'required_components':['source','core','output'],
                       'required_relationships':[{'source':'source','target':'core','representation':'physical'},
                                                 {'source':'core','target':'output','representation':'field'}],
                       'required_paths':[['source','core','output']]}
        self.manifest={'views':[{'type':'architecture','shows_components':['source','core','output']}],
                       'components':[{'id':x} for x in ['source','core','output']],
                       'connections':[{'source':{'component':e['source']},'target':{'component':e['target']},'representation':e['representation']} for e in self.contract['required_relationships']]}

    def test_complete(self):
        self.assertEqual(validate(self.contract,self.manifest),[])

    def test_device_scope_rejected(self):
        self.manifest['views'][0]['type']='component-sheet'
        self.assertTrue(validate(self.contract,self.manifest))

    def test_disconnected_inventory_rejected(self):
        self.manifest['connections']=[]
        self.assertTrue(validate(self.contract,self.manifest))

    def test_wrong_medium_class_rejected(self):
        self.manifest['connections'][1]['representation']='physical'
        self.assertTrue(validate(self.contract,self.manifest))

    def test_missing_visible_output_rejected(self):
        self.manifest['views'][0]['shows_components'].remove('output')
        self.assertTrue(validate(self.contract,self.manifest))

    def test_device_views_cannot_be_combined_to_fake_system(self):
        self.manifest['views']=[{'type':'architecture','shows_components':[x]} for x in ['source','core','output']]
        self.assertTrue(validate(self.contract,self.manifest))

    def test_missing_contract_rejected(self):
        self.assertTrue(validate({},self.manifest))

    def test_unlocked_requirements_rejected(self):
        self.contract['required_paths']=[]
        self.assertTrue(validate(self.contract,self.manifest))

    def test_requested_device_is_valid(self):
        self.manifest['views'][0]['type']='component-sheet'
        self.assertEqual(validate({'requested_views':['component-sheet']},self.manifest),[])

    def test_malformed_request_rejected(self):
        for bad in ('architecture', ['architectur'], None, [None]):
            with self.subTest(bad=bad):
                self.assertTrue(validate({'requested_views':bad},{}))

    def test_blank_boundary_rejected(self):
        self.contract['system_boundary']='   '
        self.assertTrue(validate(self.contract,self.manifest))

    def test_every_requested_view_required(self):
        self.contract['requested_views'].append('physical-setup')
        self.assertTrue(validate(self.contract,self.manifest))

    def test_alias_accepted(self):
        self.contract['requested_views']=['architecture_overview']
        self.assertEqual(validate(self.contract,self.manifest),[])

    def test_hidden_control_endpoint_rejected(self):
        self.contract['required_relationships'].append({'source':'controller','target':'core','representation':'logical'})
        self.manifest['components'].append({'id':'controller'})
        self.manifest['connections'].append({'source':{'component':'controller'},'target':{'component':'core'},'representation':'logical'})
        self.assertTrue(validate(self.contract,self.manifest))

    def test_parallel_branches_cannot_share_one_connection(self):
        self.contract['required_relationships'].append(dict(self.contract['required_relationships'][0]))
        self.assertTrue(validate(self.contract,self.manifest))

    def test_optional_relationship_identity_preserved(self):
        for key, value in [('id','command'),('medium','data'),('source_port','control-out'),('target_port','control-in')]:
            with self.subTest(key=key):
                self.contract['required_relationships'][0][key]=value
                self.assertTrue(validate(self.contract,self.manifest))
                del self.contract['required_relationships'][0][key]

    def test_exact_parallel_relationships_accepted(self):
        for name in ('power','command'):
            self.contract['required_relationships'].append({'source':'core','target':'output','representation':'physical','id':name,'medium':name})
            self.manifest['connections'].append({'source':{'component':'core'},'target':{'component':'output'},'representation':'physical','id':name,'medium':name})
        self.assertEqual(validate(self.contract,self.manifest),[])

    def test_self_loop_cannot_fake_system_path(self):
        self.contract['required_paths']=[['core','core']]
        self.assertTrue(validate(self.contract,self.manifest))

    def test_unknown_constraint_rejected(self):
        self.contract['required_relationships'][0]['ignored_constraint']='must-not-ignore'
        self.assertTrue(validate(self.contract,self.manifest))

    def test_bad_requirement_types_rejected(self):
        for key in ('required_components','required_relationships','required_paths'):
            previous=self.contract[key]
            for bad in (None, 'unresolved', [{}]):
                with self.subTest(key=key,bad=bad):
                    self.contract[key]=bad
                    self.assertTrue(validate(self.contract,self.manifest))
            self.contract[key]=previous


if __name__=='__main__':unittest.main()
