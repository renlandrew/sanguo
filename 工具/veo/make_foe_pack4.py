"""邓茂、黄巾旗手、张宝、督邮首录（10-29）。用户：「10 美元」。原来邓茂借程远志的 3D 模型染红，旗手借黄巾兵、张宝借术士、督邮借衙役。
首帧：美术/<名>/正面.png（Codex 重画的透明版，邓茂是灰底），透明的先铺到纯中灰 #808080 再补 9:16，镜头、反向提示词照 make_foe_pack2.py。
只录切图用得到的段：邓茂斗将 4 段（待机、挺枪突刺、叫人围攻、倒下），旗手、张宝、督邮各 3 段（朝镜头走／跑、出手、倒下）；共 13 条 × 4 秒 × .15 ≈ 7.8 美元。
在 Cloud Shell 里：SHOTS=shots_foe4.json SECONDS=4 CAP_USD=10 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_foe_pack4.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
src = (HERE / 'make_foe_pack2.py').read_text(encoding='utf-8').split('\nSHOTS = {')[0]
g = {'__file__': str(HERE / 'make_foe_pack2.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src, g)
ref, BASE, TAIL, NEG, IDLE, SUMMON, DIE = (g[k] for k in ('ref', 'BASE', 'TAIL', 'NEG', 'IDLE', 'SUMMON', 'DIE'))
WALK = ("walks steadily straight toward the camera; the camera dollies backward at exactly the same speed, so he stays at the same size "
        "and in the same place in the frame, walking in place; his robes and sleeves sway with each step. Continuous looping walk.")
RUN = g['RUN']
SHOTS = {
 'dengmao': ('邓茂', "the Yellow Turban lieutenant Deng Mao, a burly square-faced man with a short hard beard and a yellow headband with a bronze plate, in heavy ochre-and-dark-brown armor made of a few large smooth plates over a dark-red robe, holding a long spear with a red tassel", [
   ('idle', IDLE),
   ('heavy', "draws the spear back, then lunges and thrusts it hard straight toward the camera twice, and returns to his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'qishou': ('巾旗手', "a young Yellow Turban flag bearer in a plain yellow tunic, grey trousers and straw sandals, a yellow headband, both hands gripping the tall pole of a huge yellow banner with the character 黄", [
   ('run', RUN.replace('his arms, cape and armor plates swing', 'the huge banner flaps and his tunic swings')),
   ('ram', "stops, plants his feet and swings the tall banner pole down and forward toward the camera like a spear, shouting, then raises the banner high again."),
   ('die', DIE.replace('drops his weapon', 'lets go of the banner'))]),
 'zhangbao': ('张宝', "the Yellow Turban sorcerer-general Zhang Bao, a gaunt middle-aged man with a long thin beard, a yellow headband and small Taoist cap, in layered yellow-and-brown Taoist robes with a red sash, a peachwood sword in one hand and a yellow paper talisman in the other", [
   ('run', WALK),
   ('cast', "stops, raises the peachwood sword high and thrusts the paper talisman toward the camera while chanting, sleeves billowing, then lowers his arms."),
   ('die', DIE.replace('drops his weapon', 'drops his sword and talisman'))]),
 'duyou': ('督邮', "a fat, smug Han dynasty inspector official with a round face and small moustache, a black official's cap, a long purple court robe with gold trim and a wide belt, holding a red-and-black official's staff", [
   ('run', WALK),
   ('ram', "stops, lifts the red-and-black staff and swings it down hard toward the camera, then jabs it forward once more, sneering."),
   ('die', "is struck by a heavy blow, stumbles back in shock, drops his staff and falls on his backside, then rolls over and lies on the floor groaning.")]),
}
shots = []
for k, (_, who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
tmp = out / 'gray'; tmp.mkdir(exist_ok=True)
with tarfile.open(out / 'foe_pack4.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k, (nm, _, _) in SHOTS.items():
        im = Image.open(ROOT / '美术' / nm / '正面.png').convert('RGBA'); bg = Image.new('RGBA', im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        p = tmp / f'{k}.png'; bg.convert('RGB').save(p)                                   # 透明的铺灰底（ref 读 RGB，透明处会变黑）
        data = ref(p); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe4.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack4.tar.gz', (out / 'foe_pack4.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
