from utils import *
#因为市面上没有十九平均律的乐器所以
pa=pad.PyAudio()
st=pa.open(format=pad.paInt32,channels=1,rate=44100,output=1)
def sound(freq):
    X=np.linspace(0,1,44100)
    Y=(2**30)*np.sin(TAU*freq*X)
    Y=Y.astype(np.int32)
    B=bytes(Y.ravel().view('b').data)
    st.write(B)
to=0
add=0.005
def sounds(freqs):
    global to
    X=np.linspace(to,to+add,np.floor(44100*add).astype(np.int32))
    to+=add
    Y=np.zeros_like(X)
    for freq in freqs:
        for k in range(1,65):
            Y+=(2**28)*np.sin(TAU*freq*X*k)*(0 if k%2==0 else
                                           (-1)**((k+1)//2)/(k**2)*8/PI**2)
    Y=Y.astype(np.int32)
    B=bytes(Y.ravel().view('b').data)
    st.write(B)
pyg.init()
wd=90
scr=pyg.display.set_mode((wd*15,700))
pyg.display.set_caption('KeyboardNineteen')
run=1
font=pyg.font.Font(None,50)
font2=pyg.font.Font(None,25)
fc=spfc[19]
dc={(i,0):0 for i in fc.notes}
dc.update({(i,1):0 for i in fc.notes})
dc['C',2]=0
asc={'rtyui1234567890-qwevbnm,opasdfghjklzxc.'[x]:i for x,i in enumerate(dc)}
ras=dict(zip(asc.values(),asc.keys()))
bx,bb={},{}
for i in range(0,wd*15+1,wd):
    pyg.draw.rect(scr,(255,255,255),[i,0,wd,700])
    pyg.draw.rect(scr,(0,0,0),[i,0,wd,700],2)
    bx['CDEFGAB'[i//wd%7],i//wd//7]=[i,0,wd,700]
    scr.blit(font.render('CDEFGAB'[i//wd%7]+'%d'%(i//wd//7),
                         True,(127,217,72)),
             (i+wd//4,550))
    if i//wd%7 in (1,2,4,5,6) and i!=wd*15:
        pyg.draw.rect(scr,(0,0,0),[i-40,0,40,394])
        pyg.draw.rect(scr,(128,128,128),[i,0,40,394])
        scr.blit(font2.render('_CD_FGA'[i//wd%7]+'#%d'%(i//wd//7),
                              True,(127,217,72)),
                 (i-36,370))
        scr.blit(font2.render('_DE_GAB'[i//wd%7]+'b%d'%(i//wd//7),
                              True,(247,193,226)),
                 (i+3,370))
        bb['_CD_FGA'[i//wd%7]+'#',i//wd//7]=[i-40,0,40,394]
        bb['_DE_GAB'[i//wd%7]+'b',i//wd//7]=[i,0,40,394]
    elif i//wd%7 in (0,3) and i!=0:
        pyg.draw.rect(scr,(0,0,0),[i-17,0,35,394])
        scr.blit(font2.render('B__E___'[i//wd%7]+'#%d'%((i//wd-1)//7),
                              True,(127,217,72)),
                 (i-15,370))
        bb['B__E___'[i//wd%7]+'#',(i//wd-1)//7]=[i-17,0,35,394]
    pyg.display.update()
bud=False
while run:
    try:
        ls=[]
        for i in dc:
            if dc[i]:
                ls.append(fc.ansi2freq(*i))
        if len(ls)==0:
            to=0
        sounds(ls)
    finally:
        for ev in pyg.event.get():
            match ev.type:
                case pyg.QUIT:
                    run=0
                case pyg.MOUSEBUTTONDOWN:
                    x,y=ev.pos
                    bud=True
                    for i in bb:
                        nx,ny,w,h=bb[i]
                        mx,my=nx+w,ny+h
                        if nx<x<mx and ny<y<my:
                            dc[i]=1
                            break
                    else:
                        for i in bx:
                            nx,ny,w,h=bx[i]
                            mx,my=nx+w,ny+h
                            if nx<x<mx and ny<y<my:
                                dc[i]=1
                                break
                case pyg.MOUSEMOTION:
                    if not bud:
                        continue
                    for i in dc:
                        dc[i]=0
                    x,y=ev.pos
                    for i in bb:
                        nx,ny,w,h=bb[i]
                        mx,my=nx+w,ny+h
                        if nx<x<mx and ny<y<my:
                            dc[i]=1
                            break
                    else:
                        for i in bx:
                            nx,ny,w,h=bx[i]
                            mx,my=nx+w,ny+h
                            if nx<x<mx and ny<y<my:
                                dc[i]=1
                                break
                case pyg.MOUSEBUTTONUP:
                    for i in dc:
                        dc[i]=0
                    bud=False
                case pyg.KEYDOWN:
                    c=ev.dict['unicode']
                    if c in asc:
                        dc[asc[c]]=1
                case pyg.KEYUP:
                    c=ev.dict['unicode']
                    if c in asc:
                        dc[asc[c]]=0
pyg.quit()
