import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from master_rallye.addon_sdk.gt4_source import Reader,vif,shape_geometry,translate_pass,modelset,unpack_uv,unpack_normals
from master_rallye.addon_sdk.gt4_commands import command_graph,binding_trace

class GT4Tests(unittest.TestCase):
    def test_numeric_material_names_are_not_inputs(self):
        r=translate_pass(['AlphaFunction(GREATER, 0)'])
        self.assertEqual(r['route'],'alpha_test');self.assertEqual(r['state']['alpha_ref'],0)
    def test_special_passes_are_not_opaque(self):
        cases=[(['ColorMask(0xFF000000)'],'alpha_only_effect'),(['DisableDepthMask'],'unsupported_special'),(['EnableDestinationAlphaTest'],'unsupported_special'),(['BlendFunction(0, 2, 1, 1, 0)'],'unsupported_blend'),(['UnknownOp()'],'unsupported_special')]
        for commands,route in cases:self.assertEqual(translate_pass(commands)['route'],route)
        self.assertEqual(translate_pass([],shadow=True)['route'],'unsupported_shadow')
        self.assertEqual(translate_pass([],external_texture=True)['route'],'unsupported_environment')
    def test_reader_rejects_truncation_and_unknown_formats(self):
        with self.assertRaises(ValueError):Reader(bytes(4)).get('I',2)
        with self.assertRaises(ValueError):modelset(bytes(128))
        with self.assertRaises(ValueError):vif(struct.pack('<HBB',0,1,0x6f),0,4)
    def test_packet_local_strip_does_not_join_packets(self):
        def command(addr,op,rows,fmt):
            payload=b''.join(struct.pack('<'+fmt*len(row),*row) for row in rows);b=struct.pack('<HBB',addr,len(rows),op)+payload;return b+bytes((-len(b))%4)
        raw=command(0xc000,0x68,[(0,0,0),(1,0,0),(0,1,0)],'f')+command(0xc040,0x64,[(0,0),(1,0),(0,1)],'f')+command(0xc040,0x62,[(0,),(3,)],'B')
        packet={'offset':0,'material':1,'texture':1,'commands':vif(raw,0,len(raw))}
        shape={'header_triangles':2,'packets':[packet,packet]};g=shape_geometry(shape)
        self.assertEqual(g['triangles'],[(0,1,2),(3,4,5)]);self.assertEqual(g['vertices'][3]['position'],(0.,0.,0.))
        shape['header_triangles']=3
        with self.assertRaises(ValueError):shape_geometry(shape)
    def test_branch_and_depth_state_recorded(self):
        r=translate_pass(['DisableAlphaTest','BlendFunction(0, 1, 0, 1, 0)'],tail_branch='off')
        self.assertEqual(r['route'],'source_alpha');self.assertEqual(r['tail_branch'],'off')
    def test_signed_delta_uv_and_split_upload(self):
        commands=[{'address':2,'opcode':5}, {'address':0,'opcode':0x30,'register_words':[4096,2048,0,0]},
                  {'address':0x8040,'opcode':0x66,'format':[2,2],'values':[[0,0],[255,2]]},
                  {'address':0x8042,'opcode':0x65,'format':[1,2],'values':[[-4095,-2050]]}]
        self.assertEqual(unpack_uv(commands,3),[(1.,.5),(4095/4096,2050/4096),(0.,0.)])
        with self.assertRaises(ValueError):unpack_uv([commands[0],*commands[2:]],3)
        # A separate tween UV array at +0x20 must remain a separate attribute.
        commands.append({'address':0xc060,'opcode':0x64,'format':[0,2],'values':[[0,0]]})
        self.assertEqual(len(unpack_uv(commands,3)),3)
        with self.assertRaises(ValueError):unpack_uv([{'opcode':1,'address':0x0201},*commands],3)
        with self.assertRaises(ValueError):vif(struct.pack('<HBB',0x0201,0,1)+struct.pack('<HBB',0xc040,1,0x64)+bytes(8),0,16)
    def test_original_external_texture_operand_is_read_only(self):
        source=bytes([80,2,4,1,0]);graph=command_graph(source,0,len(source));trace=binding_trace(graph)
        self.assertEqual(trace['draws'][0]['texture_table'],{'kind':'external','index':2})
        self.assertEqual(source,bytes([80,2,4,1,0]))
    def test_signed_uv_without_row_arithmetic(self):
        self.assertEqual(unpack_uv([{'opcode':0x66,'address':0x8040,'format':[2,2],'values':[[255,128],[0,127]]}],2),
                         [(-1/4096,-128/4096),(0,127/4096)])
        self.assertEqual(unpack_uv([{'opcode':0x65,'address':0x8040,'format':[1,2],'values':[[-4096,4096]]}],1),[(-1.,1.)])
    def test_packed_normal_direction_and_fail_closed_arithmetic(self):
        n={'opcode':0x6a,'address':0x8080,'format':[2,3],'values':[[0,0,129],[127,0,0]]}
        self.assertEqual(unpack_normals([n],n),[(0.,0.,-1.),(1.,0.,0.)])
        with self.assertRaises(ValueError):unpack_normals([{'opcode':5,'address':2},n],n)
        n={**n,'values':[[0,0,0]]}
        with self.assertRaises(ValueError):unpack_normals([n],n)
    def test_command_targets_and_unknown_callbacks_fail_closed(self):
        # callback 11, one branch; its table entry points at the shape command.
        source=bytes([6,11,0,1,3,0,0,4,2,0])
        g=command_graph(source,0,len(source))
        self.assertEqual(binding_trace(g)['blocked_at']['parameter'],11)
        self.assertEqual(binding_trace(g,callbacks={'11':0})['draws'][0]['shape'],2)
        with self.assertRaises(ValueError):command_graph(bytes([9,255,255]),0,3)
        self.assertTrue(command_graph(bytes([0x7f]),0,1)['unsupported'])

if __name__=='__main__':unittest.main()
