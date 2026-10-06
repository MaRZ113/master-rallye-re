import copy
import json
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import r_ai1_2_randomizer as r


class ConfigTests(unittest.TestCase):
    def parse(self,text):return r.config(text.encode("ascii") if text is not None else None)
    def test_missing_and_invalid_files(self):
        for data in (None,b"",b"\xff",b"\0",b"x"*4097):
            with self.subTest(data=str(data)[:20]):self.assertEqual(set(r.config(data).values()),{"Stock"})
    def test_case_and_missing_keys(self):
        data=self.parse("[opponentrandomizer]\nConfigVersion=1\nQUICKRACE=mIxEd\nChallenge=bad\nInvitation=Diverse")
        self.assertEqual(data,dict(zip(r.MODES,("Mixed","Stock","Stock","Diverse","Stock"))))
    def test_version_fail_closed(self):
        for version in ("","0","2","1.0"):
            with self.subTest(version=version):
                self.assertEqual(set(self.parse(f"[OpponentRandomizer]\nConfigVersion={version}\nQuickRace=Mixed").values()),{"Stock"})
    def test_malformed_fail_closed(self):
        for text in ("[Other]\nConfigVersion=1\nQuickRace=Mixed",
                     "[OpponentRandomizer]\nConfigVersion=1\nQuickRace=Mixed\nBrokenLine",
                     "[OpponentRandomizer]\nConfigVersion=1\nUnknown=Mixed",
                     "[OpponentRandomizer]\nConfigVersion=1\nQuickRace=Mixed\nQuickRace=Diverse",
                     "[OpponentRandomizer]\nConfigVersion:1\nQuickRace=Mixed",
                     "[OpponentRandomizer]\nConfigVersion=1\nQuickRace=Mixed\n  continued",
                     "[OpponentRandomizer]\nConfigVersion=1\v\nQuickRace=Mixed"):
            with self.subTest(text=text):self.assertEqual(set(self.parse(text).values()),{"Stock"})
    def test_samples(self):
        root=Path(__file__).resolve().parents[2]/"research/r-ai1-2"
        self.assertEqual(set(r.config((root/"MRallyeRandomizer.stock.ini").read_bytes()).values()),{"Stock"})
        example=r.config((root/"MRallyeRandomizer.example.ini").read_bytes())
        self.assertEqual(example["Challenge"],"Stock")
        self.assertEqual([example[m] for m in r.MODES if m!="Challenge"],["Mixed"]*4)


class BridgeTests(unittest.TestCase):
    def test_layout_nonoverlap_and_max_size(self):
        for five in (False,True):
            rows=sorted(r.ranges(five),key=lambda p:p["offset"]);end=0
            for row in rows:
                self.assertGreaterEqual(row["offset"],end)
                self.assertEqual(len(row["original"]),len(row["replacement"]))
                end=row["offset"]+len(row["original"])
            for row in r.bridge_ranges():
                if row["va"] is not None and row["va"]>=0x68E000:
                    self.assertGreaterEqual(row["va"],0x68E400)
                    self.assertLessEqual(row["va"]+len(row["replacement"]),0x68F000)
    def test_unchanged_capacity_composition(self):
        normal={p["offset"]:p for p in r.ranges(False)}
        composed={p["offset"]:p for p in r.ranges(True)}
        extra={p["offset"] for p in r.capacity_ranges() if p["va"] is not None}
        self.assertEqual(set(composed)-set(normal),extra)
        for offset in set(normal)&set(composed):
            self.assertEqual(normal[offset],composed[offset])
    def test_synthetic_byte_verification_determinism_and_inverse(self):
        rows=r.ranges(True)
        source=bytearray(r.RETAIL_SIZE)
        for row in rows:source[row["offset"]:row["offset"]+len(row["original"])]=row["original"]
        source=bytes(source);digest=r.sha256(source)
        output=r.apply_ranges(source,rows,digest)
        self.assertEqual(output,r.apply_ranges(source,rows,digest))
        restored=bytearray(output)
        for row in rows:restored[row["offset"]:row["offset"]+len(row["original"])]=row["original"]
        self.assertEqual(bytes(restored),source)
        wrong=bytearray(source);wrong[rows[-1]["offset"]]^=1
        with self.assertRaises(ValueError):r.apply_ranges(bytes(wrong),rows,r.sha256(bytes(wrong)))
        with self.assertRaises(ValueError):r.apply_ranges(source,rows,"0"*64)
    def test_unknown_build_rejected(self):
        with self.assertRaises(ValueError):r.build(bytes(r.RETAIL_SIZE))
        with self.assertRaises(ValueError):r.verify(bytes(r.RETAIL_SIZE))
    def test_displaced_calls_are_relocated(self):
        for spec in r.SPECS:
            first=r.selection_code(spec)[0]
            if spec["hint"]==2:
                target=spec["base"]+8+5+struct.unpack_from("<i",first,9)[0]
                self.assertEqual(target,0x4AE700)


class OracleTests(unittest.TestCase):
    def sample(self,ids=(0,14,7,1,8),mode="QuickRace"):
        types={"QuickRace":2,"Challenge":7,"RallyeCup":6,"Invitation":8,"MasterRallye":5}
        values={"Race/NumCars":len(ids),"Race/NumPlayers":1,"Race/NumNetworkPlayers":0,"Race/Type":types[mode],
                "Race/AttractMode":False,"Race/PlaybackReplay":False}
        for n,id in enumerate(ids):
            for key,value in {"CarID":id,"CarClass":r.stock_class_local(id)[0],
                "DriverID":30 if n==0 else n,"PlayerType":1 if n==0 else 2}.items():
                values[f"Race/Car{n}/{key}"]=value
        return {"entries":[{"path":p,"value":v} for p,v in values.items()]}
    def test_all_modes_and_counts(self):
        for mode in r.MODES:
            for count in range(1,6):
                with self.subTest(mode=mode,count=count):
                    result=r.roster(self.sample((0,14,7,1,8)[:count],mode),mode,"Mixed",count,0)
                    self.assertEqual(result["status"],"BROKER_STATE_MATCH_ONLY")
                    self.assertFalse(result["runtime_full_pass"])
    def test_diverse_cycles(self):
        result=r.roster(self.sample(),"QuickRace","Diverse",5,0)
        self.assertEqual(len(result["participants"]),5)
        with self.assertRaises(ValueError):r.roster(self.sample((0,14,15)),"QuickRace","Diverse",3,0)
    def test_duplicates_player_and_class(self):
        for ids,player in (((0,0),0),((0,14),7)):
            with self.assertRaises(ValueError):r.roster(self.sample(ids),"QuickRace","Mixed",2,player)
        snap=self.sample((0,14))
        next(e for e in snap["entries"] if e["path"]=="Race/Car1/CarClass")["value"]=0
        with self.assertRaises(ValueError):r.roster(snap,"QuickRace","Mixed",2,0)
        fixed=r.roster(self.sample((0,0),"Challenge"),"Challenge","Stock",2,0)
        self.assertEqual(fixed["duplicate_policy"],"native_fixed_pair")
        with self.assertRaises(ValueError):r.roster(self.sample((0,0),"Challenge"),"Challenge","Mixed",2,0)
    def test_unknown_mode_replay_attract_and_count(self):
        for path in ("Race/AttractMode","Race/PlaybackReplay"):
            snap=self.sample((0,14));next(e for e in snap["entries"] if e["path"]==path)["value"]=True
            with self.assertRaises(ValueError):r.roster(snap,"QuickRace","Mixed",2,0)
        for mode,count in (("Unknown",2),("QuickRace",6)):
            with self.assertRaises(ValueError):r.roster(self.sample((0,14)),mode,"Mixed",count,0)
    def test_generation_log_requires_complete_matching_context(self):
        digest="a"*64
        data=(f"QuickRace Diverse 3 1 2 {digest}\nQuickRace Diverse 3 2 0 {digest}\n"
              f"QuickRace Diverse 3 3 1 {digest}\n").encode()
        report=r.log_generation(data,"QuickRace","Diverse",digest,[2,0,1])
        self.assertEqual(report["matching_generations"],1)
        self.assertFalse(report["native_dump"])
        for mode,policy,config,classes in (("RallyeCup","Diverse",digest,[2,0,1]),
                ("QuickRace","Mixed",digest,[2,0,1]),("QuickRace","Diverse","b"*64,[2,0,1]),
                ("QuickRace","Diverse",digest,[2,1,0])):
            with self.assertRaises(ValueError):r.log_generation(data,mode,policy,config,classes)
        with self.assertRaises(ValueError):r.log_generation(data.splitlines()[0],"QuickRace","Diverse",digest,[2,0,1])
    def test_available_identity_evidence(self):
        snap=self.sample((0,14))
        snap["entries"].append({"path":"Race/Car1/CarType","value":"Wildcat"})
        result=r.roster(snap,"QuickRace","Mixed",2,0)
        self.assertEqual(result["available_identity_checks"][1]["Race/Car1/CarType"],"Wildcat")
        snap["entries"][-1]["value"]="Landcruiser"
        with self.assertRaises(ValueError):r.roster(snap,"QuickRace","Mixed",2,0)
    def test_stock_log_and_bad_log(self):
        digest="f"*64
        report=r.log_generation(f"Challenge Stock 1 1 - {digest}\n".encode(),"Challenge","Stock",digest,[1])
        self.assertEqual(report["complete_generations"],1)
        for data in (b"broken",b"x"*131073,b"QuickRace Mixed 9 1 2 abc"):
            with self.assertRaises(ValueError):r.log_generation(data,"QuickRace","Mixed",digest,[2])
    def test_variation_summary_keeps_lifecycle_and_rng_limits(self):
        a=r.roster(self.sample((0,14,7)),"QuickRace","Mixed",3,0)
        b=r.roster(self.sample((0,7,1)),"QuickRace","Mixed",3,0)
        result=r.summarize([a,b])
        self.assertTrue(result["ai_ids_vary"])
        self.assertTrue(result["ai_classes_vary"])
        self.assertFalse(result["rng_uniformity_proven"])
        self.assertTrue(result["fresh_generation_requires_lifecycle_evidence"])
        with self.assertRaises(ValueError):r.summarize([a,{**b,"policy":"Stock"}])


if __name__=="__main__":unittest.main()
