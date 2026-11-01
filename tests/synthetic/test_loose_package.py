import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from master_rallye.workshop.loose_package import prepare, safe_path


class LoosePackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bundle = self.root / 'bundle'
        self.assets = self.bundle / 'resource-root'
        self.assets.mkdir(parents=True)
        self.retail = self.root / 'retail'
        self.retail.mkdir()
        self.original = self.retail / 'Data.sma'
        self.write_zip(self.original, {'DataGx/Vehicles/A/car.dx': b'old', 'DataGame/dev.xml': b'base'})
        self.write_zip(self.assets / 'Data.sma', {'DataGx/Vehicles/A/car.dx': b'archive change',
                                                   'DataGx/Vehicles/A/wheel.dx': b'new', 'DataGame/dev.xml': b'base'})
        self.asset('DataGx/Vehicles/A/car.dx', b'loose change')
        self.asset('DataGame/options.xml', b'user settings')
        self.index()

    def tearDown(self): self.tmp.cleanup()

    def write_zip(self, path, values):
        with zipfile.ZipFile(path, 'w') as z:
            for name, data in values.items(): z.writestr(name, data)

    def asset(self, name, data):
        path = self.assets / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def index(self):
        rows = []
        for path in sorted(self.assets.rglob('*')):
            if path.is_file():
                data = path.read_bytes()
                rows.append(f'{hashlib.sha256(data).hexdigest()}\t{len(data)}\t{path.relative_to(self.assets).as_posix()}\n')
        index = ''.join(rows).encode()
        (self.bundle / 'resource-index.tsv').write_bytes(index)
        (self.bundle / 'runtime-profile.json').write_text(json.dumps({'resource_index_sha256': hashlib.sha256(index).hexdigest()}))

    def run_prepare(self, output='draft'):
        root = self.root / 'private'
        return prepare(self.bundle, self.original, self.retail, root / output, allowed_output_root=root)

    def test_deterministic_loose_overrides_skip_mutable_and_leave_input(self):
        before = self.original.read_bytes()
        a = self.run_prepare('a')
        b = self.run_prepare('b')
        self.assertEqual(a, b)
        self.assertFalse(a['installable'])
        files = {r['path']: r for r in a['resources']}
        self.assertEqual(set(files), {'DataGx/Vehicles/A/car.dx', 'DataGx/Vehicles/A/wheel.dx'})
        self.assertEqual((self.root / 'private/a/resources/DataGx/Vehicles/A/car.dx').read_bytes(), b'loose change')
        for name in files:
            self.assertEqual((self.root / 'private/a/resources' / name).read_bytes(),
                             (self.root / 'private/b/resources' / name).read_bytes())
        self.assertEqual(self.original.read_bytes(), before)

    def test_changed_indexed_resource_rejected(self):
        self.asset('DataGx/Vehicles/A/car.dx', b'tamper')
        with self.assertRaisesRegex(ValueError, 'changed|mismatch'): self.run_prepare()
        self.assertFalse((self.root / 'private/draft').exists())

    def test_removed_archive_member_rejected(self):
        self.write_zip(self.assets / 'Data.sma', {'DataGame/dev.xml': b'base'})
        self.index()
        with self.assertRaisesRegex(ValueError, 'deletion'): self.run_prepare()

    def test_existing_loose_file_wins_over_archive_and_is_reported(self):
        self.asset('DataGx/Vehicles/A/car.dx', b'old')
        existing = self.retail / 'DataGx/Vehicles/A/car.dx'
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b'other mod')
        self.index()
        result = self.run_prepare()
        car = next(row for row in result['resources'] if row['path'].endswith('/car.dx'))
        self.assertEqual(car['review'], 'existing loose file conflict')
        self.assertEqual(car['existing_loose_sha256'], hashlib.sha256(b'other mod').hexdigest())
        self.assertEqual(existing.read_bytes(), b'other mod')

    def test_reject_paths_and_foreign_output(self):
        for name in ('../DataGx/car.dx', 'DataGx/../car.dx', 'DataGx/A/a.dll', 'DataGx/A/C:/evil', 'DataGx/A/con.txt'):
            with self.assertRaises(ValueError): safe_path(name)
        with self.assertRaisesRegex(ValueError, 'fresh output'):
            prepare(self.bundle, self.original, self.retail, self.retail / 'output', allowed_output_root=self.root / 'private')


if __name__ == '__main__': unittest.main()
