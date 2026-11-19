# -*- coding: utf-8 -*-
"""第三章敌人首录（11-18，用户：「需要画画和veo就自己调」）。原来借第二章图集调色（tintOwn）。
首帧：美术/第三章/立绘/pt_<键>.png（敌将，Codex 画的灰底正面全身立绘）、foe_<键>.png（新兵种）；铺灰后按人物外框缩放、贴底居中（ref 借 make_foe_pack2）。
兵种各 3 条（朝镜头原地跑、出手、倒下），敌将 4 条（待机、重招、连招或护阵、倒下；颜良多一条召兵）：共 30 条约 18 美元（设计/第三章设定.md 第六节）。
Cloud Shell：SHOTS=shots_foe7.json SECONDS=4 CAP_USD=… python3 veo_wendao.py
用法：python3 三国志/工具/veo/make_foe_pack7.py <输出目录> [只录哪几个键]
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ONLY = sys.argv[2:]
src = (HERE / 'make_foe_pack2.py').read_text(encoding='utf-8').split('\nSHOTS = {')[0]
g = {'__file__': str(HERE / 'make_foe_pack2.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src, g)
ref, BASE, TAIL, NEG, RUN, DIE, IDLE, SUMMON = (g[k] for k in ('ref', 'BASE', 'TAIL', 'NEG', 'RUN', 'DIE', 'IDLE', 'SUMMON'))
GUARD = "plants his feet, raises his weapon crosswise in front of his chest and holds a firm guarding stance for a moment, glaring at the camera, then lowers it back to his stance."
SHOTS = {
 'hebei': ("a Yuan Shao infantryman in an ochre-yellow cloth armor and an ochre head scarf, gripping a long spear, a short sword at his hip", [
   ('run', RUN.replace('his arms, cape and armor plates swing', 'his arms and scarf swing')),
   ('ram', "stops and stabs the long spear forward toward the camera twice in quick jabs, then pulls it back."),
   ('die', DIE.replace('drops his weapon', 'drops his spear'))]),
 'daji': ("a big elite Yuan Shao halberdier officer in ochre-yellow and dark iron heavy plate armor with an ochre iron helmet, holding a long ji halberd (a long pole with a crescent side blade and a straight spear tip) with both hands", [
   ('run', RUN),
   ('ram', "stops, swings the long halberd overhead and chops it down toward the camera in a big blow, then sweeps it back across once more, shouting."),
   ('die', DIE.replace('drops his weapon', 'drops his halberd'))]),
 'xiandeng': ("a lean, fierce Yuan Shao vanguard death-squad soldier with a red cloth band around his head, an ochre short jacket under light leather armor, a small round shield and a short sword", [
   ('run', RUN.replace('charges straight toward the camera on foot at a heavy run', 'sprints straight toward the camera on foot').replace('his arms, cape and armor plates swing', 'his arms and the red head band swing')),
   ('ram', "stops, bashes forward with the small round shield and then slashes the short sword toward the camera twice, fast and reckless."),
   ('die', DIE.replace('drops his weapon', 'drops his sword and shield'))]),
 'xuchu': ("the huge Cao Cao bodyguard general Xu Chu, a massively muscular man with a round face and a short stiff beard, his right arm and half his chest bare, a reddish-brown robe, a dark iron pauldron on his left shoulder, holding a thick long-handled broad blade", [
   ('idle', IDLE),
   ('heavy', "raises the long broad blade high over his head with both hands and smashes it down toward the camera in one huge blow, then heaves it back up."),
   ('combo', "swings the broad blade toward the camera left and right in three fast heavy slashes, roaring, then returns to his stance."),
   ('die', DIE)]),
 'yanliang': ("the Yuan Shao general Yan Liang, a tall fierce man with a long black beard in ochre-gold and dark-red heavy plate armor, a golden helmet with a red plume and a dark-red cape, holding a long-handled broad glaive", [
   ('idle', IDLE),
   ('heavy', "lifts the glaive high and chops it straight down toward the camera in one heavy blow, then raises it again."),
   ('combo', "sweeps the glaive in a wide horizontal arc from right to left across the front of the camera, then back from left to right, and returns to his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'caiyang': ("the old Cao Cao general Cai Yang, white-haired with a white beard, a hard angry face, iron-grey heavy plate armor and a dark-blue cape, holding a long-handled broad glaive", [
   ('idle', IDLE),
   ('heavy', "raises the glaive high and cleaves it diagonally down toward the camera in one powerful stroke, then returns to his stance."),
   ('combo', "slashes toward the camera twice in quick succession, a rising cut then a falling cut, and steps back into his stance."),
   ('die', DIE)]),
 'gaolan': ("the general Gao Lan, a lean sharp-faced man with a short beard in ochre-yellow plate armor and a dark-brown war robe, an ochre helmet, holding a long spear", [
   ('idle', IDLE),
   ('heavy', "pulls the long spear back and drives it straight toward the camera in one huge thrust, then snaps it back to his stance."),
   ('combo', "stabs the spear toward the camera three times in very fast jabs, then twirls it once and returns to his stance."),
   ('die', DIE)]),
 'caoren': ("the Cao Cao general Cao Ren, a stern square-faced man with a short beard in dark blue-black heavy plate armor, a black iron helmet with a blue plume, a long rectangular black shield in his left hand and a long sabre in his right", [
   ('idle', IDLE),
   ('heavy', "raises the sabre and chops it down toward the camera in one heavy blow from behind his shield, then raises the shield again."),
   ('guard', GUARD.replace('raises his weapon crosswise in front of his chest', 'raises the big black shield in front of his body')),
   ('die', DIE.replace('drops his weapon', 'drops his sabre and shield'))]),
}
if ONLY: SHOTS = {k: v for k, v in SHOTS.items() if k in ONLY}
shots = []
for k, (who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
tmp = out / 'gray'; tmp.mkdir(exist_ok=True)
with tarfile.open(out / 'foe_pack7.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in SHOTS:
        d = ROOT / '美术' / '第三章' / '立绘'; f = d / f'foe_{k}.png'; f = f if f.exists() else d / f'pt_{k}.png'
        im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        p = tmp / f'{k}.png'; bg.convert('RGB').save(p)
        data = ref(p); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe7.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack7.tar.gz', (out / 'foe_pack7.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
