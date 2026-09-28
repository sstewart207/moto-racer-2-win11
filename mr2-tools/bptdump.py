import re,os
for f in ["CONFIG.BPT","COURSEAI.BPT","CROSSAI.BPT","MOTOKTM.BPT","MOTOSPD.BPT"]:
    p=os.path.join(r"C:\Games\Moto Racer 2\data",f)
    d=open(p,"rb").read()
    strs=re.findall(rb"[\x20-\x7e]{4,}",d)
    print("==== %s (%d bytes) ====" % (f,len(d)))
    print("  first32:",d[:32].hex(" "))
    for s in strs[:40]: print("   ",s.decode("latin1"))
    if not strs: print("    (no ascii strings)")
