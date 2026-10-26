# 配乐 WAV → 80kbps mp3（Cloud Shell 上跑，ffmpeg 用 imageio_ffmpeg 自带的），顺手传到桶里 music/，再用 recv.py 取回本机 劫云问道/art/music/
F=$(python3 -c "import imageio_ffmpeg as i;print(i.get_ffmpeg_exe())")
mkdir -p mp3
for w in out/*.wav; do n=$(basename $w .wav); [ -f mp3/$n.mp3 ] && continue
  $F -v error -y -i $w -af "silenceremove=start_periods=1:start_threshold=-55dB,areverse,silenceremove=start_periods=1:start_threshold=-55dB,areverse" -ar 44100 -ac 2 -b:a 80k mp3/$n.mp3
  gsutil -q cp mp3/$n.mp3 gs://hero-takes-2000f509/sanguo_music/$n.mp3
done
ls -la mp3; for m in mp3/*.mp3; do $F -i $m 2>&1 | grep -o 'Duration: [0-9:.]*' | tr '\n' ' '; echo $m; done
