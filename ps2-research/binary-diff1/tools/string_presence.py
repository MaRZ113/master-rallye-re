import sys
for path,tag in [(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe","PC"),(r"D:\Game\Master Rallye PS2\SLES_509.06","PS2")]:
    b=open(path,'rb').read().lower()
    print(tag, {n:b.count(n.lower().encode()) for n in sys.argv[1:]})
