# 11-02 主页背景重画（用户：「这个背景图我觉的不好，没特色，没展示出游戏的特点，还花眼睛」）

现在的主页底图是 `原型/img/bg.jpg`：远山、河、城、田、树一大片，处处是细节，跟守关玩法没关系。
刘关张是单独一张抠图（`IMG.trio`）叠在上面，所以**背景里不画人物**。

要表达的就是这个游戏：**我们守在城头，黄巾从远处一路杀过来。**

版面（竖屏 9:16，按 360×640 的位置说）：
- 最上 1/5（y 0–130）：标题「群雄逐鹿」压在这里 → 天空要平、暗、干净。
- 中间（y 140–460）：刘关张站在这里 → 人后面的背景要暗、色块大，人要跳出来。
- 下面（y 460–640）：点卯条、出征卡、底栏 → 底部城墙城砖，压暗，几乎没细节。

存 `美术/场景/主页背景_守关.png`，我缩成 `原型/img/bg.jpg` 换上（也是没底图的关卡的垫底图）。

## 主页背景（竖版 9:16）

```text
Vertical 9:16 mobile game title-screen background, Three Kingdoms era, the view from behind the battlements of a besieged Han dynasty city gate looking out over the battlefield at dusk: the bottom fifth of the image is the top of the city wall seen close up, a simple row of large dark weathered stone battlements and a wooden rail with two red Han war banners at the sides; beyond the wall a wide empty dusty plain leads straight to the horizon, and on the far horizon a vast Yellow Turban rebel army is gathering — only a long soft band of countless small yellow banners and torch glows, no individual faces or detailed soldiers; above them a huge dark storm sky with heavy rolling purple-gray clouds and one distant purple lightning bolt; the upper part of the sky is calm, dark and plain; strong depth, the whole image is quiet and simple with few large color areas, warm torch-orange and yellow on the horizon against cool deep blue-purple sky and dark brown stone, bright hand-painted game illustration with light ink-wash brush texture, NO people in the foreground, no characters, no text, no logo, no UI, no dark outlines, no dense small details, no busy patterns
```

要点：
- **一眼就是「守关」**：近处是我方城垛，远处是黄巾大军（只要一长条黄旗火光，不要画清每个兵）。
- **不花眼**：大色块，天空和中间几乎平的，只有地平线那一条亮、有一道远处紫雷（张角）。
- **背景里不要人**：刘关张会单独叠在中间；画了人就会两套人打架。
- 中间段要比人物暗、偏冷，人物（红绿白蓝）才跳得出来。
