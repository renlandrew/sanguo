"""11-13 讨伐：每招单独录一条动作（用户：「3个怪物的动作都要好看多变」→「录每招的动作」）。
原来每只只录一条，三招共用。现在按招录；巨灵「举拳砸地」正好是震地、蛟「昂首探头」正好是喷水，这两条留用（各省三条）。
共 21 条 × 4 秒 × .15 = 12.6 美元（limingze091 项目赠金）。首帧用 ~/sanguo_hunt 里已有的 ref_<键><形态>.jpg，不再重传。
Cloud Shell：cd ~/sanguo_hunt && SHOTS=shots_move.json SECONDS=4 LAST=1 CAP_USD=18 PROJECT=$DEVSHELL_PROJECT_ID python3 veo_wendao.py
用法：python3 三国志/工具/veo/make_hunt_move_pack.py <输出目录>
"""
import json, sys
from pathlib import Path
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
BASE = ("Locked-off static camera in front of a giant monster on a plain, perfectly uniform mid-gray studio background. "
        "It faces the camera, stays in the same place and stays fully inside the frame. Keep the detailed painted illustration look of the first frame, the same body, colors and markings. "
        "It holds its starting pose for the first half second, then: ")
TAIL = " Then it returns to exactly the starting pose. The background stays a flat uniform mid-gray the whole time, no ground, no shadow, no scenery."
NEG0 = ("black background, gradient background, dark background, vignette, spotlight, scenery, landscape, ground, floor, shadow, "
        "turning around, back view, extra creatures, people, leaving the frame, walking away, camera movement, zoom, text, subtitles, watermark, logo")
NEG = [NEG0 + ", glow, particles, smoke, mist, fire, lightning, light beams, magic effects", NEG0 + ", smoke, mist, light beams", NEG0 + ", smoke, mist, light beams"]
FX = ['', ' The glowing cracks on its body flicker.', ' The flames and sparks on its body keep burning and flickering.']
WHO = { 'juling': "a towering clay-skinned giant with a yellow turban and a ragged yellow waist cloth tied with a thick rope, bare-chested and hugely muscular",
        'shanjun': "a gigantic tiger, facing the camera",
        'jiao': "a giant hornless river dragon with a long scaled body coiled in big arcs across the frame and its head raised in the middle" }
MOVES = {   # 键 → [(招序号, 动作)]；没列的那一招用原来那条
 'juling': [(1, "it pulls its right fist far back past its hip, twisting its torso, then steps in and drives one huge straight punch forward toward the camera at chest height, the whole body behind it, and pulls the fist back."),
            (2, "it drops into a low crouch, sweeps its right arm forward low along the ground and closes its huge hand into a grabbing claw toward the camera, then drags the closed fist back to its chest and straightens up.")],
 'shanjun': [(0, "it crouches down low with its hindquarters raised and its tail lashing, then springs forward toward the camera low over the ground with both front paws reaching out and claws spread, jaws wide open, and lands back on all fours."),
             (1, "it plants all four paws, draws its head back and its chest swells, then throws its head forward and roars with its jaws wide open, its fur and whiskers blasted backwards, then settles back down."),
             (2, "it rises up on its hind legs and swipes its right front paw across in front of it in a wide horizontal arc with the claws spread, then swipes the left paw back the other way, then drops down onto all fours.")],
 'jiao': [(1, "it darts its head and neck forward and to one side, then throws one big loop of its scaled body forward through the air as if to wrap around something in front of it, and pulls the coil back."),
          (2, "it rears the front of its body high up, then slams both front claws and its chest straight down onto the ground in front of it, then lifts back up.")] }
shots = [{'id': f'{k}{n}_m{mi}', 'ref': f'{k}{n}', 'prompt': BASE + 'It is ' + WHO[k] + '. ' + m + FX[n - 1] + TAIL, 'neg': NEG[n - 1]}
         for k, mv in MOVES.items() for mi, m in mv for n in (1, 2, 3)]
(out / 'shots_move.json').write_text(json.dumps(shots, ensure_ascii=False, indent=1))
(out / 'run2.sh').write_text("""#!/bin/bash
cd ~/sanguo_hunt
env PROJECT=$DEVSHELL_PROJECT_ID SHOTS=shots_move.json SECONDS=4 LAST=1 CAP_USD=18 python3 veo_wendao.py 2>&1 | grep "^VEO"
mkdir -p small2; FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
for f in out/*_m?.mp4; do b=$(basename $f); [ -f small2/$b ] || "$FF" -nostdin -loglevel error -y -i $f -an -vf scale=480:-2 -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p small2/$b; done
cp go2.html small2/; ls small2 | wc -l; du -sh small2; cd small2; (pkill -f "http.server 8094"; true); nohup python3 -m http.server 8094 > ../http2.log 2>&1 &
echo READY https://8094-$WEB_HOST/go2.html
""")
names = [s['id'] for s in shots]
go = (Path(__file__).resolve().parents[2].parent / 'x').parent  # 占位
print('条数', len(shots), '约', round(len(shots) * 4 * .15, 1), '美元'); print(json.dumps(names, ensure_ascii=False))
