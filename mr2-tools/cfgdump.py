import re
d=open(r"C:\Games\mr2-state-backup\config.bin.bak","rb").read()
print("len",len(d))
print("head64:",d[:64].hex(" "))
strs=re.findall(rb"[\x20-\x7e]{5,}",d)
print("ascii strings found:",len(strs))
for s in strs[:60]: print("   ",s.decode("latin1"))
