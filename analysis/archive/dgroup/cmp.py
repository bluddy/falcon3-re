import glob,os
exe=open('game/FALCONCD.EXE','rb').read()
R69_FILE=0x13AC60; R69_IDA=0x706E0; R69_END=0x85067
def ida2file(ea): return R69_FILE+(ea-R69_IDA)
base_link=0x6A32
for fn in sorted(glob.glob('memdump/*.BIN')):
    m=open(fn,'rb').read()
    lb=0x1F5 if 'MEMDUMP_' not in os.path.basename(fn) else 0x1A2
    res=[]
    for cand_link in [0x6A32,0x6894,0x606E]:
        rt=(cand_link+lb)*16; ida=(cand_link+0x1000)*16
        n=min(0x1000,R69_END-ida)
        f=exe[ida2file(ida):ida2file(ida)+n]; d=m[rt:rt+n]
        same=sum(a==b for a,b in zip(f,d))
        res.append(f'{cand_link:#x}:{same}/{n}')
    # whole R69 compare
    rt=(0x606E+lb)*16; n=R69_END-R69_IDA
    f=exe[R69_FILE:R69_FILE+n]; d=m[rt:rt+n]
    same=sum(a==b for a,b in zip(f,d))
    # also try shifted: is R69 found elsewhere?
    print(os.path.basename(fn),'lb',hex(lb),res,'R69 whole',same,'/',n)
