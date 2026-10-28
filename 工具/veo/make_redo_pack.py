"""吕布和刘关张换新画风后重录 Veo 动作（10-27，用户：「用 Veo 重录吕布和刘关张的动作，上限 8 美元」）。
首帧：美术/重画/codex/back_<键>.png（Codex 画的新背影动作图）和 lvbu_battle.png（新吕布，灰底无阴影）；补 9:16 的办法照 make_pack / make_foe_pack2。
刘关张每人三条（待机、普攻、招式，背对镜头），吕布四条（待机、方天画戟重击、冲阵、倒下，面向镜头），共 13 条，每条 4 秒按 .15 美元/秒记约 7.8 美元。
输出 <输出目录>/redo_pack.tar.gz，Cloud Shell 里：SHOTS=shots_redo.json SECONDS=4 CAP_USD=8 python3 veo_wendao.py
"""
import io, json, sys, tarfile, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; VEO = ROOT.parent / '修仙' / '工具' / '问道' / 'veo_wendao.py'
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
def load(name):
    src = (HERE / name).read_text(encoding='utf-8'); src = src.split('\nBASE = ')[0]   # 只要 ref 函数，不跑原脚本
    g = {'__file__': str(HERE / name), 'sys': type('S', (), {'argv': ['', str(out)]})}; exec(src.replace("out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)", ""), g); return g
HREF = load('make_pack.py')['ref']; FREF = load('make_foe_pack2.py')['ref']
HB = ("Locked-off static camera behind and slightly above a Chinese Three Kingdoms general on a plain, perfectly uniform mid-gray studio background. "
      "He always keeps his back to the camera and his face is never visible. Exaggerated, dynamic, powerful wuxia action choreography: legs, feet, hips and torso all move clearly, "
      "with deep stances, big steps and strong weight shifts. He stays inside the frame and ends back on his starting spot. Even when he twists his torso or swings his weapon, his back stays toward the camera. "
      "Keep the bright painted illustration look of the first frame, the same costume and the same weapon; the weapon stays rigid steel. ")
HT = " Fast, snappy, forceful timing. The background stays a flat uniform mid-gray the whole time, no ground, no shadow, no smoke."
HN = ("black background, gradient background, dark background, vignette, scenery, ground, floor, shadow, face, turning around, facing the camera, profile view, "
      "extra weapon, extra people, glow, particles, smoke, fire, dust, light beams, leaving the frame, camera movement, zoom, pan, text, watermark, "
      "standing still, stiff pose, slow motion, snake, serpent creature, bending spear, rubbery weapon, morphing weapon")
HEROES = {
 'guan': ('Guan Yu, with long black hair and a green headscarf, in a long flowing plain green robe with a brown leather belt, holding a long-shafted glaive with one smooth crescent steel blade', [
   ('idle', "sinks into a deep horse stance and rocks his weight from leg to leg, the long crescent glaive swinging in a slow figure-eight beside him; his green robe and headscarf tails whip in the wind."),
   ('atk', "coils his body, twisting far to the right into a crouch, then lunges forward with a big step and sweeps the crescent glaive in a huge horizontal arc away from the camera, then springs back to his stance."),
   ('skill', "takes two running steps, leaps high lifting the glaive over his head with both hands, then crashes down chopping the crescent glaive straight down in a giant overhead strike in front of him, robe billowing; he rises back up.")]),
 'zhang': ('Zhang Fei, a burly general with curly black hair and a red headband, in red cloth over black armor with a few large smooth plates, holding a long rigid steel spear with a wavy steel blade (a weapon, never a snake)', [
   ('idle', "bounces on the balls of his feet in a wide brawler's stance, stamping his right foot, rolling his huge shoulders and swinging the steel spear from side to side; his red cloth flaps wildly."),
   ('atk', "drops into a low front lunge with a big step forward and drives the rigid steel spear straight out away from the camera with his whole body behind it, twice in quick succession, then hops back to his guard."),
   ('skill', "jumps and stamps both feet down hard, slams the spear butt down, throws both arms wide, arches his back and roars forward away from the camera with his whole body shaking; his red cloth is blasted straight back.")]),
 'liu': ('Liu Bei, with a topknot and blue ribbons, in a long white robe with blue trim and a blue sash, holding a straight double-edged sword in each hand', [
   ('idle', "shifts lightly from foot to foot in a nimble swordsman's stance, knees bent, both straight swords circling at his wrists; his white-and-blue robe and ribbons ripple."),
   ('atk', "springs forward with a quick skipping step and slashes both swords upward and forward in a fast crossing X, torso twisting, back foot kicking up, then skips back to his stance."),
   ('skill', "twists hard left then right, sweeping both swords in two huge circles around his body like a whirlwind without turning to face the camera, the white robe flaring, then bounds forward and thrusts both swords far forward.")]),
}
FB = ("Locked-off static camera in front of and slightly above a character on a plain, perfectly uniform mid-gray studio background. "
      "He faces the camera the whole time. Keep the bright painted illustration look of the first frame, the same costume and the same halberd. He is ")
FT = " The background stays a flat uniform mid-gray the whole time, no ground, no shadow, no scenery."
FN = ("black background, gradient background, dark background, vignette, scenery, ground, floor, shadow, dark outline, dark halo, turning around, back view, extra people, "
      "glow, particles, smoke, fire, lightning, magic effects, leaving the frame, zoom, text, watermark")
LVBU = "the young general Lü Bu with two long red pheasant feathers on a small gold crown, in smooth gold plate armor over a red robe and a big red cape, holding a halberd with a straight spear tip and one smooth crescent blade"
LVA = [('idle', "He stands his ground in a fighting stance, breathing heavily and shifting his weight; his red cape and feathers flutter in a strong wind. Small, looping motion."),
       ('heavy', "He swings the halberd in a huge horizontal sweep across the front of the camera, spins it once over his head and brings it down in a second sweep, then plants it."),
       ('rush', "He charges straight toward the camera on foot at a heavy run; the camera dollies backward at exactly the same speed, so he stays at the same size and in the same place in the frame, running in place; his cape and feathers stream behind him. Continuous looping run."),
       ('die', "He is struck by a heavy blow, staggers back, drops his halberd, sinks to his knees and slowly collapses to the floor.")]
shots = []
for k, (who, acts) in HEROES.items():
    for i, (act, m) in enumerate(acts): shots.append({'id': f'{k}{i}_{act}', 'ref': k, 'prompt': HB + who + ', ' + m + HT, 'neg': HN})
for i, (act, m) in enumerate(LVA): shots.append({'id': f'lvbu{i}_{act}', 'ref': 'lvbu', 'prompt': FB + LVBU + '. ' + m + FT, 'neg': FN})
C = ROOT / '美术' / '重画' / 'codex'
with tarfile.open(out / 'redo_pack.tar.gz', 'w:gz') as tar:
    def add(name, data):
        ti = tarfile.TarInfo(name); ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
    for k in HEROES: d = HREF(C / f'back_{k}.png'); add(f'ref_{k}.jpg', d); (out / f'ref_{k}.jpg').write_bytes(d)
    d = FREF(C / 'lvbu_battle.png'); add('ref_lvbu.jpg', d); (out / 'ref_lvbu.jpg').write_bytes(d)
    add('shots_redo.json', json.dumps(shots, ensure_ascii=False, indent=1).encode()); add('veo_wendao.py', VEO.read_bytes())
print('包', (out / 'redo_pack.tar.gz').stat().st_size // 1024, 'KB，', len(shots), '条，约', round(len(shots) * 4 * .15, 1), '美元')
