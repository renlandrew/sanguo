"""第二章敌人首录（11-08，用户：「敌将动作报价」→「全做上限 32 美元」）。原来都借第一章图集换色（tintOwn）。
首帧：美术/第二章/敌人正面/<键>.png（Codex 画，中灰底 2:3；敌将造型照剧情立绘），铺灰后按人物外框缩放、贴底居中（ref 借 make_foe_pack2）。
兵种各 3 条（朝镜头原地跑、出手、倒下；虎豹骑同第一章骑兵：原地奔、人立挺枪、落马），敌将按招式表 3–5 条（待机、重招、连招、掷戟、召兵、倒下）。
共 40 条 × 4 秒 × .15 ≈ 24 美元，Cloud Shell：SHOTS=shots_foe6.json SECONDS=4 CAP_USD=32 python3 veo_wendao.py
用法：python3 三国志/工具/veo/make_foe_pack6.py <输出目录> [只录哪几个键]
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ONLY = sys.argv[2:]   # 11-08 Codex 额度用完：先只录有剧情立绘（灰底正面全身）的四员敌将，首帧直接用立绘原图
src = (HERE / 'make_foe_pack2.py').read_text(encoding='utf-8').split('\nSHOTS = {')[0]
g = {'__file__': str(HERE / 'make_foe_pack2.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src, g)
ref, BASE, TAIL, NEG, RUN, DIE, IDLE, SUMMON, GALLOP, FALL = (g[k] for k in ('ref', 'BASE', 'TAIL', 'NEG', 'RUN', 'DIE', 'IDLE', 'SUMMON', 'GALLOP', 'FALL'))
SHOTS = {
 'caobing': ("a Cao Cao infantryman in blue-grey cloth under iron-grey plate armor and a round iron helmet, a tall rectangular blue-grey wooden shield on his left arm and a long ji halberd in his right hand", [
   ('run', RUN),
   ('ram', "stops, braces behind his raised shield and thrusts the halberd forward toward the camera twice from behind the shield, then pulls it back."),
   ('die', DIE.replace('drops his weapon', 'drops his halberd and shield'))]),
 'nushou': ("a Cao Cao crossbowman in a blue-grey short robe and leather armor with a soft blue-grey cap, holding a wooden crossbow, a quiver at his hip", [
   ('run', RUN.replace('his arms, cape and armor plates swing', 'his arms and robe swing')),
   ('shoot', "stops, raises the crossbow to his shoulder, aims straight at the camera and shoots one bolt, then lowers it, pulls the string back with both hands and loads a new bolt."),
   ('die', DIE.replace('drops his weapon', 'drops his crossbow'))]),
 'caoxiao': ("a burly Cao Cao officer with a short full beard in a dark-blue robe under black iron heavy armor with big pauldrons, an iron helmet with a dark-blue plume, a heavy smooth iron club in his right hand and a small round shield on his left arm", [
   ('run', RUN),
   ('ram', "stops, swings the heavy iron club down toward the camera in a big overhead smash, then sweeps it back across once more, shouting."),
   ('die', DIE)]),
 'huainan': ("a thin Yuan Shu foot soldier in an ochre-yellow cloth jacket and leg wraps, a simple bamboo-plate chest guard and an ochre bamboo hat-helmet, gripping a long spear with both hands", [
   ('run', RUN.replace('charges straight toward the camera on foot at a heavy run', 'runs straight toward the camera on foot').replace('his arms, cape and armor plates swing', 'his arms and jacket swing')),
   ('ram', "stops and stabs the long spear forward toward the camera twice in quick jabs, then pulls it back."),
   ('die', DIE.replace('drops his weapon', 'drops his spear'))]),
 'yuanlishi': ("a huge bald Yuan Shu strongman with a short stubble beard, bare muscular arms, golden plate pauldrons and a wide golden belt, baggy ochre trousers, a long thick iron staff on his shoulder", [
   ('run', RUN.replace('his arms, cape and armor plates swing', 'his arms and the iron staff swing')),
   ('ram', "stops, lifts the iron staff over his head with both hands and slams it down toward the camera, then sweeps it sideways once."),
   ('die', DIE.replace('drops his weapon', 'drops his iron staff'))]),
 'hubao': ("an elite Cao Cao heavy cavalryman (Tiger and Leopard Cavalry) in black plate armor, a black cape and a black iron helmet with a black plume, riding a tall black warhorse with black barding on its head and chest, holding a long spear pointed forward", [
   ('run', GALLOP),
   ('ram', "reins in the horse, which rears up on its hind legs; the rider stabs the long spear down and forward toward the camera twice, then the horse comes back down."),
   ('die', FALL)]),
 'xiahoudun': ("the Cao Cao general Xiahou Dun in dark-blue plate armor and a dark-blue cape, holding a long spear", [
   ('idle', IDLE),
   ('heavy', "pulls the long spear back and drives it straight toward the camera in one huge thrust with his whole body, then snaps it back to his stance."),
   ('combo', "flicks the spear upward toward the camera twice in fast rising thrusts, then sweeps it sideways in a wide arc and returns to his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'dianwei': ("the giant Cao Cao bodyguard Dian Wei, a dark-skinned, hugely muscular man, bare-armed in iron-grey leather armor, holding a short-handled iron halberd in each hand", [
   ('idle', IDLE),
   ('heavy', "raises both iron halberds high over his head and smashes them down together toward the camera in one huge blow, then heaves them back up."),
   ('combo', "strikes toward the camera left and right alternately with the two halberds, four fast heavy blows, then returns to his stance."),
   ('seal', "draws back his right arm and hurls one short halberd straight toward the camera, then pulls a spare halberd from behind his back and takes his stance again."),
   ('die', DIE.replace('drops his weapon', 'drops both halberds'))]),
 'jiling': ("the Yuan Shu general Ji Ling in golden plate armor, holding a long three-pointed double-edged glaive", [
   ('idle', IDLE),
   ('heavy', "lifts the three-pointed glaive high over his head and chops it down toward the camera in one heavy blow, then raises it again."),
   ('combo', "sweeps the three-pointed glaive in a wide horizontal arc from right to left across the front of the camera, then back from left to right, and returns to his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'zhangliao': ("Lü Bu's general Zhang Liao in deep-purple plate armor and a deep-purple cape with a long beard, holding a long-handled broad glaive (a long pole with one wide curved steel blade at the top)", [
   ('idle', IDLE),
   ('heavy', "raises the long-handled glaive high and cleaves it diagonally down toward the camera in one powerful stroke, then returns to his stance."),
   ('combo', "slashes toward the camera twice in quick succession, a rising cut then a falling cut, and steps back into his stance."),
   ('die', DIE)]),
 'xunzheng': ("the Yuan Shu general Xun Zheng, an arrogant square-faced man with a short beard in golden plate armor with an ochre robe and cape and a golden helmet, gripping a long spear", [
   ('idle', IDLE),
   ('heavy', "pulls the long spear back and drives it straight toward the camera in one hard thrust, then snaps it back to his stance."),
   ('die', DIE)]),
}
if ONLY: SHOTS = {k: v for k, v in SHOTS.items() if k in ONLY}
shots = []
for k, (who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
tmp = out / 'gray'; tmp.mkdir(exist_ok=True)
with tarfile.open(out / 'foe_pack6.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in SHOTS:
        f = ROOT / '美术' / '第二章' / '敌人正面' / f'{k}.png'; f = f if f.exists() else ROOT / '美术' / '第二章' / '立绘' / f'pt_{k}.png'
        im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        p = tmp / f'{k}.png'; bg.convert('RGB').save(p)
        data = ref(p); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe6.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack6.tar.gz', (out / 'foe_pack6.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
