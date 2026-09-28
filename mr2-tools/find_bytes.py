import os,sys
needle = bytes.fromhex("48 5C C7 91 22 AC 46 5F")
roots = [r"C:\Games\mr2-state-backup", r"C:\Games\Moto Racer 2", r"D:\DATA"]
hits=[]
for root in roots:
    for dp,dn,fn in os.walk(root):
        for f in fn:
            p=os.path.join(dp,f)
            try:
                if os.path.getsize(p) > 200*1024*1024: continue
                d=open(p,'rb').read()
            except Exception: continue
            if needle in d: hits.append(p)
print("BYTE-SEQUENCE HITS:")
for h in hits: print("  ",h)
if not hits: print("   (none)")
