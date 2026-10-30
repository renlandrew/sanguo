"""华雄、李傕、胡轸大甲片版重录（10-29）。用户：「要不要这三个盔甲简化大块一些？」「写」「10 美元」。
首帧：美术/<名>/正面.png（Codex 画的大甲片新立绘，中灰底 2:3），补 9:16 的办法、镜头和反向提示词全照 make_foe_pack2.py。
只录切图用得到的段（cut_generals.py 的 PLAN）：胡轸待机取连斩收势那几帧，所以不录 idle；共 12 条 × 4 秒 × .15 ≈ 7.2 美元。
输出 <输出目录>/foe_pack3.tar.gz = ref_<键>.jpg + shots_foe3.json + veo_wendao.py，在 Cloud Shell 里：
  SHOTS=shots_foe3.json SECONDS=4 CAP_USD=10 python3 veo_wendao.py
用法：<media-venv>/bin/python 三国志/工具/veo/make_foe_pack3.py <输出目录>
"""
import io, json, sys, tarfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
src = (HERE / 'make_foe_pack2.py').read_text(encoding='utf-8').split('\nSHOTS = {')[0]
g = {'__file__': str(HERE / 'make_foe_pack2.py'), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src, g)
ref, BASE, TAIL, NEG, IDLE, SUMMON, DIE = (g[k] for k in ('ref', 'BASE', 'TAIL', 'NEG', 'IDLE', 'SUMMON', 'DIE'))
PLATES = "His armor is made of a few large smooth plates (big shoulder plates, one solid breastplate, large thigh plates) with simple highlights, no scales and no small pieces"
SHOTS = {
 'huzhen': ('胡轸', "the Dong Zhuo general Hu Zhen, a sturdy round-faced man with thick brows and a short beard, in bright polished steel armor trimmed with earthy gold, a round steel helmet with a short golden plume, an ochre robe and a big ochre-gold scarf over his shoulder, a straight sabre in each hand. " + PLATES, [
   ('combo', "lunges toward the camera and slashes with both sabres in a fast cross-cut, left then right, then a final double downward chop, and steps back into his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'huaxiong': ('华雄', "the Dong Zhuo general Hua Xiong, a huge black-bearded warrior in black-iron armor trimmed with dark red, a round black-iron helmet with a red tassel, a dark-red robe and a huge dark-red cape, both hands resting on the hilt of a broad heavy sabre planted point-down in front of him. " + PLATES, [
   ('idle', IDLE),
   ('taunt', "points the heavy sabre up at the camera as if at the city wall above, throws his head back and bellows insults, beats his chest with his fist and laughs scornfully."),
   ('heavy', "lifts the broad heavy sabre high over his head with both hands and brings it crashing down toward the camera in one huge chop, then heaves it back up to his shoulder."),
   ('summon', SUMMON),
   ('die', DIE)]),
 'lijue': ('李傕', "the Dong Zhuo general Li Jue, a lean long-faced man with narrow eyes, a thin moustache and a sly grin, in bronze armor trimmed with deep purple, a pointed bronze helmet with a long deep-purple plume, a deep-purple robe and short cape, holding a broad-backed sabre across his body. " + PLATES, [
   ('idle', IDLE),
   ('heavy', "swings his broad sabre in one wide horizontal sweep from right to left across the front of the camera, then back to his stance."),
   ('summon', SUMMON),
   ('die', DIE)]),
}
shots = []
for k, (_, who, acts) in SHOTS.items():
    for i, (act, motion) in enumerate(acts):
        shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': BASE + 'He is ' + who + '. He ' + motion + TAIL, 'neg': NEG})
with tarfile.open(out / 'foe_pack3.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k, (nm, _, _) in SHOTS.items():
        data = ref(ROOT / '美术' / nm / '正面.png'); add(f'ref_{k}.jpg', data); (out / f'ref_{k}.jpg').write_bytes(data)
    add('shots_foe3.json', json.dumps(shots, ensure_ascii=False, indent=1).encode())
    add('veo_wendao.py', VEO.read_bytes())
print('包', out / 'foe_pack3.tar.gz', (out / 'foe_pack3.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
