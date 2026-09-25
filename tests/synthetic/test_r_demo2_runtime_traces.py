from __future__ import annotations

import csv
import io
import unittest

from tools.runtime.demo_debug_classify import parse_debug_lines
from tools.runtime.demo_procmon_extract import extract_events, parse_detail, parse_procmon_number
from tools.runtime.demo_cache_trace import analyze_events, compare_traversals


def procmon_csv(rows):
    stream = io.StringIO()
    fields = ['Time of Day', 'Process Name', 'PID', 'Operation', 'Path', 'Result', 'Detail', 'Event Class', 'Sequence']
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({'Time of Day': '12:00:00,0000000', 'Process Name': 'MRallye.exe', 'PID': '77',
                         'Operation': 'ReadFile', 'Path': r'C:\Scratch\Trooper\complete.gxm',
                         'Result': 'SUCCESS', 'Detail': '', 'Event Class': 'File System', 'Sequence': 'n/a', **row})
    return stream.getvalue()


class DebugViewRealFormatTests(unittest.TestCase):
    def test_parses_pid_model_and_completed_stages(self):
        text = ('00000010\t1.25\t77\tReading GXM: [D:\\demo\\car.gxm]\n'
                '00000012\t1.30\t77\tMaking dx model for moModel named : [vehicles\\car]\n'
                '00000013\t1.31\t77\tInserting moSortPlane nodes -\n'
                '00000014\t1.32\t77\tdone\n'
                '00000015\t1.33\t77\tVertex welder -\n'
                '00000016\t1.34\t77\tdone\n')
        proc = parse_debug_lines(text)['processes']['77']
        self.assertEqual(proc['models'][0], r'D:\demo\car.gxm')
        self.assertEqual([s['status'] for s in proc['stages']], ['done', 'done'])
        self.assertEqual(proc['stages'][0]['compiled_model'], r'vehicles\car')
        self.assertEqual(proc['messages'][-1]['sequence'], 16)
        self.assertIsNone(proc['last_started_stage'])

    def test_marks_unclosed_chull_stage_as_runtime_crash_candidate(self):
        proc = parse_debug_lines('00000001\t0.1\t9001\tVertex welder -\n00000002\t0.2\t9001\tdone\n00000003\t0.3\t9001\tBuilding convex hull -\n')['processes']['9001']
        self.assertEqual(proc['last_completed_stage'], 'Vertex welder')
        self.assertEqual(proc['last_started_stage'], 'Building convex hull')
        self.assertEqual(proc['stages'][-1]['status'], 'incomplete')
        self.assertEqual(proc['classification'], 'CRASH_DURING_CONVEX_HULL_BUILD')
        self.assertEqual(proc['final_message'], 'Building convex hull -')


class ProcMonRealFormatTests(unittest.TestCase):
    def test_detail_numbers_with_grouping_spaces(self):
        parsed = parse_detail('Offset: 134 345, Length: 1 040')
        self.assertEqual((parsed['offset'], parsed['length']), (134345, 1040))
        self.assertEqual(parse_procmon_number('262\u00a0144'), 262144)

    def test_real_columns_and_open_metadata(self):
        events = extract_events(procmon_csv([{'Operation': 'CreateFile', 'Result': 'SUCCESS', 'Detail': 'Desired Access: Generic Read/Write, Disposition: OverwriteIf, OpenResult: Overwritten'},
                                             {'Operation': 'QueryAllInformationFile', 'Result': 'BUFFER OVERFLOW', 'Detail': 'LastWriteTime: 08.10.2001 14:43:00, EndOfFile: 134 349'},
                                             {'Operation': 'ReadFile', 'Result': 'END OF FILE', 'Detail': 'Offset: 134 349, Length: 4'}]), 'complete.', 77)
        self.assertEqual(events[0]['open_result'], 'Overwritten')
        self.assertEqual(events[1]['last_write_time'], '08.10.2001 14:43:00')
        self.assertEqual(events[1]['end_of_file'], 134349)
        self.assertEqual((events[2]['offset'], events[2]['length'], events[2]['result']), (134349, 4, 'END OF FILE'))

    def test_name_not_found_and_created_are_distinct(self):
        events = extract_events(procmon_csv([{'Operation': 'CreateFile', 'Result': 'NAME NOT FOUND'},
                                             {'Operation': 'CreateFile', 'Result': 'SUCCESS', 'Detail': 'Disposition: OverwriteIf, OpenResult: Created'}]), 'complete.', 77)
        self.assertEqual([e['result'] for e in events], ['NAME NOT FOUND', 'SUCCESS'])
        self.assertEqual(events[1]['open_result'], 'Created')

    def test_miss_and_cache_states_are_event_classified(self):
        def event(op, path, result='SUCCESS', detail='', row=0):
            from tools.runtime.demo_procmon_extract import parse_detail
            item = {'operation': op, 'path': path, 'result': result, 'detail': detail, 'row': row}
            item.update(parse_detail(detail))
            return item
        src, dx = r'C:\Demo\complete.gxm', r'C:\Demo\complete.dx'
        miss = [event('CreateFile', src, row=0), event('QueryAllInformationFile', src, detail='LastWriteTime: 08.10.2001 14:43:00, EndOfFile: 8', row=1),
                event('CreateFile', dx, 'NAME NOT FOUND', row=2), event('ReadFile', src, detail='Offset: 0, Length: 8', row=3),
                event('CreateFile', dx, detail='Disposition: OverwriteIf, OpenResult: Created', row=4),
                event('WriteFile', dx, detail='Offset: 0, Length: 8', row=5), event('ReadFile', dx, detail='Offset: 0, Length: 8', row=7)]
        self.assertEqual(analyze_events(miss)['classification'], 'CACHE_MISS_BUILD')
        self.assertEqual(analyze_events(miss)['cache_probe_result'], 'NAME NOT FOUND')
        fallback = [event('CreateFile', src, 'NAME NOT FOUND', row=0), event('CreateFile', dx, row=1),
                    event('QueryAllInformationFile', dx, detail='LastWriteTime: 09.10.2001 14:43:00, EndOfFile: 8', row=2),
                    event('ReadFile', dx, detail='Offset: 0, Length: 8', row=3)]
        self.assertEqual(analyze_events(fallback)['classification'], 'SOURCE_MISSING_COMPILED_FALLBACK')
        stale = [event('CreateFile', src, row=0), event('CreateFile', dx, row=1),
                 event('QueryAllInformationFile', src, detail='LastWriteTime: 08.10.2001 14:43:00, EndOfFile: 8', row=2),
                 event('QueryAllInformationFile', dx, detail='LastWriteTime: 03.10.2001 10:06:44, EndOfFile: 8', row=3),
                 event('CreateFile', dx, detail='Disposition: OverwriteIf, OpenResult: Overwritten', row=4),
                 event('WriteFile', dx, detail='Offset: 0, Length: 8', row=5)]
        self.assertEqual(analyze_events(stale)['classification'], 'STALE_CACHE_REBUILD')
        fresh = [event('CreateFile', src, row=0), event('CreateFile', dx, row=1),
                 event('QueryAllInformationFile', src, detail='LastWriteTime: 08.10.2001 14:43:00, EndOfFile: 8', row=2),
                 event('QueryAllInformationFile', dx, detail='LastWriteTime: 09.10.2001 10:06:44, EndOfFile: 8', row=3),
                 event('ReadFile', dx, detail='Offset: 0, Length: 8', row=4)]
        self.assertEqual(analyze_events(fresh)['classification'], 'FRESH_CACHE_HIT')

    def test_writer_reader_traversal_and_gap_report(self):
        writes = [{'offset': 0, 'length': 4, 'result': 'SUCCESS'}, {'offset': 4, 'length': 4, 'result': 'SUCCESS'}]
        reads = [dict(event) for event in writes]
        report = compare_traversals(writes, reads)
        self.assertTrue(report['exact_match'])
        self.assertEqual(report['final_serialized_size'], 8)
        gap = compare_traversals([writes[0], {'offset': 8, 'length': 4, 'result': 'SUCCESS'}], reads)
        self.assertEqual(gap['gaps'], [[4, 8]])
        self.assertIsNotNone(gap['first_divergence'])

    def test_texture_cache_miss_classification(self):
        from tools.runtime.demo_procmon_extract import parse_detail
        def ev(op, path, result='SUCCESS', detail='', row=0):
            item={'operation':op,'path':path,'result':result,'detail':detail,'row':row}; item.update(parse_detail(detail)); return item
        gxi=r'C:\Demo\black-tga.gxi'; dxt=r'C:\Demo\black-tga.dxt'
        events=[ev('CreateFile',gxi,row=0),ev('QueryAllInformationFile',gxi,detail='EndOfFile: 1 032',row=1),
                ev('CreateFile',dxt,'NAME NOT FOUND',row=2),ev('ReadFile',gxi,detail='Offset: 0, Length: 8',row=3),
                ev('CreateFile',dxt,detail='Disposition: OverwriteIf, OpenResult: Created',row=4),
                ev('WriteFile',dxt,detail='Offset: 0, Length: 4',row=5),ev('ReadFile',dxt,detail='Offset: 0, Length: 4',row=6)]
        self.assertEqual(analyze_events(events)['classification'], 'GXI_DXT_CACHE_MISS')


if __name__ == '__main__':
    unittest.main()
