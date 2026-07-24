"""Paint an extension of the cherry tree crown into the top sky area (small-res grid)."""
import numpy as np, cv2

def paint_tree_ext(sm, seed=5):
    sm = sm.copy()
    b,g,r = [sm[:,:,i].astype(np.int16) for i in range(3)]
    lum = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.int16)
    pink = (r>g+15)&(r>b+18)&(lum<225)
    rng = np.random.default_rng(seed)

    # wood palette sampled from existing dark branches
    woodmask = (lum<95)&(np.mgrid[0:sm.shape[0],0:sm.shape[1]][1]<60)
    woodmask[90:,:]=False
    wys,wxs = np.nonzero(woodmask)
    woodcols = sm[wys,wxs]

    # blossom source patches (7x7) from existing crown
    cnt = cv2.boxFilter(pink.astype(np.float32),-1,(7,7),normalize=False)
    gy,gx = np.mgrid[0:sm.shape[0],0:sm.shape[1]]
    cand = np.argwhere((cnt>30)&(gx<58)&(gy>6)&(gy<70))
    patches=[]
    for (py,px) in cand[rng.choice(len(cand), 40, replace=False)]:
        y0,x0 = py-3,px-3
        if y0<0 or x0<0: continue
        pat = sm[y0:y0+7, x0:x0+7].copy()
        pm  = pink[y0:y0+7, x0:x0+7] | (lum[y0:y0+7, x0:x0+7]<110)
        if pm.sum()>=22: patches.append((pat,pm))

    def draw_branch(pts, w0):
        pts = np.array(pts, np.float32)
        allp=[]
        for i in range(len(pts)-1):
            n = int(np.hypot(*(pts[i+1]-pts[i]))*3)+1
            for t in np.linspace(0,1,n):
                allp.append(pts[i]*(1-t)+pts[i+1]*t)
        allp=np.array(allp)
        L=len(allp)
        for i,(x,y) in enumerate(allp):
            wdt = max(1, int(round(w0*(1-i/L))))
            col = woodcols[rng.integers(len(woodcols))]
            cv2.circle(sm,(int(round(x)),int(round(y))),wdt//2,col.tolist(),-1)
        return allp

    def blossoms_along(allp, every=7, prob=0.9):
        L=len(allp)
        i= int(every*0.7)
        while i < L:
            if rng.random()<prob and patches:
                x,y = allp[i]
                x += rng.integers(-2,3); y += rng.integers(-3,2)
                pat,pm = patches[rng.integers(len(patches))]
                x0,y0 = int(x)-3, int(y)-3
                if 0<=x0 and 0<=y0 and x0+7<sm.shape[1] and y0+7<sm.shape[0]:
                    roi = sm[y0:y0+7, x0:x0+7]
                    roi[pm] = pat[pm]
            i += every + int(rng.integers(0,4))
        # tip cluster
        x,y = allp[-1]
        for _ in range(2):
            pat,pm = patches[rng.integers(len(patches))]
            x0 = int(x)-3+int(rng.integers(-2,3)); y0=int(y)-3+int(rng.integers(-2,3))
            if 0<=x0 and 0<=y0 and x0+7<sm.shape[1] and y0+7<sm.shape[0]:
                roi = sm[y0:y0+7, x0:x0+7]; roi[pm]=pat[pm]

    # main new branches growing right into the sky zone (small coords)
    A = draw_branch([(52,14),(72,8),(92,12),(112,7),(124,10)], 3)
    B = draw_branch([(54,30),(74,26),(94,30),(110,24),(122,27)], 3)
    C = draw_branch([(50,44),(68,48),(84,42),(96,45)], 2)
    # twigs
    t1 = draw_branch([(80,10),(88,18),(97,20)], 1)
    t2 = draw_branch([(96,28),(103,35),(112,38)], 1)
    t3 = draw_branch([(70,26),(76,17)], 1)
    for path,ev in [(A,6),(B,6),(C,7),(t1,6),(t2,6),(t3,6)]:
        blossoms_along(path, ev)
    return sm

if __name__ == '__main__':
    img = cv2.imread('assets/banner.png')
    sm = cv2.resize(img,(384,256),interpolation=cv2.INTER_NEAREST)
    out = paint_tree_ext(sm)
    cv2.imwrite('/tmp/tree_ext.png', cv2.resize(out[:100,:140],None,fx=5,fy=5,interpolation=cv2.INTER_NEAREST))
    cv2.imwrite('/tmp/tree_ext_full.png', cv2.resize(out,(1536,1024),interpolation=cv2.INTER_NEAREST))
