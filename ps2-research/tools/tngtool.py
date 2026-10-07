"""Deterministic, bounded offline Master Rallye PS2 PackFS reader."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

PAK_SHA = 'd98c7cf1049a8a3bc2f90a528a2b6f52cd43c16c2e0564830d5ecb9c592ab28d'
DIRECTORY_SHA = '391929a42dac29eaa6a4306d9e178ad7da925a5426de0befd5550524cc6a56c4'
DATA_SHA = '004ac1676376275bf40c1fd5c1c4a9dcfaae870bf1a7916434eb73b0b1faff86'
MAX_OUTPUT = 64 * 1024 * 1024

class FormatError(ValueError):
    """Corrupt or unsupported input; no recovery or guessing."""

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def lzo1x(data: bytes, expected: int) -> bytes:
    """LZO1X token machine verified against ELF 0x002c0cd0.

    Bounds and consumption checks are deliberately stricter than the game's
    unsafe decoder. Match copies are bytewise to preserve overlap semantics.
    """
    if not 0 <= expected <= MAX_OUTPUT:
        raise FormatError('LZO output size exceeds limit')
    pos, out = 0, bytearray()
    def byte():
        nonlocal pos
        if pos >= len(data): raise FormatError('Truncated LZO token')
        value = data[pos]; pos += 1
        return value
    def literals(n):
        nonlocal pos
        if n > len(data) - pos: raise FormatError('Truncated LZO literals')
        if n > expected - len(out): raise FormatError('LZO output overrun')
        out.extend(data[pos:pos+n]); pos += n
    def match(distance, n):
        if distance <= 0 or distance > len(out): raise FormatError('Invalid LZO back-reference')
        if n > expected - len(out): raise FormatError('LZO output overrun')
        for _ in range(n): out.append(out[-distance])
    def length(n, mask):
        if n: return n
        while True:
            value = byte()
            if value: return n + mask + value
            n += 255
            if n > expected: raise FormatError('Impossible LZO extended length')
    token = byte()
    state = 'outer'
    if token > 17:
        n = token - 17
        literals(n)
        state = 'first' if n >= 4 else 'match'
        token = byte()
    while True:
        if state == 'outer' and token < 16:
            literals(length(token, 15) + 3)
            token = byte()
            state = 'first'
        if state == 'first' and token < 16:
            match(1 + 0x800 + (token >> 2) + byte() * 4, 3)
        elif token >= 64:
            match(1 + ((token >> 2) & 7) + byte() * 8, (token >> 5) + 1)
        elif token >= 32:
            n = length(token & 31, 31) + 2
            low, high = byte(), byte()
            match(1 + ((low | high << 8) >> 2), n)
        elif token >= 16:
            n = length(token & 7, 7) + 2
            low, high = byte(), byte()
            distance = ((token & 8) << 11) + ((low | high << 8) >> 2)
            if distance == 0:
                if n != 3: raise FormatError('Invalid LZO end token')
                if pos != len(data): raise FormatError('Trailing bytes after LZO end')
                if len(out) != expected: raise FormatError('Wrong LZO decompressed size')
                return bytes(out)
            match(distance + 0x4000, n)
        else:
            match(1 + (token >> 2) + byte() * 4, 2)
        tail = data[pos-2] & 3
        if tail:
            literals(tail)
            state = 'match'
        else:
            state = 'outer'
        token = byte()

def decompress(data: bytes, max_output: int = MAX_OUTPUT) -> tuple[bytes, dict]:
    if len(data) < 8: raise FormatError('Truncated PackFS header')
    total, kind, method, block = struct.unpack_from('<IBBH', data)
    if (kind, method) != (1, 1): raise FormatError(f'Unsupported compression header {kind},{method}')
    if not 0 < block <= 65535: raise FormatError('Invalid PackFS block size')
    if total > max_output: raise FormatError('PackFS output size exceeds limit')
    pos, previous, out, rows = 8, 0, bytearray(), []
    while True:
        if len(data) - pos < 8: raise FormatError('Missing/truncated terminal block')
        prev, stored = struct.unpack_from('<II', data, pos)
        header = pos; pos += 8
        if prev != previous: raise FormatError('Invalid previous-block length')
        if not stored:
            if len(out) != total: raise FormatError('Premature terminal block')
            if pos != len(data): raise FormatError('Trailing PackFS bytes')
            return bytes(out), {'total_unpacked_size': total, 'compressor_id': kind, 'unknown_0x05': method,
                                'block_size': block, 'blocks': rows, 'terminal_offset': header}
        if len(out) == total: raise FormatError('Nonzero terminal block')
        if stored > len(data) - pos: raise FormatError('Impossible compressed size/truncated payload')
        expected = min(block, total-len(out))
        decoded = lzo1x(data[pos:pos+stored], expected)
        rows.append({'header_offset': header, 'payload_offset': pos, 'previous_size': prev,
                     'stored_size': stored, 'unpacked_size': len(decoded)})
        out.extend(decoded); pos += stored; previous = stored

def logical_path(value: str) -> str:
    value = value.replace('/', '\\')
    if not value or value.startswith('\\\\') or ':' in value:
        raise FormatError('Invalid logical path')
    if not value.startswith('\\'): value = '\\' + value
    if value == '\\': return value
    parts = value[1:].split('\\')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}
    for part in parts:
        if (not part or part in ('.','..') or part.endswith((' ','.'))
                or any(ord(c) < 32 or c in '<>"|?*' for c in part)
                or part.split('.')[0].rstrip(' .').upper() in reserved):
            raise FormatError('Unsafe logical path component')
    return value

def path_hash(path: str) -> int:
    """ELF 0x002bfd98, including its unusual length-dependent prefix sampling."""
    encoded = path.encode('ascii')
    remaining = value = len(encoded)
    step = (remaining >> 5) | 1
    pos = 0
    while remaining >= step:
        char = encoded[pos]; pos += 1
        if char == 47: char = 92
        value = (value ^ ((value << 5) + (value >> 2) + (char & 0xdf))) & 0xffffffff
        remaining -= step
    return value

def parse_directory(data: bytes) -> dict:
    """Serialized pointer structures, not string carving.

    Fixup owners: 0x002bfe18 / 0x002bfeb0 / 0x002bfef8 / 0x002bff88.
    Header sizes, bucket chains, contiguous node pool, and directory tree are
    checked independently, so a valid string alone cannot create an entry.
    """
    if len(data) < 40: raise FormatError('Truncated directory header')
    magic, size = struct.unpack_from('<II', data)
    if magic != 0x0100face: raise FormatError('Invalid directory magic/root')
    if size != len(data)-8: raise FormatError('Invalid directory body size')
    body = data[8:]
    count, codec_count, codecs_ptr, codecs_size, hash_ptr, hash_size, nodes_ptr, nodes_size, base = struct.unpack_from('<HHIIIIIII', body)
    if not count or not codec_count or not base: raise FormatError('Invalid directory counts/base')
    def u32(p):
        if not 0 <= p <= len(body)-4: raise FormatError('Directory field out of bounds')
        return struct.unpack_from('<I',body,p)[0]
    def pointer(value, width=1):
        pos = value - base
        if value == 0 or not 0 <= pos <= len(body)-width:
            raise FormatError('Bad relocation/string offset')
        return pos
    def string(pos, end):
        stop = body.find(b'\0',pos,end)
        if stop < 0: raise FormatError('Unterminated directory string')
        try: value = body[pos:stop].decode('ascii')
        except UnicodeDecodeError as e: raise FormatError('Non-ASCII directory string') from e
        return value, stop+1
    codecs = pointer(codecs_ptr,codecs_size)
    buckets = pointer(hash_ptr,hash_size)
    node_start = pointer(nodes_ptr,nodes_size)
    node_end = node_start+nodes_size
    if not (codecs == 32 and codecs_size >= codec_count*16 and codecs+codecs_size == buckets
            and buckets+hash_size == node_start and node_end == len(body)):
        raise FormatError('Malformed directory section boundaries')
    codec_rows = []
    for i in range(codec_count):
        values = []
        for field in range(0,16,4):
            ptr = u32(codecs+i*16+field)
            if ptr:
                text_pos=pointer(ptr)
                if not codecs+codec_count*16 <= text_pos < codecs+codecs_size:
                    raise FormatError('Codec string offset outside string region')
                values.append(string(text_pos,codecs+codecs_size)[0])
            else: values.append(None)
        if not values[0]: raise FormatError('Missing codec name')
        codec_rows.append({'index':i,'name':values[0], 'encoder':values[1], 'decoder':values[2], 'unknown_0x0c':values[3]})
    bucket_count, bucket_unknown = struct.unpack_from('<HH',body,buckets)
    if not bucket_count or bucket_count & (bucket_count-1) or hash_size != 4+bucket_count*4:
        raise FormatError('Invalid hash table size')
    parsed = {}
    order = []
    p = node_start
    while p < node_end:
        if node_end-p < 25: raise FormatError('Malformed node')
        offset, stored, declared, sibling, next_hash, codec, unknown = struct.unpack_from('<IIIIIHH',body,p)
        name, end = string(p+24,node_end)
        if logical_path(name) != name: raise FormatError('Noncanonical node path spelling')
        if codec >= codec_count: raise FormatError('Invalid node codec index')
        kind = 'directory' if codec_rows[codec]['name'] == 'dir' else 'file'
        if kind == 'directory' and (stored or declared): raise FormatError('Directory has file sizes')
        row = {'path':name,'entry_index':len(order), 'node_offset':p+8,
               'serialized_address':base+p, 'kind':kind,'data_file':'TNG.000' if kind == 'file' else None,
               'data_file_index':0 if kind == 'file' else None,
               'offset':offset if kind == 'file' else None,
               'stored_size':stored, 'directory_size_0x08':declared,
               'unpacked_size':declared if codec_rows[codec]['name'] == 'raw' else None,
               'codec_index':codec,'storage_codec':codec_rows[codec]['name'],
               'compression':'raw' if codec_rows[codec]['name'] == 'raw' else ('directory' if kind == 'directory' else 'UNKNOWN'),
               'first_child_address':offset if kind == 'directory' else None,
               'next_sibling_address':sibling,'next_hash_address':next_hash,
               'unknown_0x16':unknown,'evidence':'CONFIRMED_BY_BOTH'}
        parsed[base+p] = row; order.append(row)
        p = (end+3)&~3
    if p != node_end or len(order) != count: raise FormatError('Node count/pool size mismatch')
    paths = {row['path'].upper():row for row in order}
    if len(paths) != len(order) or '\\' not in paths or paths['\\']['kind'] != 'directory':
        raise FormatError('Invalid root/duplicate logical path')
    visited = set()
    for i in range(bucket_count):
        ptr = u32(buckets+4+i*4)
        while ptr:
            if ptr not in parsed or ptr in visited: raise FormatError('Invalid/cyclic hash-chain relocation')
            row = parsed[ptr]; visited.add(ptr)
            if path_hash(row['path']) & (bucket_count-1) != i: raise FormatError('Node in wrong hash bucket')
            row['hash_bucket'] = i
            ptr = row['next_hash_address']
    if len(visited) != count: raise FormatError('Unreachable directory nodes')
    tree_seen = set()
    for directory in order:
        if directory['kind'] != 'directory': continue
        ptr = directory['first_child_address']
        while ptr:
            if ptr not in parsed or ptr in tree_seen: raise FormatError('Invalid/cyclic child/sibling relocation')
            child = parsed[ptr]; tree_seen.add(ptr)
            parent = child['path'].rsplit('\\',1)[0] or '\\'
            if parent != directory['path']: raise FormatError('Child path disagrees with directory parent')
            ptr = child['next_sibling_address']
    if len(tree_seen) != count-1 or paths['\\']['serialized_address'] in tree_seen:
        raise FormatError('Invalid root/tree reachability')
    return {'schema_version':1, 'ordering':'serialized node pool offset; entry_index is zero-based offline index',
            'directory_sha256':sha(data),'serialized_base':base,'root':'\\',
            'bucket_count':bucket_count,'unknown_hash_0x02':bucket_unknown,
            'codecs':codec_rows,'directory_count':sum(x['kind']=='directory' for x in order),
            'file_count':sum(x['kind']=='file' for x in order), 'entries':order}

def load_pak(path: Path) -> tuple[dict, dict]:
    data = read_pak_bytes(path)
    if sha(data) != PAK_SHA: raise FormatError('Unsupported TNG.PAK SHA256')
    decoded, framing = decompress(data)
    if len(decoded) != 269668 or sha(decoded) != DIRECTORY_SHA: raise FormatError('Canonical PAK golden mismatch')
    return parse_directory(decoded), framing

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda:file.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def read_pak_bytes(path: Path) -> bytes:
    if path.stat().st_size > MAX_OUTPUT: raise FormatError('PAK input exceeds memory limit')
    return path.read_bytes()

def validate_ranges(manifest: dict, size: int) -> list:
    invalid = []
    for row in manifest['entries']:
        if row['kind'] != 'file': continue
        offset, stored = row['offset'], row['stored_size']
        if not isinstance(offset,int) or not isinstance(stored,int) or offset < 0 or stored < 0 or offset > size or stored > size-offset:
            invalid.append({'path':row['path'],'offset':offset,'stored_size':stored})
    return invalid

def verify_data(manifest: dict, data: Path) -> dict:
    size = data.stat().st_size
    invalid = validate_ranges(manifest,size)
    if invalid: raise FormatError(f'Invalid data ranges: {invalid}')
    header_counts = Counter()
    files = [row for row in manifest['entries'] if row['kind']=='file']
    with data.open('rb') as f:
        for row in files:
            f.seek(row['offset']); head=f.read(min(8,row['stored_size']))
            if row['storage_codec'] == 'gz':
                if len(head) != 8: raise FormatError('Truncated nested header: '+row['path'])
                total, kind, method, block = struct.unpack('<IBBH',head)
                if (kind,method) != (1,1) or block == 0:
                    raise FormatError('Unsupported gz resource header: '+row['path'])
                row['compression']='packfs_lzo'
                row['unpacked_size']=total
                row['unpacked_size_source']='framing header; full payload validation is separate'
                row['block_size']=block
                header_counts[f'{kind},{method},{block}'] += 1
            elif row['storage_codec'] == 'raw':
                row['unpacked_size_source']='directory_size_0x08'
            else:
                raise FormatError('Unsupported data codec: '+row['storage_codec'])
    overlaps = []
    end = 0; previous = None
    for row in sorted(files,key=lambda r:(r['offset'],r['stored_size'],r['path'])):
        if row['stored_size'] and row['offset'] < end:
            overlaps.append({'path':row['path'],'with':previous})
        if row['offset']+row['stored_size'] > end:
            end=row['offset']+row['stored_size']; previous=row['path']
    result = {'data_file':data.name,'size':size,'sha256':file_hash(data),
              'invalid_ranges':invalid,'overlaps':overlaps,
              'file_ranges_checked':len(files),'compressed_headers_checked':sum(header_counts.values()),
              'compressed_header_statistics':dict(sorted(header_counts.items())),
              'full_decompression':'targeted validation only',
              'total_stored_bytes':sum(x['stored_size'] for x in files),
              'total_header_declared_unpacked_bytes':sum(x['unpacked_size'] for x in files)}
    manifest['data_validation']=result
    return result

def read_payload(entry: dict, data: Path, max_output: int=MAX_OUTPUT) -> tuple[bytes, dict]:
    if entry['kind'] != 'file': raise FormatError('Cannot extract a directory')
    if validate_ranges({'entries':[entry]},data.stat().st_size): raise FormatError('Invalid extraction range')
    if entry['stored_size'] > max_output: raise FormatError('Stored extraction exceeds memory limit')
    with data.open('rb') as f:
        f.seek(entry['offset']); stored=f.read(entry['stored_size'])
    if len(stored) != entry['stored_size']: raise FormatError('Truncated extraction read')
    if entry['storage_codec']=='raw':
        payload=stored
        if len(payload) != entry['directory_size_0x08']: raise FormatError('Raw directory size mismatch')
        compression='raw'
    elif entry['storage_codec']=='gz':
        payload,_=decompress(stored,max_output)
        compression='packfs_lzo'
    else: raise FormatError('Unsupported extraction codec')
    report={'path':entry['path'],'offset':entry['offset'],'stored_size':len(stored),
            'directory_size_0x08':entry['directory_size_0x08'], 'unpacked_size':len(payload),
            'compression':compression,'stored_sha256':sha(stored),'payload_sha256':sha(payload),
            'evidence':'CONFIRMED_BY_BOTH'}
    if len(payload)>=8 and struct.unpack_from('<I',payload)[0]==0x13039:
        width,height=struct.unpack_from('<HH',payload,4)
        simple=len(payload)==8+width*height*4
        report['gxi']={'width':width,'height':height,'classification':'SIMPLE_4_BYTES_PER_PIXEL' if simple else 'UNKNOWN/OTHER',
                       'channel_order':'UNKNOWN','size_equation_match':simple}
    else: report['asset_format']='PSB/PSM or UNKNOWN; format reverse deferred'
    return payload,report

def extraction_path(root: Path, path: str) -> Path:
    value=logical_path(path)
    if value=='\\': raise FormatError('Cannot extract root')
    root=root.resolve()
    result=(root/Path(*value[1:].split('\\'))).resolve()
    if not result.is_relative_to(root): raise FormatError('Extraction path escapes output root')
    return result

def write_json(path: Path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')

def protect_inputs(output: Path, inputs: list[Path]):
    if (output.resolve() in {p.resolve() for p in inputs}
            or (output.exists() and any(p.exists() and output.samefile(p) for p in inputs))):
        raise FormatError('Refusing to overwrite an input file')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['info', 'decompress-pak','list','find','verify','extract'])
    ap.add_argument('pak', type=Path)
    ap.add_argument('data', type=Path, nargs='?')
    ap.add_argument('path', nargs='?')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--query',default='')
    ap.add_argument('--manifest',type=Path)
    ap.add_argument('--provenance',type=Path)
    a = ap.parse_args()
    try:
        inputs=[a.pak,*[a.pak.parent/name for name in ('SLES_509.06','SYSTEM.CNF','TNG.PAK','TNG.000')]]
        if a.data: inputs.append(a.data)
        for destination in (a.output,a.manifest,a.provenance):
            if destination: protect_inputs(destination,inputs)
        if a.command in ('info','decompress-pak'):
            data = read_pak_bytes(a.pak)
            decoded, info = decompress(data)
            info.update(input_size=len(data), input_sha256=sha(data), output_sha256=sha(decoded))
            if sha(data) == PAK_SHA and (len(decoded) != 269668 or sha(decoded) != DIRECTORY_SHA):
                raise FormatError('Canonical PAK golden mismatch')
            if a.command == 'decompress-pak':
                if not a.output: ap.error('decompress-pak requires --output')
                a.output.parent.mkdir(parents=True, exist_ok=True)
                a.output.write_bytes(decoded)
            print(json.dumps(info, indent=2))
        else:
            manifest,_ = load_pak(a.pak)
            if a.command=='verify':
                if not a.data: ap.error('verify requires TNG.000')
                report=verify_data(manifest,a.data)
                if report['sha256'] != DATA_SHA: raise FormatError('Unsupported TNG.000 SHA256')
                if a.manifest: write_json(a.manifest,manifest)
                if a.provenance:
                    inputs={}
                    for name in ('SLES_509.06','SYSTEM.CNF','TNG.PAK','TNG.000'):
                        path=a.pak.parent/name
                        inputs[name]={'available':path.is_file()}
                        if path.is_file(): inputs[name].update(size=path.stat().st_size,sha256=file_hash(path))
                    write_json(a.provenance,{'schema_version':1,'inputs':inputs,'source_policy':'immutable external proprietary inputs'})
                print(json.dumps(report,indent=2))
            elif a.command=='extract':
                if not a.data or not a.path or not a.output: ap.error('extract requires TNG.000, logical path and --output directory')
                wanted=logical_path(a.path).upper()
                matches=[r for r in manifest['entries'] if r['path'].upper()==wanted]
                if len(matches)!=1: raise FormatError('Logical resource not found')
                entry=matches[0]
                target=extraction_path(a.output,entry['path'])
                protect_inputs(target,inputs)
                if file_hash(a.data) != DATA_SHA: raise FormatError('Unsupported TNG.000 SHA256')
                payload,report=read_payload(entry,a.data)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(payload)
                write_json(target.with_name(target.name+'.provenance.json'),report)
                print(json.dumps(report,indent=2))
            else:
                rows=[r for r in manifest['entries'] if a.query.upper() in r['path'].upper()]
                print(json.dumps(rows,indent=2))
    except (FormatError, OSError) as e:
        ap.exit(2, f'tngtool: {e}\n')

if __name__ == '__main__': main()
