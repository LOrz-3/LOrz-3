# LOrz-3/LOrz-3（个人主页）

GitHub profile README。页面上的三张动图都是像素仙侠风成品，**不在本仓库制作**。

## 动图从哪来

制作管线在 [`LOrz-3/pixel-anim-workflow`](https://github.com/LOrz-3/pixel-anim-workflow)：
AI 整幅场景 → 像素化 → GLSL 结构式动效 → ffmpeg 出 webp。
要新做或修改动图（含只是调一下摆幅/浓度这类参数），去那个仓库，
先读它的 `.claude/skills/pixel-scene-anim/SKILL.md`（审美偏好、硬性原则、淘汰清单），
本仓库只负责把成品放进 `assets/` 并更新 README 引用。

注意 `scripts/` 下的 `banner_fx.py` / `mist_fx.py` / `tree_paint.py` 与工作流仓库
**逐字节相同**，是历史遗留的副本。改动效请只改工作流仓库那一份，否则两边会漂移。
（这三份副本可以删，等本人确认。）

## 当前素材

| 文件 | 内容 | 规格 |
|---|---|---|
| `assets/banner_framed.webp` | 仙山云海头图（含鎏金回纹画框） | 1536×1024 / 48 帧 |
| `assets/divider.webp` | 灵剑分隔条 | 1536×349 / 48 帧 |
| `assets/fairy_dance_framed.webp` | 《仙子夜湖·凌波舞》尾图 | 1536×1024 / 96 帧 |
| `assets/footer.webp` | 月下扁舟（旧尾图，已被替换，存档保留） | 1536×1024 / 48 帧 |
| `assets/sprites/` | 人物透明精灵 + 48 帧动画、仙鹤 4 帧精灵表 | |

`banner.webp` / `fairy_dance.webp` 是未加画框的原图，README 引用的是 `*_framed` 版本。

## README 注意事项

- GitHub README 不支持 CSS 边框，画框是**直接绘进图片像素**的（4px 像素格）
- 第三方统计卡片（github-readme-stats）已删除：服务加载失败会显示成裂图
- 课程成果表格用 `<table align="center">` 使表格整体居中，单元格内保持左对齐
