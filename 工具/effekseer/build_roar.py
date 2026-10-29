# 用用户原来的声浪画稿制作 Effekseer 正面前冲；不改画稿轮廓，沿 Y 轴飞行并淡出。
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parent
source=Path("/Volumes/andrew's SSD/Mistport-worktrees/hero-v4-device/output/shield-effekseer-ref-20261006/packs/MAGICALxSPIRAL/MAGICALxSPIRAL/foot_smoke6.efkproj")
tree=ET.parse(source); n=tree.getroot().find('./Root/Children/Node')
def setv(path,value):
 e=n.find(path)
 if e is None: raise RuntimeError('缺少节点 '+path)
 e.text=str(value)
def rng(path,value):
 for name in ('Center','Max','Min'):setv(path+'/'+name,value)
setv('Name','当阳一喝_原画前冲');setv('CommonValues/MaxGeneration/Value',1);rng('CommonValues/Life',48)
setv('CommonValues/GenerationTime',1);setv('CommonValues/GenerationTimeOffset',0)
setv('LocationValues/Type',1)
for key in ('Location','Velocity','Acceleration'):
 for axis in 'XYZ':rng('LocationValues/PVA/'+key+'/'+axis, .035 if key=='Velocity' and axis=='Y' else 0)
setv('RotationValues/Type',0);setv('ScalingValues/Type',0)
for axis in 'XYZ':setv('ScalingValues/Fixed/Scale/'+axis, .612 if axis=='X' else 1)
setv('RendererCommonValues/ColorTexture','Texture/shout.png');setv('RendererCommonValues/AlphaBlend',1);setv('RendererCommonValues/UV',0)
setv('RendererCommonValues/FadeIn/Frame',4);setv('RendererCommonValues/FadeOut/Frame',12)
setv('DrawingValues/Sprite/Billboard',0);setv('DrawingValues/Sprite/ColorAll',0)
# 原画前后错时叠加金红色的亮部：四次短促闪耀贴着原声浪前行。
# 原画仍是主体，亮层按同样速度跟随，不增加完整几何环。
from copy import deepcopy
base = n
children = tree.getroot().find('./Root/Children')
for phase in (2, 13, 24, 35):
 n = deepcopy(base); children.append(n)
 setv('Name','声浪_金光闪烁_'+str(phase)); setv('CommonValues/GenerationTimeOffset',phase); rng('CommonValues/Life',13)
 rng('LocationValues/PVA/Location/Y', .035 * phase)
 setv('RendererCommonValues/AlphaBlend',2);setv('RendererCommonValues/FadeIn/Frame',3);setv('RendererCommonValues/FadeOut/Frame',7)
 for k,v in [('R',255),('G',195),('B',85),('A',205)]:setv('DrawingValues/Sprite/ColorAll_Fixed/'+k,v)
# 四处错时闪点，单次只在原画边缘闪现，不形成密集粒子。
for i,(phase,x,y) in enumerate(((5,-.18,.30),(15,.18,.35),(25,-.15,.20),(35,.16,.27))):
 n=deepcopy(base);children.append(n);setv('Name','声浪_金色闪点_'+str(i));setv('CommonValues/GenerationTimeOffset',phase);rng('CommonValues/Life',9)
 rng('LocationValues/PVA/Location/X',x);rng('LocationValues/PVA/Location/Y',y+.035*phase)
 setv('RendererCommonValues/ColorTexture','Texture/star.png');setv('RendererCommonValues/AlphaBlend',2)
 setv('RendererCommonValues/FadeIn/Frame',2);setv('RendererCommonValues/FadeOut/Frame',6)
 for axis in 'XYZ':setv('ScalingValues/Fixed/Scale/'+axis,.22)
 for k,v in [('R',255),('G',220),('B',135),('A',220)]:setv('DrawingValues/Sprite/ColorAll_Fixed/'+k,v)
out=root/'_cand/roar';out.mkdir(parents=True,exist_ok=True)
import shutil
shutil.copy2(root/'_cand/t1/Texture/star.png',out/'Texture/star.png')
proj=out/'shout.efkproj';tree.write(proj,encoding='utf-8',xml_declaration=True)
# 旧版编辑器在包含中文或单引号的绝对路径下会写坏贴图 URI；在 ASCII 临时目录编译。
import tempfile,shutil
tmp=Path(tempfile.mkdtemp(prefix='sanguo-efk-'));(tmp/'Texture').mkdir();shutil.copy2(out/'Texture/shout.png',tmp/'Texture/shout.png');shutil.copy2(out/'Texture/star.png',tmp/'Texture/star.png');shutil.copy2(proj,tmp/'shout.efkproj')
exe="/Volumes/andrew's SSD/tools-downloads/effekseer170e/Effekseer.app/Contents/Resources/Effekseer"
r=subprocess.run([exe,'-cui','-in','shout.efkproj','-e','shout.efk'],cwd=tmp,capture_output=True,text=True)
if (tmp/'shout.efk').exists():shutil.copy2(tmp/'shout.efk',out/'shout.efk')
shutil.rmtree(tmp)
if r.returncode or not (out/'shout.efk').exists(): raise RuntimeError('Effekseer 编译失败：'+r.stderr[-1000:])
print('Effekseer 声浪已编译',out/'shout.efk')
