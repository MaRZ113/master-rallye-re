import hashlib,tempfile,unittest
from pathlib import Path
from master_rallye.addon_sdk.player_state import seed_player_state,MAX_BYTES


class PlayerStateTests(unittest.TestCase):
    def test_exact_private_seed_and_no_overwrite(self):
        with tempfile.TemporaryDirectory()as tmp:
            r=Path(tmp);source=r/'game/DataGame/PlayerState.xml';source.parent.mkdir(parents=True)
            raw=b'<?xml version="1.0"?><Game><Broker><Value Name="fixture"/></Broker></Game>';source.write_bytes(raw)
            result=seed_player_state(r/'game',r/'runtime');self.assertEqual(result['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual((r/'runtime/DataGame/PlayerState.xml').read_bytes(),raw);self.assertEqual(source.read_bytes(),raw)
            with self.assertRaises(FileExistsError):seed_player_state(r/'game',r/'runtime')

    def test_missing_and_invalid_sources(self):
        with tempfile.TemporaryDirectory()as tmp:
            r=Path(tmp);self.assertFalse(seed_player_state(r/'game',r/'runtime')['copied'])
            p=r/'game/DataGame/PlayerState.xml';p.parent.mkdir(parents=True)
            for raw in (b'<Other/>',b'<Game>',b'<!DOCTYPE Game><Game><Broker/></Game>','<Game><Broker/></Game>'.encode('utf-16'),b'x'*(MAX_BYTES+1),b''):
                p.write_bytes(raw)
                with self.assertRaises(ValueError):seed_player_state(r/'game',r/'runtime')
            self.assertFalse((r/'runtime/DataGame/PlayerState.xml').exists())


if __name__=='__main__':unittest.main()
