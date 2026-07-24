import numpy as np, cv2
from PIL import Image

BASE = 'assets/banner.png'
ANIM = 'assets/banner.webp'
OUT  = '/tmp/banner_final.webp'

base = cv2.imread(BASE)
H,W = base.shape[:2]
sm = cv2.resize(base,(W//4,H//4),interpolation=cv2.INTER_NEAREST)
sh,sw = sm.shape[:2]
b,g,r = [sm[:,:,i].astype(np.int16) for i in range(3)]
lum = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.int16)

# ---------- lanterns ----------
red = (r>g+25)&(r>b+25)&(r>90)
dark = lum<150
lant_defs = [ ((78.5,127.0),(74,83,128,148)), ((87.0,125.0),(84,91,126,141)) ]
plate = sm.copy()
lant_sprites=[]
for pivot,(x0,x1,y0,y1) in lant_defs:
    m = np.zeros(dark.shape,bool)
    m[y0:y1,x0:x1] = dark[y0:y1,x0:x1] | red[y0:y1,x0:x1]
    ys,xs = np.nonzero(m)
    lant_sprites.append((pivot,xs,ys,sm[ys,xs].copy()))
    plate = cv2.inpaint(plate, m.astype(np.uint8)*255, 3, cv2.INPAINT_TELEA)

# ---------- tree ----------
reg = np.zeros(lum.shape,bool); reg[0:90,0:106]=True
pink = (r>b+18)&(r>110)&(r<230)
tree = reg & ((lum<115)|pink); tree[86:90,:]=False
tys,txs = np.nonzero(tree)
tcols = sm[tys,txs].copy()
ax,ay = 22.0,88.0
tdx = txs-ax; tdy = tys-ay
tdist = np.sqrt(tdx**2+tdy**2)
twgt = np.clip(tdist/tdist.max(),0,1)**1.6
torder = np.argsort(tdist)
tphase = txs*0.045 + tys*0.03
tpink = pink[tys,txs]
plate = cv2.inpaint(plate, tree.astype(np.uint8)*255, 3, cv2.INPAINT_TELEA)

# ---------- wisps (all clusters) ----------
cyan = ((g>r+55)&(b>r+40)&(lum>110)).astype(np.uint8)
cyd = cv2.dilate(cyan,np.ones((3,3),np.uint8),1)
ncc,lab = cv2.connectedComponents(cyd,8)
wisps=[]
for i in range(1,ncc):
    m = (lab==i)&(cyan>0)
    if m.sum()<6: continue
    ys,xs = np.nonzero(m)
    pts = np.stack([xs,ys],1).astype(np.float32)
    d = pts-pts.mean(0)
    _,_,vt = np.linalg.svd(d,full_matrices=False)
    sp = d@vt[0]; sp = (sp-sp.min())/(np.ptp(sp)+1e-6)
    phase0 = (i*0.37)%1.0
    wisps.append((xs,ys,sm[ys,xs].astype(np.float32),sp,phase0,m))
wisp_all = np.zeros(lum.shape,bool)
for *_ ,m in wisps: wisp_all |= m
plate = cv2.inpaint(plate, wisp_all.astype(np.uint8)*255, 3, cv2.INPAINT_TELEA)

# ---------- clouds boundary evolution ----------
cool = (b>=r-2)
cloud = np.zeros(lum.shape,np.uint8)
cloud[0:75,:] = ((lum[0:75,:]>150)&(lum[0:75,:]<232)&cool[0:75,:]).astype(np.uint8)
cloud[30:85,172:252] = 0   # floating islands
mist = np.zeros(lum.shape,np.uint8)
mist[130:230,:] = ((lum[130:230,:]>190)&cool[130:230,:]).astype(np.uint8)
mist[130:210,78:150] = 0   # character
cloud = cv2.morphologyEx(cloud, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
mist  = cv2.morphologyEx(mist,  cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
cloud = np.clip(cloud+mist,0,1).astype(np.uint8)
band_out = (cv2.dilate(cloud,np.ones((3,3),np.uint8))>0)&(cloud==0)
band_in  = (cloud>0)&(cv2.erode(cloud,np.ones((3,3),np.uint8))==0)
k = np.ones((9,9),np.float32)/81
smf = sm.astype(np.float32)
cm = cloud.astype(np.float32)
cloudcol = np.dstack([cv2.filter2D(smf[:,:,i]*cm,-1,k)/(cv2.filter2D(cm,-1,k)+1e-4) for i in range(3)])
skm = 1.0-cm
skycol = np.dstack([cv2.filter2D(smf[:,:,i]*skm,-1,k)/(cv2.filter2D(skm,-1,k)+1e-4) for i in range(3)])
rng = np.random.default_rng(11)
noise = cv2.GaussianBlur(rng.random((sh,sw)).astype(np.float32),(0,0),3.5)
noise = (noise-noise.min())/(np.ptp(noise)+1e-6)
yy,xx = np.mgrid[0:sh,0:sw].astype(np.float32)


def render(t, N):
    ph1 = 2*np.pi*t/N
    ph2 = 2*ph1
    fr = plate.copy()

    # clouds: boundary pixels toggle
    nfield = np.sin(ph1 + noise*6.28 + xx*0.05)
    grow = band_out & (nfield>0.60)
    shrink = band_in & (nfield<-0.60)
    fr[grow] = np.clip(0.55*cloudcol[grow]+0.45*fr[grow],0,255).astype(np.uint8)
    fr[shrink] = np.clip(0.55*skycol[shrink]+0.45*fr[shrink],0,255).astype(np.uint8)


    # tree bend redraw
    th = np.radians(2.4)*np.sin(ph2 + tphase)*twgt
    c,s = np.cos(th), np.sin(th)
    nx = np.clip(np.rint(ax + tdx*c - tdy*s + (tpink*0.7)*np.sin(ph2+tphase+1.0)),0,sw-1).astype(int)
    ny = np.clip(np.rint(ay + tdx*s + tdy*c),0,sh-1).astype(int)
    drawn = np.zeros((sh,sw),bool)
    fr[ny[torder],nx[torder]] = tcols[torder]
    drawn[ny,nx]=True
    holes = tree & ~drawn
    fr[holes] = sm[holes]

    # lantern pendulum redraw
    for (pivot,xs,ys,cols),tho in zip(lant_sprites,[9*np.sin(ph2), 9*np.sin(ph2+0.9)]):
        cc,ss = np.cos(np.radians(tho)), np.sin(np.radians(tho))
        px,py = pivot
        nx2 = np.rint(px+(xs-px)*cc-(ys-py)*ss).astype(int)
        ny2 = np.rint(py+(xs-px)*ss+(ys-py)*cc).astype(int)
        fr[ny2,nx2]=cols

    # wisp path flow
    for xs,ys,cols,sp,p0,m in wisps:
        tpos = (sp - ((t/N)+p0)) % 1.0
        vis = tpos<0.60
        xs2,ys2 = xs[vis],ys[vis]
        cc = cols[vis].copy()
        head = tpos[vis]<0.12
        cc[head]=np.clip(cc[head]*1.45,0,255)
        tw = ((tpos[vis]-0.40)/0.20).clip(0,1)
        bgc = fr[ys2,xs2].astype(np.float32)
        fr[ys2,xs2]=np.clip(cc*(1-tw[:,None]*0.8)+bgc*(tw[:,None]*0.8),0,255).astype(np.uint8)
    return fr

if __name__ == '__main__':
    src = Image.open(ANIM)
    N = src.n_frames
    baseup = cv2.resize(sm,(W,H),interpolation=cv2.INTER_NEAREST).astype(np.int16)
    out=[]
    for t in range(N):
        src.seek(t)
        fa = cv2.cvtColor(np.array(src.convert('RGB')), cv2.COLOR_RGB2BGR)
        edited = cv2.resize(render(t,N),(W,H),interpolation=cv2.INTER_NEAREST)
        d = np.abs(fa.astype(np.int16)-baseup).max(axis=2)
        moving = cv2.dilate((d>22).astype(np.uint8),np.ones((3,3),np.uint8))>0
        comp = edited.copy(); comp[moving]=fa[moving]
        out.append(Image.fromarray(cv2.cvtColor(comp,cv2.COLOR_BGR2RGB)))
    out[0].save(OUT,save_all=True,append_images=out[1:],duration=90,loop=0,quality=85,method=4)
    print('saved',OUT)
