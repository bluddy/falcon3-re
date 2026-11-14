import struct,glob,os
def walk(m):
    # find a chain start: scan low paras for 'M' MCB that chains to Z
    for start in range(0x40,0x400):
        p=start; chain=[]
        ok=True
        while True:
            o=p*16
            if o+16>len(m): ok=False;break
            t=m[o]; 
            if t not in (0x4D,0x5A): ok=False;break
            own,sz=struct.unpack_from('<HH',m,o+1)
            chain.append((p,chr(t),own,sz,m[o+8:o+16].split(b'\0')[0]))
            if t==0x5A: break
            p=p+1+sz
            if len(chain)>200: ok=False;break
        if ok and len(chain)>=4 and chain[-1][1]=='Z': return chain
def info(fn):
    m=open(fn,'rb').read()
    ch=walk(m)
    psp=None
    for p,t,own,sz,nm in ch:
        if own==p+1 and m[(p+1)*16:(p+1)*16+2]==b'\xcd\x20' and b'FALCON' in nm.upper(): psp=p+1
    return m,ch,psp
if __name__=='__main__':
    for fn in sorted(glob.glob('memdump/*.BIN')):
        m,ch,psp=info(fn)
        print(os.path.basename(fn),'PSP',hex(psp) if psp else None,'load',hex(psp+0x10) if psp else None)
        for c in ch:
            if c[2]==psp: print('   blk',hex(c[0]),c[1],'own',hex(c[2]),'sz',hex(c[3]),c[4])
