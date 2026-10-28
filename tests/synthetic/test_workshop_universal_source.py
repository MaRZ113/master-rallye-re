"""Provenance guards for Universal Scene authoring, using invented data."""
import json
from pathlib import Path
import tempfile
import unittest

from master_rallye import universal_vehicle_scene as uvs
from master_rallye.workshop.universal_source import verify_source, inspect_source, verify_baseline
from master_rallye.workshop.service import WorkshopProject
from tests.synthetic.test_universal_vehicle_scene import fixture
from tests.synthetic.test_workshop import family


class UniversalSourceWorkshopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);source=self.root/'source';source.mkdir()
        scene,assets=fixture(source);uvs.save_scene(scene,self.root/'neutral',assets)
        report=self.root/'conversion-report.json';report.write_text(json.dumps({'synthetic':True}))
        self.record={'scene_path':str(self.root/'neutral/scene.json'),
                     'scene_sha256':uvs.sha((self.root/'neutral/scene.json').read_bytes()),
                     'manifest_sha256':uvs.sha((self.root/'neutral/manifest.json').read_bytes()),
                     'conversion_report':str(report),'conversion_report_sha256':uvs.sha(report.read_bytes())}

    def test_provenance_reopens_and_exposes_unknowns_without_mutation(self):
        before={p:p.read_bytes()for p in self.root.rglob('*')if p.is_file()}
        value=inspect_source(self.record)
        self.assertEqual(value['unknown_semantics'][0]['status'],'UNSUPPORTED')
        self.assertEqual(verify_source(self.record)['schema'],uvs.SCHEMA)
        self.assertEqual(before,{p:p.read_bytes()for p in before})

    def test_scene_manifest_report_and_sidecar_corruption_are_rejected(self):
        for name in ('neutral/scene.json','neutral/manifest.json','conversion-report.json','neutral/textures/pixel.rgba'):
            with self.subTest(name=name):
                path=self.root/name;before=path.read_bytes();path.write_bytes(before+b' ')
                try:
                    with self.assertRaises(ValueError):verify_source(self.record)
                finally:path.write_bytes(before)

    def test_optional_guard_does_not_change_existing_projects(self):
        family(self.root/'native');project=WorkshopProject.create(self.root/'native',self.root/'workshop')
        project.verify_inputs()
        project.data['universal_source']=self.record;project.save();project.verify_inputs()
        (self.root/'conversion-report.json').write_text('changed')
        with self.assertRaisesRegex(ValueError,'conversion report changed'):
            WorkshopProject(project.root).verify_inputs()

    def test_missing_metadata_and_relative_paths_fail_closed(self):
        for record in (None,{},dict(self.record,scene_path='relative/scene.json'),dict(self.record,manifest_sha256='x')):
            with self.subTest(record=record),self.assertRaises(ValueError):verify_source(record)

    def test_source_derived_mr_baseline_has_exact_file_set_and_hashes(self):
        assets=self.root/'mr-baseline';assets.mkdir();path=assets/'car.dx';path.write_bytes(b'invented immutable model')
        record={'assets':str(assets),'sha256':{'car.dx':uvs.sha(path.read_bytes())}}
        verify_baseline(record)
        extra=assets/'extra.dx';extra.write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'file set'):verify_baseline(record)
        extra.unlink();path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'baseline changed'):verify_baseline(record)
        with self.assertRaises(ValueError):verify_baseline({'assets':str(assets),'sha256':{'../car.dx':'0'*64}})
