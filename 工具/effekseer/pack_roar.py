# 把 Effekseer WebGL 输出的透明逐帧图打成同一外框图集，不重新染色或裁掉原画。
import json,sys
from pathlib import Path
from PIL import Image
src=Path(sys.argv[1]);out=Path(__file__).resolve().parents[2]/'原型'/'img'
sheet=Image.open(src).convert('RGBA'); size=512; n=24; cols=6
frames=[sheet.crop(((i%cols)*size,(i//cols)*size,(i%cols+1)*size,(i//cols+1)*size)) for i in range(n)]
boxes=[im.getbbox() for im in frames]; live=[b for b in boxes if b]
if not live:raise RuntimeError('Effekseer 没渲染出声浪')
box=(max(0,min(b[0] for b in live)-4),max(0,min(b[1] for b in live)-4),min(size,max(b[2] for b in live)+4),min(size,max(b[3] for b in live)+4))
w,h=box[2]-box[0],box[3]-box[1];atlas=Image.new('RGBA',(w*cols,h*((n+cols-1)//cols)));rects=[];centers=[]
for i,(im,b) in enumerate(zip(frames,boxes)):
 x=(i%cols)*w;y=(i//cols)*h;atlas.paste(im.crop(box),(x,y));rects.append([x,y,w,h]);centers.append(None if not b else [(b[0]+b[2])/2-box[0],(b[1]+b[3])/2-box[1]])
atlas.save(out/'fx_shout_efk.webp',lossless=True,method=6)
(out/'fx_shout_efk.json').write_text(json.dumps({'src':'effekseer','fps':30,'frames':rects,'centers':centers,'width':w,'height':h},separators=(',',':')))
print('声浪',n,'帧',w,h,'图集', (out/'fx_shout_efk.webp').stat().st_size,'字节')
