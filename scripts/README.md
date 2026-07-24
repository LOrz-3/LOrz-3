# 动效生成脚本（可复用素材）

基于 `assets/banner.png`（静态底图，1536×1024）生成动态 `assets/banner.webp` 的像素动画脚本。
依赖：`pip install opencv-python-headless numpy pillow`，在仓库根目录运行。

## 脚本

- `banner_fx.py`：背景动效——灯笼绕挂点摆动、樱花树梯度弯曲重绘、青色灵气沿路径生长-推进-消散、云雾边缘结构演变。输入 `assets/banner.webp`（含人物动效），输出 `/tmp/banner_final.webp`。
- `tree_paint.py`：樱花树冠向右延伸的静态重绘（枝干路径 + 花簇 patch 采样），可独立预览。
- `mist_fx.py`：三层纵深雾流（近/远/更远）、人物附近灵气缕、像素仙鹤编队飞过、建筑边缘雾晕。输入当前 `assets/banner.webp`，输出 `/tmp/banner_mist.webp`。

## 复用素材

- `assets/sprites/crane_frames.png`：仙鹤 4 帧扇翅精灵表（上扬/平展/下压/平展，8x 放大，透明背景）；源坐标定义见 `mist_fx.py` 中 `CRANE_FRAMES`。
- 通用工具：`interp()` 路径插值、`apply_small()` 4x 像素块叠加、雾带边缘生消（`band_out`/`band_in` + 相位场）可直接搬到其他像素图动画。

## 用法示例

```bash
python3 scripts/mist_fx.py         # 在最新 banner.webp 上叠加雾气/仙鹤等
cp /tmp/banner_mist.webp assets/banner.webp
```
