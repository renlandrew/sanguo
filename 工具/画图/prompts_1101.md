# 11-01 七星灯提示词（用户：「写提示词」）

第十关张角拜北斗时场上的七盏灯，现在是程序画的铜灯台，像普通火把架。
照现有道具图的画法：正面略俯视、亮色厚涂、纯中灰底、只画一个、四周留空、不要文字。
存 `美术/道具/七星灯.png`；画好后抠图进 props 图集（`工具/cut_props.py`），游戏里替换 `drawLamp` 的灯台。

**灯盏里不要画火。** 火苗是游戏里用火焰纹理画的，挨打会一截截变矮；画进图里就动不了了。

## 七星灯（灯台本体，1:1）

```text
A single Taoist ritual oil lamp for a star-worship ceremony, Three Kingdoms era: a short bronze lamp stand with a round three-legged base, a slender stem wrapped with a strip of yellow talisman paper with red brush marks (no readable characters), and a wide shallow bronze oil dish on top with a small upright wick, the dish edge decorated with a simple seven-star (Big Dipper) dot pattern; the lamp is NOT lit, no flame, no glow; seen from the front at a slight top-down view, bright hand-painted game illustration, warm bronze and talisman yellow colors, large clean shapes, no fine noisy details, plain mid-gray background, single object, centered with generous margin, no text, no dark outline
```

要点：
- 要和城头火把、草棚火一眼分开：靠**黄符纸条**和**灯盏边的七星点纹**。
- 灯盏要宽而浅，火苗会从灯芯位置长出来。
- 画面里大约是一个手掌高的小物件，缩到游戏里只有约 40 像素高，所以要大色块、清楚的剪影。
