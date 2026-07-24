"""仙气/雾气流动效果：右侧远山雾带流动 + 人物附近灵气缕。
直接在动画每一帧上应用小格(4x)像素级增删，叠加在现有动效之上。"""
import numpy as np, cv2
from PIL import Image

ANIM = 'assets/banner.webp'
BASE = 'assets/banner.png'
OUT  = '/tmp/banner_mist.webp'

base = cv2.imread(BASE)
H,W = base.shape[:2]
S = 4
sm = cv2.resize(base,(W//S,H//S),interpolation=cv2.INTER_NEAREST)
sh,sw = sm.shape[:2]
b,g,r = [sm[:,:,i].astype(np.int16) for i in range(3)]
lum = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.int16)
gy,gx = np.mgrid[0:sh,0:sw]

# ---------- 远山雾带（右侧，由近及远分层） ----------
cool = (b>=r-2)
mist = ((lum>188)&cool).astype(np.uint8)
# 三层纵深：近(黄) / 远(红) / 更远(绿)，速度与强度递减
zone = np.zeros((sh,sw),np.float32)      # 值 = 流速权重
zone[163:245,6:266]   = 1.0              # 近景：左下含人物悬崖
zone[82:243,226:381]  = 0.5              # 远景：右侧群山
zone[31:88,217:358]   = 0.22             # 更远：浮岛天空
mist &= (zone>0).astype(np.uint8)
mist[130:215,78:152] = 0           # 人物本体不动
mist = cv2.morphologyEx(mist, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
band_out = (cv2.dilate(mist,np.ones((3,3),np.uint8))>0)&(mist==0)&(zone>0)
band_in  = (mist>0)&(cv2.erode(mist,np.ones((3,3),np.uint8))==0)

k = np.ones((9,9),np.float32)/81
smf = sm.astype(np.float32)
mm = mist.astype(np.float32)
mistcol = np.dstack([cv2.filter2D(smf[:,:,i]*mm,-1,k)/(cv2.filter2D(mm,-1,k)+1e-4) for i in range(3)])
nm = 1.0-mm
deepcol = np.dstack([cv2.filter2D(smf[:,:,i]*nm,-1,k)/(cv2.filter2D(nm,-1,k)+1e-4) for i in range(3)])

rng = np.random.default_rng(7)
noise = cv2.GaussianBlur(rng.random((sh,sw)).astype(np.float32),(0,0),3.0)
noise = (noise-noise.min())/(np.ptp(noise)+1e-6)
speed = zone.copy()   # 各层流速权重
alpha_map = np.clip(zone*0.5+0.18, 0.2, 0.55).astype(np.float32)   # 各层强度

# ---------- 建筑物边缘雾晕 ----------
bzone = np.zeros((sh,sw),np.float32)
bzone[30:95,300:384]  = 0.5    # 右上楼阁
bzone[90:215,270:384] = 0.5    # 右侧崖上建筑群
bzone[55:135,225:300] = 0.4    # 中部峰顶亭台
bzone[195:245,275:340]= 0.7    # 右下小阁
bzone[0:113,0:131] = 0         # 左上区域不加雾晕
bdark = ((lum<120)&(bzone>0)).astype(np.uint8)
bdark = cv2.morphologyEx(bdark, cv2.MORPH_OPEN, np.ones((2,2),np.uint8))
halo = (cv2.dilate(bdark,np.ones((9,9),np.uint8))>0)&(bdark==0)&(lum>125)&(bzone>0)
halo &= ~(mist>0)   # 不与雾带重复处理
halo_alpha = (bzone*0.8).astype(np.float32)
hm = halo.astype(np.float32)
halocol = np.dstack([cv2.filter2D(smf[:,:,i]*hm,-1,k)/(cv2.filter2D(hm,-1,k)+1e-4) for i in range(3)])
halocol = np.clip(halocol*1.10+30,0,255)   # 提亮成雾色
noise2 = cv2.GaussianBlur(rng.random((sh,sw)).astype(np.float32),(0,0),2.5)
noise2 = (noise2-noise2.min())/(np.ptp(noise2)+1e-6)

# ---------- 人物附近灵气缕 ----------
CYAN = np.array([190, 235, 170], np.float32)   # BGR 淡青
def interp(pts, dens=3):
    pts = np.array(pts,np.float32); allp=[]
    for i in range(len(pts)-1):
        n = int(np.hypot(*(pts[i+1]-pts[i]))*dens)+1
        for t in np.linspace(0,1,n):
            allp.append(pts[i]*(1-t)+pts[i+1]*t)
    return np.array(allp)

wisp_paths = [
    # 近景（黄框）：明显
    (interp([(96,206),(90,196),(94,186),(88,176),(92,166)]), 0.00, 1.0),
    (interp([(148,204),(154,194),(150,184),(156,174),(152,164)]), 0.45, 1.0),
    (interp([(118,214),(112,206),(118,198),(112,190)]), 0.20, 0.8),
    (interp([(40,220),(34,210),(40,200),(34,190)]), 0.65, 0.9),
    (interp([(190,226),(196,216),(190,206),(196,196)]), 0.35, 0.85),
]

# ---------- 仙鹤 ----------
CR_W = np.array([242,246,250],np.float32)   # 白
CR_D = np.array([45,42,50],np.float32)      # 黑（翅尖/喙/腿）
CR_R = np.array([60,60,205],np.float32)     # 丹顶
# 飞行剪影：长颈前伸、长腿后拖、大翅（像素 (dx,dy,color)）
_CR_BODY = [(-1,0,CR_W),(0,0,CR_W),(1,0,CR_W),(2,0,CR_W),   # 身体
            (3,-1,CR_W),(4,-1,CR_W),(5,-2,CR_W),            # 前伸长颈
            (6,-2,CR_W),(6,-3,CR_R),(7,-2,CR_D),(8,-2,CR_D),# 头/丹顶/长喙
            (-2,0,CR_D),                                     # 尾
            (-3,1,CR_D),(-4,1,CR_D),(-5,1,CR_D)]            # 后拖长腿
_CR_WUP  = [(0,-1,CR_W),(1,-1,CR_W),(0,-2,CR_W),(1,-2,CR_W),
            (1,-3,CR_W),(2,-3,CR_D),(2,-4,CR_D)]            # 翅上扬
_CR_WMID = [(0,-1,CR_W),(1,-1,CR_W),(2,-1,CR_W),(3,-2,CR_D)] # 翅平展
_CR_WDN  = [(0,1,CR_W),(1,1,CR_W),(0,2,CR_W),(1,2,CR_W),
            (1,3,CR_W),(2,3,CR_D),(2,4,CR_D)]               # 翅下压
CRANE_FRAMES = [_CR_BODY+_CR_WUP, _CR_BODY+_CR_WMID,
                _CR_BODY+_CR_WDN, _CR_BODY+_CR_WMID]
crane_path = interp([(222,192),(229,202),(260,205),(300,204),(330,205),(355,203)], dens=1)
cranes = [(0.00,0),(0.06,4),(0.12,-1)]   # (相位偏移, y错位) 小编队

def draw_cranes(fa, t, N):
    for p0,dy in cranes:
        # 每循环飞一次：前 62% 时间在飞，其余时间不出现
        prog = ((t/N) - p0) % 1.0
        if prog > 0.62: continue
        u = prog/0.62
        idx = int(u*(len(crane_path)-1))
        x,y = crane_path[idx]; y += dy
        fade = min(u/0.15,1.0) * min((1-u)/0.20,1.0)    # 左渐显右渐隐
        if fade<=0.05: continue
        spr = CRANE_FRAMES[(t//2)%4]
        for dx_,dy_,cc_ in spr:
            xi,yi = int(round(x))+dx_, int(round(y))+dy_
            if 0<=xi<sw and 0<=yi<sh:
                apply_small(fa,[yi],[xi],[cc_],0.9*fade)

def apply_small(fa, ys, xs, cols, alpha):
    """把小格像素以 4x 块叠加到全分辨率帧上"""
    for yy_,xx_,cc_ in zip(ys,xs,cols):
        y0,x0 = yy_*S, xx_*S
        blk = fa[y0:y0+S, x0:x0+S].astype(np.float32)
        fa[y0:y0+S, x0:x0+S] = np.clip(blk*(1-alpha)+cc_*alpha,0,255).astype(np.uint8)

def apply_small_v(fa, ys, xs, cols, alphas):
    for yy_,xx_,cc_,aa_ in zip(ys,xs,cols,alphas):
        y0,x0 = yy_*S, xx_*S
        blk = fa[y0:y0+S, x0:x0+S].astype(np.float32)
        fa[y0:y0+S, x0:x0+S] = np.clip(blk*(1-aa_)+cc_*aa_,0,255).astype(np.uint8)

def render_frame(fa, t, N):
    ph = 2*np.pi*t/N
    # 雾带流动：边界相位沿 x 行进，近快远慢
    nfield = np.sin(ph*2 - gx*0.22*speed + noise*6.28)
    grow = band_out & (nfield>0.55)
    shrink = band_in & (nfield<-0.55)
    ys,xs = np.nonzero(grow)
    apply_small_v(fa, ys, xs, mistcol[ys,xs], alpha_map[ys,xs])
    ys,xs = np.nonzero(shrink)
    apply_small_v(fa, ys, xs, deepcol[ys,xs], alpha_map[ys,xs]*0.9)
    # 建筑边缘雾晕：边界像素随相位生消，绕建筑缓慢流动
    hfield = np.sin(ph*2 - gx*0.18 - gy*0.10 + noise2*6.28)
    hon = halo & (hfield>0.0)
    ys,xs = np.nonzero(hon)
    apply_small_v(fa, ys, xs, halocol[ys,xs], halo_alpha[ys,xs]*np.clip(hfield[ys,xs],0,1.0))
    # 灵气缕：沿路径生长-推进-消散
    for allp,p0,amp in wisp_paths:
        L=len(allp)
        sp = np.arange(L)/max(L-1,1)
        tpos = (sp - (t/N + p0)) % 1.0
        vis = tpos < 0.55
        if not vis.any(): continue
        seg = allp[vis]; tp = tpos[vis]
        head = tp<0.12
        tail = ((tp-0.35)/0.20).clip(0,1)
        for (x,y),h,tl in zip(seg,head,tail):
            xi,yi = int(round(x)), int(round(y))
            if not (0<=xi<sw and 0<=yi<sh): continue
            a = amp*(0.75 if h else 0.45)*(1-tl*0.9)
            if a<=0.03: continue
            col = CYAN*(1.18 if h else 1.0)
            apply_small(fa, [yi],[xi],[col], a)
    draw_cranes(fa, t, N)
    return fa

if __name__ == '__main__':
    src = Image.open(ANIM)
    N = src.n_frames
    out=[]
    for t in range(N):
        src.seek(t)
        fa = cv2.cvtColor(np.array(src.convert('RGB')), cv2.COLOR_RGB2BGR)
        fa = render_frame(fa, t, N)
        out.append(Image.fromarray(cv2.cvtColor(fa,cv2.COLOR_BGR2RGB)))
    out[0].save(OUT,save_all=True,append_images=out[1:],duration=90,loop=0,quality=85,method=4)
    print('saved',OUT)
