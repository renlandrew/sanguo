"""城头武将的 Veo 视频 → 原型用的图集（10-24）。

输入：<帧图目录>/<键><序号>_<动作>.jpg（如 guan1_atk.jpg），每张是一条 4 秒视频的 40 帧（0.2–3.45 秒，每秒 12 帧），8 列 × 5 行，
      在浏览器里从 Cloud Storage 的视频截出来。
输出：三国志/原型/img/g_<键>.png + .json（格式同敌人的图集：stand 是人站直的像素高，anims 每段 rects + 脚底锚点）。
做法照劫云问道 cut_takes.py：灰底取第一帧两侧每行的中位数，和四边连通的近灰都算背景，只留和身体连着的最大一块；
同一个人的几条视频首帧一样、镜头不动，脚底位置取待机第一帧，各段按同一比例缩放（人站直 STAND 像素）；灰底每帧单独取（Veo 的灰会慢慢变亮）。
抠完只描一圈细墨线和纸色光晕（免得在城砖上看不清），颜色全留原样——10-24 用户：「风格可以改一下，不要那么水墨」。
敌人（张角、黄巾骑兵，make_foe_pack.py 录的正面）也用这个切：输出 原型/img/<键>.png，动作键按游戏里敌人的叫法（run/ram/hit/die/fly、斗将的 idle/cast/summon），
缺的键在 ALIAS 里借别的段。
用法：<media-venv>/bin/python 三国志/工具/veo/cut_generals.py <帧图目录> [guan zhang liu zhangjiao qibing]
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'blender')); from ink_post import ink
SRC = Path(sys.argv[1]); OUT = HERE.parents[1] / '原型' / 'img'
COLS, ROWS, N, FPS, T0 = 8, 5, 40, 12, .2
import os
STAND = int(os.environ.get('STAND', 260))           # 人站直缩到 260 像素高（游戏里约 78 点高，三倍屏也够）；斗将敌将画得大 2.2 倍，10-29 按 STAND=440 重切（用户嫌糊）
# 每段取哪几帧（在 40 帧里的序号）：待机取前一秒多来回播；普攻、招式取整个动作；受击取前半段
PICK = {'idle': list(range(12, 40, 2)),   # 10-27 站立待机（衣服随风）：前 12 帧 Veo 从首帧淡入带重影，从 12 起
        'idle_old': list(range(0, 16, 2)), 'atk': list(range(0, 36, 3)), 'skill': list(range(0, 40, 3))}
# 受击那三条中途转身、背景忽亮忽暗，城头武将在守关里也不挨打，先不用（10-24）
# 某条视频坏了（转身、冒烟）时在这里截断：{'guan2_skill': 30}
END = {'zhang2_skill': 22, 'liu2_skill': 26}       # 第三版：张飞吼完后半段转成侧身、刘备旋斩完转成正面，都只取前面那段
# 第三版每人每段从哪条视频取哪几帧：{键: {段: (哪条, 帧序号)}}，没写的照 PICK。
# 10-24 用户：「这张飞跳来跳去，好像个青蛙」「只要多变化即可」「跳没关系，但张飞是一直在跳」——
# 普攻切成两三段（atk、atk2、atk3），游戏里轮着用、跳的那段少出；待机只取站稳的几帧。
# 张飞「普攻」那条是原地跳起再落下，「待机」那条反倒是完整的举矛、端平、刺出，所以刺用待机那条、跳用普攻那条。
PLAN = {
    'zhang': {'idle': ('atk', range(0, 18, 2)), 'atk': ('idle', range(4, 28, 2)), 'atk2': ('atk', range(18, 40, 2))},                       # 刺矛；跳起举矛
    'guan': {'idle': ('idle', range(30, 40, 2)), 'atk': ('atk', range(2, 26, 2)), 'atk2': ('idle', range(4, 28, 2)), 'atk3': ('atk', range(24, 40, 2))},   # 马步横扫；举刀抡一圈；往前劈
    'liu': {'idle': ('idle', range(0, 6)), 'atk': ('idle', range(4, 26, 2)), 'atk2': ('atk', range(2, 28, 2))},                             # 双剑翻转连斩；跃起交叉双剑
    # 张角（make_foe_pack.py）：施法那条 Veo 加了一大团白烟，只取举杖递符的前 4 帧；待机后面背景里有风痕，只取前 12 帧；受击借倒下那条开头踉跄的几帧
    'zhangjiao': {'idle': ('idle', range(0, 12, 2)), 'cast': ('cast', range(0, 4)), 'summon': ('summon', range(0, 40, 3)), 'hit': ('die', range(0, 10, 2)), 'die': ('die', range(6, 40, 3))},
    # 黄巾骑兵：冲锋那条按剪影算出步伐约 9 帧一周，12–19 帧接回 12 帧最顺；马上那条人立挺枪；落马倒地
    'qibing': {'run': ('run', range(12, 20)), 'ram': ('ram', range(2, 32, 3)), 'die': ('die', range(4, 30, 2))},
    # 第 11–30 关（make_foe_pack2.py，10-25）：三种骑兵的冲锋按剪影找的一周（铁骑 8 帧、弓骑 9、狼骑 11）；敌将按斗将招式起名（heavy/combo/rush/taunt/summon），受击借倒下那条开头；潘凤、武安国只录了劈砍
    'tieqi': {'run': ('run', range(15, 23)), 'ram': ('ram', range(10, 40, 3)), 'die': ('die', range(6, 34, 2))},   # 落马第 5 帧 Veo 加了一团白光，从 6 起
    'gongqi': {'run': ('run', range(20, 29)), 'shoot': ('shoot', range(16, 40, 2)), 'die': ('die', range(0, 20, 2))},   # 弓骑落马后马还站着，只取人摔下来那段
    'langqi': {'run': ('run', range(14, 25)), 'ram': ('ram', range(0, 40, 3)), 'die': ('die', range(6, 30, 2))},   # 落马第一版人马飞出画面，重录了一条（马跪倒侧翻）
    'huzhen': {'idle': ('combo', range(30, 40, 2)),   # 待机那条 Veo 加了越来越多的风痕线（第 2 帧起），改用连斩收势后站定那几帧
                'combo': ('combo', range(0, 40, 3)), 'summon': ('summon', range(0, 40, 3)), 'hit': ('die', range(0, 10, 2)), 'die': ('die', range(6, 40, 3))},
    'huaxiong': {'idle': ('idle', range(0, 9)), 'taunt': ('taunt', range(4, 40, 3)), 'heavy': ('heavy', range(4, 30, 2)),   # 待机第 10 帧起 Veo 加了绕身的红飘带；重斩劈下时溅的血点不连身子，抠图时自然丢掉
                 'summon': ('summon', range(4, 36, 3)), 'hit': ('die', range(15, 21)), 'die': ('die', range(14, 40, 2))},   # 倒下那条先举了一下刀（0–13 帧），从跪下那段起取
    'lijue': {'idle': ('idle', range(0, 16, 2)), 'heavy': ('heavy', range(4, 40, 3)), 'summon': ('summon', range(4, 36, 3)), 'hit': ('die', range(18, 24)), 'die': ('die', range(16, 40, 2))},   # 倒下那条也先举刀，从踉跄那段起取
    'lvbu': {'idle': ('idle', range(0, 16, 2)), 'heavy': ('die', range(0, 14)), 'rush': ('rush', range(14, 40, 2)), 'hit': ('die', range(14, 20)), 'die': ('die', range(14, 40, 2))},   # 10-27 新画风重录：重击那条背景冒出一大团深蓝，改用倒下那条开头的挥戟   # 倒下第 5、6 帧胸口 Veo 加了一团亮光，从 9 起
    'gaoshun': {'run': ('run', range(21, 32)), 'ram': ('ram', range(6, 40, 3)),   # 跑步一周 11 帧；开头镜头还在追，人先小后大，按身宽归一（FIT）
                 'hit': ('die', range(18, 24)), 'die': ('die', range(14, 40, 2))},   # 倒下：戟断了、躲到盾后单膝跪地
    # 10-29 新画首录（make_foe_pack4.py）：邓茂斗将（原来借程远志的 3D 模型）；旗手、张宝、督邮朝镜头原地走／跑；督邮出手那条第 8 帧起灰底上有斜光纹
    'dengmao': {'idle': ('idle', range(0, 24, 2)), 'heavy': ('heavy', range(4, 40, 3)), 'summon': ('summon', range(4, 40, 3)), 'hit': ('die', range(0, 8, 2)), 'die': ('die', range(6, 40, 3))},
    'qishou': {'run': ('run', range(16, 32)), 'ram': ('ram', range(4, 34, 2)), 'die': ('die', range(4, 34, 2))},
    'zhangbao': {'run': ('run', range(8, 32, 2)), 'ram': ('cast', range(0, 40, 3)), 'die': ('die', range(4, 40, 3))},
    'duyou': {'run': ('run', range(8, 32, 2)), 'ram': ('ram', range(0, 40, 3)), 'die': ('die', range(0, 34, 2))},
    'panfeng': {'idle': ('ram', range(0, 4)), 'ram': ('ram', range(0, 40, 3))},
    'wuanguo': {'idle': ('ram', range(0, 4)), 'ram': ('ram', range(0, 40, 3))},
}

# 10-27 新画风重录时个别人的段换来源：刘备待机那条 Veo 整条叠了两个人（10-28 用户：「这里 2 个刘备」），改用普攻那条末尾站定的 9 帧
NEW_PLAN = {'liu': {'idle': ('atk', range(31, 40))}}

# 镜头中途推近了的那几条（10-25：西凉铁骑撞城那条，人马越来越大）：这一段按它自己第一帧的马身宽度缩回和定脚底那条一样大，脚底也用它自己的
FIT = {('tieqi', 'ram'), ('gaoshun', 'run')}

def body(m):
    # 人马的「身宽」：剪影下半截每行宽度的九成分位（举起的矛、刀不算），和脚底、中线
    ys = np.where(m.any(axis=1))[0]; top, feet = ys.min(), ys.max() + 1; band = m[top + int((feet - top) * .55):feet]
    wid = np.array([np.ptp(r.nonzero()[0]) + 1 if r.any() else 0 for r in band]); cols = np.where(m[feet - 14:feet].any(axis=0))[0]
    return np.percentile(wid, 90), feet, (cols.min() + cols.max()) / 2

ALIAS = {'zhangjiao': {'run': 'idle', 'ram': 'cast', 'fly': 'die'}, 'qibing': {'hit': 'run', 'fly': 'die'},   # {键: {缺的动作: 借哪一段}}
         'tieqi': {'hit': 'run', 'fly': 'die'}, 'langqi': {'hit': 'run', 'fly': 'die'}, 'gongqi': {'hit': 'run', 'fly': 'die', 'ram': 'shoot'},
         'huzhen': {'run': 'idle', 'ram': 'combo', 'cast': 'combo', 'heavy': 'combo', 'fly': 'die'},
         'huaxiong': {'run': 'idle', 'ram': 'heavy', 'cast': 'heavy', 'fly': 'die'}, 'lijue': {'run': 'idle', 'ram': 'heavy', 'cast': 'heavy', 'fly': 'die'},
         'lvbu': {'run': 'rush', 'ram': 'heavy', 'cast': 'heavy', 'fly': 'die'}, 'gaoshun': {'fly': 'die'},
         'panfeng': {'run': 'idle'}, 'wuanguo': {'run': 'idle'},
         'dengmao': {'run': 'idle', 'ram': 'heavy', 'cast': 'heavy', 'fly': 'die'}, 'qishou': {'hit': 'run', 'fly': 'die'},
         'zhangbao': {'hit': 'run', 'fly': 'die', 'cast': 'ram'}, 'duyou': {'hit': 'run', 'fly': 'die'}}

def gray_of(rgb):
    a = rgb.astype(np.float32)
    return ndi.median_filter(np.median(np.concatenate([a[:, :6], a[:, -6:]], axis=1), axis=1), size=(15, 1))[:, None, :]

def flat_gray(rgb):
    # 一帧的灰底：四边像素里几乎无色的那些取中位数（刀、披风甩到边上时，边上那几行不能拿来当灰）
    a = rgb.astype(np.float32); edge = np.concatenate([a[:6].reshape(-1, 3), a[-3:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    v = edge.max(axis=1); sat = (v - edge.min(axis=1)) / np.maximum(v, 1); g = edge[sat < .06]
    return np.broadcast_to(np.median(g if len(g) > 50 else edge, axis=0), (a.shape[0], 1, 3))

def matte(rgb, bg):
    a = rgb.astype(np.float32)
    distance = np.max(np.abs(a - bg), axis=2)
    v = a.max(axis=2); bv = np.broadcast_to(bg, a.shape).max(axis=2)
    sat = (v - a.min(axis=2)) / np.maximum(v, 1)
    near = (distance < 18) | ((sat < .1) & (v > .6 * bv) & (v < bv + 8))
    seeds = np.zeros(near.shape, bool); seeds[0] = near[0]; seeds[-1] = near[-1]; seeds[:, 0] = near[:, 0]; seeds[:, -1] = near[:, -1]
    bgm = ndi.binary_propagation(seeds, mask=near)
    holes, n = ndi.label((distance < 15) & (sat < .12) & ~bgm)                       # 胳膊和兵器围出来的灰
    sizes = np.bincount(holes.ravel()); sizes[0] = 0
    bgm |= ndi.binary_propagation(np.isin(holes, np.where(sizes > 40)[0]), mask=(distance < 18) & (sat < .14))
    solid = ~bgm
    labels, count = ndi.label(ndi.binary_dilation(solid, iterations=2))
    if count > 1:
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        solid &= labels == sizes.argmax()
    alpha = ndi.gaussian_filter(solid.astype(np.float32), .6)
    alpha[solid & (ndi.distance_transform_edt(solid) > 1.2)] = 1
    unmix = (a - (1 - alpha[..., None]) * bg) / np.maximum(alpha[..., None], .15)
    rgba = np.dstack([np.clip(unmix, 0, 255), alpha * 255]).astype(np.uint8); rgba[alpha < .02] = 0
    return rgba

def cells(path):
    sheet = np.asarray(Image.open(path).convert('RGB')); ch, cw = sheet.shape[0] // ROWS, sheet.shape[1] // COLS
    return [sheet[(i // COLS) * ch:(i // COLS + 1) * ch, (i % COLS) * cw:(i % COLS + 1) * cw] for i in range(N)]

FOE = {'dengmao', 'qishou', 'zhangbao', 'duyou', 'zhangjiao', 'qibing', 'tieqi', 'gongqi', 'langqi', 'huzhen', 'huaxiong', 'lijue', 'lvbu', 'gaoshun', 'panfeng', 'wuanguo'}   # 敌人和友军：图集不带 g_ 前缀
for g in (sys.argv[2:] or ['guan', 'zhang', 'liu']):
    takes = {p.stem.split('_', 1)[1]: p for p in SRC.glob(f'{g}[0-9]_*.jpg')}
    base = 'idle' if 'idle' in takes else next(iter(PLAN.get(g, {}).values()), (None,))[0]   # 脚底和缩放按这条的首帧定
    if base not in takes: print(g, '没有定脚底的那条，跳过'); continue
    first = cells(takes[base])[0]; bg = gray_of(first); m0 = matte(first, bg)[..., 3] > 40
    ys = np.where(m0.any(axis=1))[0]; fig0, feet0 = ys.max() - ys.min() + 1, ys.max() + 1
    cols0 = np.where(m0[feet0 - 14:feet0].any(axis=0))[0]; cx0 = (cols0.min() + cols0.max()) / 2
    k = STAND / fig0; bw0 = body(m0)[0]
    strips, meta = [], {'stand': STAND, 'anims': {}}
    import os; NEWP = os.environ.get('NEWPLAN') == '1'   # 10-27 新画风重录：刘关张不用旧的 PLAN（那是按旧视频挑的帧），照 PICK
    for anim, (src, idx) in (PLAN[g] if g in FOE else {**{a: (a, i) for a, i in PICK.items()}, **(NEW_PLAN.get(g, {}) if NEWP else PLAN.get(g, {}))}).items():
        if src not in takes: continue
        tid = takes[src].stem; end = END.get(tid, N - 1); cs = cells(takes[src])
        frames = []
        for i in [i for i in idx if i <= end]:
            f = matte(cs[i], flat_gray(cs[i]))                                       # Veo 的灰底会随时间变亮，每帧单独取
            edge = np.concatenate([f[:4, :, 3].ravel(), f[-4:, :, 3].ravel(), f[:, :4, 3].ravel(), f[:, -4:, 3].ravel()])
            if frames and (edge > 128).mean() > .3: print('  ', tid, '帧', i, '灰底没抠掉，用上一帧'); frames.append(frames[-1]); continue
            frames.append(f)
        kk, cx, feet = k, cx0, feet0
        if (g, anim) in FIT: bw, feet, cx = body(frames[0][..., 3] > 40); kk = k * bw0 / bw; print('  ', tid, '按马身宽缩', round(bw0 / bw, 2))
        al = np.stack([f[..., 3] > 40 for f in frames]); ys, xs = np.where(al.any(axis=0))
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1               # 整段一个外框，脚底不动
        W, H = int(np.ceil((x1 - x0) * kk)) + 16, int(np.ceil((y1 - y0) * kk)) + 16    # 留 8 像素给墨线和光晕
        ims = []
        for f in frames:
            im = Image.fromarray(f[y0:y1, x0:x1], 'RGBA').resize((W - 16, H - 16), Image.Resampling.LANCZOS)
            pad = Image.new('RGBA', (W, H), (0, 0, 0, 0)); pad.paste(im, (8, 8)); ims.append(ink(pad, keep=1, line=int(os.environ.get('INK_LINE', 3)), halo=int(os.environ.get('INK_HALO', 4))))   # 10-27 用户嫌吕布「阴影好严重」：新画风重录时 INK_LINE=1 INK_HALO=0
        strips.append((anim, ims, [round((cx - x0) * kk + 8, 1), round((feet - y0) * kk + 8, 1)]))
        print(g, anim, tid, len(ims), '帧', f'{W}x{H}')
    PER = 8                                                                             # 一行最多 8 帧，图集长宽都别超过 4096（手机上贴图边长有上限）
    AW = max(ims[0].width * min(PER, len(ims)) for _, ims, _ in strips); AH = sum(ims[0].height * -(-len(ims) // PER) for _, ims, _ in strips)
    atlas = Image.new('RGBA', (AW, AH)); y = 0
    for anim, ims, anchor in strips:
        rects = []
        for j, im in enumerate(ims):
            x, yy = (j % PER) * im.width, y + (j // PER) * im.height; atlas.paste(im, (x, yy)); rects.append([x, yy, im.width, im.height])
        meta['anims'][anim] = {'rects': rects, 'anchor': anchor}; y += ims[0].height * -(-len(ims) // PER)
    for a, src in ALIAS.get(g, {}).items(): meta['anims'][a] = meta['anims'][src]
    name = g if g in FOE else 'g_' + g
    atlas.save(OUT / f'{name}.png', optimize=True); (OUT / f'{name}.json').write_text(json.dumps(meta, ensure_ascii=False))
    print(g, '图集', atlas.size, (OUT / f'{name}.png').stat().st_size // 1024, 'KB')
