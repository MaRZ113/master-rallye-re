import copy,math,struct,unittest
from master_rallye.game_camera import gameplay_mode,vertical_fov,fixed_pose
from master_rallye.workshop.camera_live import packet,fit_follow_draft,draft_pose,projected_bounds
from master_rallye.addon_sdk.camera_profile import bind_camera_profile


class Camera2Tests(unittest.TestCase):
    def test_auto_framing_is_bounded_preview_draft(self):
        params={'FOV':78.,'Dist Front':14.,'Dist Back':4.2,'Dist Up':.65}
        ext={'half_length_m':2.62,'height_m':2.02}
        from master_rallye.game_camera import static_pose
        report={'mode':gameplay_mode(0),'identity':{'current':ext,'minimum':[-1.04,-.6,-2.87],'maximum':[1.04,1.94,2.38]},'poses':{'modified':static_pose(ext,params)},'parameters':{'modified':params}}
        before=copy.deepcopy(report);fields=fit_follow_draft(report,params)
        envelope=projected_bounds(draft_pose(report,fields),{'minimum':report['identity']['minimum'],'maximum':report['identity']['maximum']},16/9)
        self.assertLessEqual(max(abs(x)for values in envelope.values()for x in values),.9)
        self.assertEqual(report,before);self.assertLess(fields['Dist Front'],params['Dist Front'])

    def test_five_modes_are_three_follow_two_fixed(self):
        self.assertEqual([(gameplay_mode(i)['kind'],gameplay_mode(i)['index'])for i in range(5)],[('follow',0),('follow',1),('follow',2),('fixed',0),('fixed',1)])
        for v in (-1,5,True,'0'):
            with self.assertRaises(ValueError):gameplay_mode(v)

    def test_source_linear_aspect_rule(self):
        self.assertEqual(vertical_fov(90,1920,1080),50.625)
        self.assertEqual(vertical_fov(90,480,640),90)
        for v in (float('nan'),0,-1):
            with self.assertRaises(ValueError):vertical_fov(90,v,480)

    def test_fixed_initializer_uses_source_bounds_not_xml_offsets(self):
        b={'minimum':[-1,-.2,-2.5],'maximum':[1,1.8,2.5]}
        p={'Type':0,'FOV':90,'Dist forward/back':99}
        a=fixed_pose(b,p);self.assertAlmostEqual(a['eye'][2],2.38);self.assertAlmostEqual(a['eye'][1],1.7)
        p['Type']=1;self.assertAlmostEqual(fixed_pose(b,p)['eye'][1],.5)

    def test_live_packet_bounded_and_typed(self):
        pose={'eye':[0,2,-6],'target':[0,0,14],'source_fov_degrees':90}
        self.assertEqual(len(packet(pose)),48)
        for bad in (float('nan'),0,180):
            with self.assertRaises(ValueError):packet({**pose,'source_fov_degrees':bad})
        for aspect in (-1,.1,5):
            with self.assertRaises(ValueError):packet(pose,aspect=aspect)
        with self.assertRaises(ValueError):packet(pose,mode=5)

    def test_parameter_schema_rejects_unqualified_fields_before_model(self):
        p={'version':1,'policy':'native_follow_extents','car_id':28,'runtime_family':'Test','source_model_sha256':'0'*64,'follow_extents':{'half_length_m':2.,'height_m':1.5}}
        for overrides in ({'fixed0':{'Dist Up':1.}}, {'follow0':{'FOV':float('nan')}},{'replay':{'FOV':90}},{'follow0':{'Smooth':.3}},{'follow0':{'FOV':180}}):
            with self.assertRaises(ValueError):bind_camera_profile({**p,'mode_overrides':overrides},b'')


if __name__=='__main__':unittest.main()
