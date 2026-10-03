"""Read-only PE identity/layout and bounded Ghidra assembly correspondence report.

Raw assembly exports stay ignored. Only fingerprints and comparison summaries
are emitted. This is evidence collection, never a patcher or runtime bypass.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


def pe_metadata(path):
    raw = path.read_bytes()
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    if raw[pe:pe+4] != b'PE\0\0':
        raise ValueError('Not a PE executable')
    count = struct.unpack_from('<H', raw, pe+6)[0]
    optional_size = struct.unpack_from('<H', raw, pe+20)[0]
    base = struct.unpack_from('<I', raw, pe+24+28)[0]
    sections = []
    for i in range(count):
        entry = pe+24+optional_size+i*40
        virtual_size, rva, size, offset = struct.unpack_from('<IIII', raw, entry+8)
        sections.append(dict(name=raw[entry:entry+8].rstrip(b'\0').decode('ascii'),
                             rva=hex(rva), virtual_size=virtual_size, raw_size=size, raw_offset=offset))
    return dict(sha256=hashlib.sha256(raw).hexdigest(), size=len(raw),
                md5=hashlib.md5(raw).hexdigest(), image_base=hex(base), sections=sections,
                freeze_site_file_offset='0x24a1bc', freeze_site_bytes=raw[0x24a1bc:0x24a1be].hex())


def signature(folder, address):
    lines = (folder/(address.lower()+'.asm.txt')).read_text().splitlines()
    instructions = [re.sub(r'0x[0-9a-fA-F]{6,8}', 'ADDR', line.split(' ; ')[0].split(' ',1)[1])
                    for line in lines]
    return dict(instruction_count=len(instructions),
                normalized_sha256=hashlib.sha256('\n'.join(instructions).encode()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pristine',type=Path,required=True)
    parser.add_argument('--patched',type=Path,required=True)
    parser.add_argument('--exports',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = {'pristine':pe_metadata(args.pristine),'patched':pe_metadata(args.patched),
              'ghidra_version':'12.1.4','correspondence':[]}
    if result['pristine']['sha256'] != 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4':
        raise ValueError('Wrong pristine input')
    if result['patched']['sha256'] != 'bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6':
        raise ValueError('Wrong patched input')
    raw = args.patched.read_bytes()
    def offset(va):
        rva = va-int(result['patched']['image_base'],16)
        for section in result['patched']['sections']:
            begin = int(section['rva'],16)
            if begin <= rva < begin+section['raw_size']:
                return section['raw_offset']+rva-begin
        raise ValueError('VA has no file-backed section')
    def word(va):
        return struct.unpack_from('<I',raw,offset(va))[0]
    def call(va):
        position = offset(va)
        if raw[position] != 0xe8:
            raise ValueError('Expected rel32 CALL')
        return va+5+struct.unpack_from('<i',raw,position+1)[0]
    index = raw[offset(0x64b294+0x27)]
    case = word(0x64b1a4+4*index)
    assert case == 0x64b0f7 and call(0x64b10a) == 0x65fb20
    assert word(0x660010+4*2) == 0x65fe51 and call(0x65fe5e) == 0x650020
    assert (word(0x69bf3c),word(0x69bf40)) == (0x652500,0x652530)
    assert raw[0x24a1bc:0x24a1be] == bytes.fromhex('7500')
    result['patched_routes'] = dict(main_dispatcher='0x0064a9f0',
        main_broker_command='0x27', main_translation_index=index,
        main_case=hex(case), main_call='0x0064b10a', broker_opener='0x0065fb20',
        local_dispatcher='0x0065fdd0', local_dump_command=2,
        local_case='0x0065fe51', dump_call='0x0065fe5e', dump_function='0x00650020',
        menu_builder='0x00660040', active_sink_rva='0x2f6b64', vtable_rva='0x29bf3c')
    for name, pristine, patched in [('formatted_logger','004d0620','004d0310'),
            ('debug_clear','0064e640','00652500'),('debug_append','0064e670','00652530'),
            ('broker_open','0065e990','0065fb20'),('broker_local_dispatch','0065ec40','0065fdd0')]:
        first = signature(args.exports/'pristine',pristine)
        second = signature(args.exports/'patched',patched)
        result['correspondence'].append(dict(role=name,pristine=pristine,patched=patched,
            pristine_signature=first,patched_signature=second,
            normalized_equal=first==second))
    first = signature(args.exports/'pristine','005b0990')
    second = signature(args.exports/'patched-routes','0064a9f0')
    result['correspondence'].append(dict(role='main_dispatcher',pristine='005b0990',patched='0064a9f0',
        pristine_signature=first,patched_signature=second,normalized_equal=first==second))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['correspondence'],indent=2))


if __name__ == '__main__':
    main()
