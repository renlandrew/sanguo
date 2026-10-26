// 墨流层（10-25）：实时流体模拟，给大招用——墨像真墨在水里翻卷、火从地里炸出来带烟尘。
// 用户发来几张电影截图：「我要这样的」（火从地里炸出来带烟尘碎石、墨一缕缕翻卷夹着水花和飞的黑片、顺着兵器喷出的白色水雾）；
// 看了试样：「不错，边缘羽化应该就好一些」「可以，试下青金色」「你也不能全部都是这样，也要有没有烟气的」——
// 所以只给两个大招用（青龙斩青金墨浪、当阳一喝火爆），普攻和双股剑仍是干净的刀光剑光（帧动画）。
// 做法：稳定流体（平流、旋度加强、压力投影），WebGL2 半精度浮点纹理。
// 染料四个通道：r 墨、g 火（热）、b 烟、a 水花；火往上飘、慢慢变成烟；墨、烟、水花各按自己的速度淡掉。
// 画：输出预乘透明的一层，叠到游戏画布上——墨、烟、水花是盖上去的（边缘羽化：和周围平均一下、淡处很快透明），火是加亮的（颜色超过透明度，预乘叠加时就是加光）。
// 碎石、火星、墨里卷出的飞片、水珠由 drawParts 画在调用方的 2D 画布上（少而大，不要密集）。
// 用法：const ML = Moliu.create({ W: 360, H: 640 }); 每帧 ML.step(dt)、ML.render(像素宽, 像素高)，再 ctx.drawImage(ML.canvas, 0, 0, W, H)、ML.drawParts(ctx)；
//       招式：ML.fx.qinglong(x, y, R, dir)（弯刀光＋青金墨浪）、ML.fx.roar(x, y)、ML.fx.fireWhip(x, y)、ML.fx.jet(x0, y0, x1, y1)、ML.fx.inkDragon(x, y)。
(function () {
'use strict';
const PALETTE = {                                                   // 墨的颜色：淡处、浓处、墨里的亮边（10-25 用户：「试下青金色」——石青打底、泥金勾边）
  qingjin: { thin: [.24, .47, .56], dense: [.03, .16, .24], sheen: [.96, .78, .36], sheenAmt: .55 },
  ink:     { thin: [.30, .34, .36], dense: [.035, .035, .045], sheen: [.9, .95, 1], sheenAmt: .22 },
};
function create(opt = {}) {
  const W = opt.W || 360, H = opt.H || 640;
  const c = document.createElement('canvas'); c.width = opt.pw || W; c.height = opt.ph || H;
  const gl = c.getContext('webgl2', { alpha: true, premultipliedAlpha: true, preserveDrawingBuffer: true, antialias: false });
  if (!gl) return null;
  if (!gl.getExtension('EXT_color_buffer_float') && !gl.getExtension('EXT_color_buffer_half_float')) return null;
  const SIM = { w: 180, h: 320 }, DYE = { w: 360, h: 640 };                                     // 模拟格子细一点，墨丝才细
  const CFG = { curl: 46, pressureIters: 22, velDecay: .8, buoy: 3, burn: 2.2, decay: [.4, 3.6, .85, 2.2], palette: 'qingjin' };   // 烟散得快一点，不长时间挡着战场   // 每秒衰减：墨、火、烟、水花
  const VS = `#version 300 es
in vec2 aPos; uniform vec2 uTexel; out vec2 vUv, vL, vR, vT, vB;
void main(){ vUv = aPos * .5 + .5; vL = vUv - vec2(uTexel.x, 0.); vR = vUv + vec2(uTexel.x, 0.); vT = vUv + vec2(0., uTexel.y); vB = vUv - vec2(0., uTexel.y); gl_Position = vec4(aPos, 0., 1.); }`;
  const FS = {
    splat: `uniform sampler2D uTarget; uniform float uAspect, uRadius; uniform vec2 uPoint; uniform vec4 uColor;
      void main(){ vec2 p = vUv - uPoint; p.x *= uAspect; vec4 s = exp(-dot(p, p) / uRadius) * uColor; o = texture(uTarget, vUv) + s; }`,
    advect: `uniform sampler2D uVel, uSrc; uniform vec2 uSimTexel; uniform float uDt; uniform vec4 uDecay; uniform float uBurn;
      void main(){ vec2 c = vUv - uDt * texture(uVel, vUv).xy * uSimTexel; vec4 r = texture(uSrc, c); vec4 k = exp(-uDecay * uDt); r.b += r.g * uBurn * uDt; o = r * k; }`,
    curl: `uniform sampler2D uVel;
      void main(){ float L = texture(uVel, vL).y, R = texture(uVel, vR).y, T = texture(uVel, vT).x, B = texture(uVel, vB).x; o = vec4(.5 * (R - L - T + B), 0., 0., 1.); }`,
    vort: `uniform sampler2D uVel, uCurl, uDye; uniform float uCurlK, uDt, uBuoy;
      void main(){ float L = texture(uCurl, vL).x, R = texture(uCurl, vR).x, T = texture(uCurl, vT).x, B = texture(uCurl, vB).x, C = texture(uCurl, vUv).x;
        vec2 f = .5 * vec2(abs(T) - abs(B), abs(R) - abs(L)); f /= length(f) + 1e-4; f *= uCurlK * C; f.y *= -1.;
        vec2 v = texture(uVel, vUv).xy + f * uDt; v.y += texture(uDye, vUv).g * uBuoy * 60. * uDt; o = vec4(clamp(v, -1200., 1200.), 0., 1.); }`,
    div: `uniform sampler2D uVel;
      void main(){ float L = texture(uVel, vL).x, R = texture(uVel, vR).x, T = texture(uVel, vT).y, B = texture(uVel, vB).y; vec2 C = texture(uVel, vUv).xy;
        if (vL.x < 0.) L = -C.x; if (vR.x > 1.) R = -C.x; if (vT.y > 1.) T = -C.y; if (vB.y < 0.) B = -C.y; o = vec4(.5 * (R - L + T - B), 0., 0., 1.); }`,
    press: `uniform sampler2D uP, uDiv;
      void main(){ float L = texture(uP, vL).x, R = texture(uP, vR).x, T = texture(uP, vT).x, B = texture(uP, vB).x, d = texture(uDiv, vUv).x; o = vec4((L + R + B + T - d) * .25, 0., 0., 1.); }`,
    grad: `uniform sampler2D uP, uVel;
      void main(){ float L = texture(uP, vL).x, R = texture(uP, vR).x, T = texture(uP, vT).x, B = texture(uP, vB).x; vec2 v = texture(uVel, vUv).xy - vec2(R - L, T - B); o = vec4(v, 0., 1.); }`,
    scale: `uniform sampler2D uSrc; uniform float uK; void main(){ o = uK * texture(uSrc, vUv); }`,
    show: `uniform sampler2D uDye; uniform vec2 uDyeTexel; uniform vec3 uThin, uDense, uSheen; uniform float uSheenAmt;
      vec3 fireRamp(float h){ return vec3(.95, .32, .06) * smoothstep(.03, .45, h) + vec3(.45, .36, .12) * smoothstep(.4, 1.1, h) + vec3(.22) * smoothstep(1.1, 2.2, h); }
      void main(){
        vec4 d0 = max(texture(uDye, vUv), 0.); vec2 e2 = uDyeTexel * 2.5;
        vec4 avg = (max(texture(uDye, vUv + vec2(e2.x, 0.)), 0.) + max(texture(uDye, vUv - vec2(e2.x, 0.)), 0.) + max(texture(uDye, vUv + vec2(0., e2.y)), 0.) + max(texture(uDye, vUv - vec2(0., e2.y)), 0.)) * .25;
        vec4 d = mix(d0, avg, .5);                                                          // 边缘羽化：和周围平均一下
        float dl = texture(uDye, vUv - vec2(uDyeTexel.x, 0.)).r, dr = texture(uDye, vUv + vec2(uDyeTexel.x, 0.)).r, db = texture(uDye, vUv - vec2(0., uDyeTexel.y)).r, dt = texture(uDye, vUv + vec2(0., uDyeTexel.y)).r;
        float edge = clamp(length(vec2(dr - dl, dt - db)) * 2.2, 0., 1.);
        float ink = pow(1. - exp(-d.r * 1.35), 1.7) * .96;                                  // 淡处很快透明，边是虚的
        vec3 C = mix(uThin, uDense, clamp(d.r * .55, 0., 1.)) * ink; float A = ink;
        C += uSheen * edge * smoothstep(.35, .9, ink) * uSheenAmt * A;                       // 墨里面的亮边（青金是泥金色），不在外沿描一圈
        vec3 fire = fireRamp(d.g);
        float sm = pow(1. - exp(-d.b * 1.3), 1.4) * .9; vec3 smokeCol = mix(vec3(.80, .74, .64), vec3(.24, .21, .19), clamp(d.b * .55, 0., 1.)) + fire * .3;
        C = smokeCol * sm + C * (1. - sm); A = sm + A * (1. - sm);
        float wa = pow(1. - exp(-d.a * 1.6), 1.3) * .85; C = vec3(.96, .98, 1.) * wa + C * (1. - wa); A = wa + A * (1. - wa);
        float fa = pow(smoothstep(.02, .9, d.g), 1.5) * .72; vec3 fc = mix(vec3(.78, .2, .04), vec3(1., .62, .18), smoothstep(.5, 1.4, d.g));   // 火先盖一层橙红实色（浅色地面上纯加光会冲成淡黄）
        C = fc * fa + C * (1. - fa); A = fa + A * (1. - fa);
        o = vec4(C + fire * .55, A); }`,                                                       // 再加一层光：颜色超过透明度，预乘叠上去就是加光
  };
  const compile = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
  let P;
  try {
    const vs = compile(gl.VERTEX_SHADER, VS); P = {};
    for (const k in FS) { const p = gl.createProgram(); gl.attachShader(p, vs); gl.attachShader(p, compile(gl.FRAGMENT_SHADER, `#version 300 es\nprecision highp float; precision highp sampler2D; in vec2 vUv, vL, vR, vT, vB; out vec4 o;\n${FS[k]}`)); gl.bindAttribLocation(p, 0, 'aPos'); gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
      const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS); for (let i = 0; i < n; i++) { const a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); } P[k] = { p, u }; }
  } catch (e) { console.error('墨流层着色器', e); return null; }
  const quad = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, quad); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  function tex(w, h) { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, w, h, 0, gl.RGBA, gl.HALF_FLOAT, null); const f = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, f); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
    gl.viewport(0, 0, w, h); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); return { t, f, w, h }; }
  const dbl = (w, h) => { const a = tex(w, h), b = tex(w, h); return { r: a, w: b, swap() { const x = this.r; this.r = this.w; this.w = x; } }; };
  const vel = dbl(SIM.w, SIM.h), dye = dbl(DYE.w, DYE.h), prs = dbl(SIM.w, SIM.h), dvg = tex(SIM.w, SIM.h), crl = tex(SIM.w, SIM.h);
  if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) return null;
  function run(prog, target, uni, texel) {
    const { p, u } = P[prog]; gl.useProgram(p); let unit = 0;
    for (const k in uni) { const v = uni[k]; if (!u[k]) continue; if (v && v.t) { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, v.t); gl.uniform1i(u[k], unit++); } else if (typeof v === 'number') gl.uniform1f(u[k], v); else if (v.length === 2) gl.uniform2fv(u[k], v); else if (v.length === 3) gl.uniform3fv(u[k], v); else gl.uniform4fv(u[k], v); }
    const tw = target ? target.w : c.width, th = target ? target.h : c.height; gl.uniform2fv(u.uTexel, texel || [1 / tw, 1 / th]);
    gl.bindFramebuffer(gl.FRAMEBUFFER, target ? target.f : null); gl.viewport(0, 0, tw, th); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  // 往流体里点一笔：屏幕坐标、速度（屏幕像素/秒）、半径（屏幕像素）、染料 [墨, 火, 烟, 水花]
  let t = 0, lastSplat = -99; const pending = [], parts = [];
  function splat(x, y, vx, vy, r, d) {
    const pt = [x / W, 1 - y / H], aspect = W / H, rad = Math.pow(r / H, 2); lastSplat = t;
    run('splat', vel.w, { uTarget: vel.r, uAspect: aspect, uPoint: pt, uRadius: rad, uColor: [vx * SIM.w / W, -vy * SIM.h / H, 0, 0] }); vel.swap();
    if (d) { run('splat', dye.w, { uTarget: dye.r, uAspect: aspect, uPoint: pt, uRadius: rad, uColor: d }); dye.swap(); }
  }
  const at = (delay, fn) => pending.push({ t: t + delay, fn });
  const idle = () => t - lastSplat > 8 && !pending.length;                                     // 8 秒没新东西（墨也淡完了）就不算、不画了（省电）
  function step(dt) {
    t += dt; for (let i = pending.length - 1; i >= 0; i--) if (pending[i].t <= t) { const p = pending.splice(i, 1)[0]; p.fn(); }
    for (const p of parts) { p.t += dt; if (p.drag) { const k = Math.exp(-p.drag * dt); p.vx *= k; p.vy *= k; } p.vy += p.g * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.spin * dt; if (p.ground && p.y > p.ground) { p.y = p.ground; p.vy *= -.25; p.vx *= .6; p.spin *= .5; } }
    for (let i = parts.length - 1; i >= 0; i--) if (parts[i].t > parts[i].life) parts.splice(i, 1);
    if (idle()) return;
    const st = [1 / SIM.w, 1 / SIM.h];
    run('curl', crl, { uVel: vel.r }, st);
    run('vort', vel.w, { uVel: vel.r, uCurl: crl, uDye: dye.r, uCurlK: CFG.curl, uDt: dt, uBuoy: CFG.buoy }, st); vel.swap();
    run('div', dvg, { uVel: vel.r }, st);
    run('scale', prs.w, { uSrc: prs.r, uK: .8 }, st); prs.swap();
    for (let i = 0; i < CFG.pressureIters; i++) { run('press', prs.w, { uP: prs.r, uDiv: dvg }, st); prs.swap(); }
    run('grad', vel.w, { uP: prs.r, uVel: vel.r }, st); vel.swap();
    run('advect', vel.w, { uVel: vel.r, uSrc: vel.r, uSimTexel: st, uDt: dt, uDecay: [CFG.velDecay, CFG.velDecay, 0, 0], uBurn: 0 }, st); vel.swap();
    run('advect', dye.w, { uVel: vel.r, uSrc: dye.r, uSimTexel: st, uDt: dt, uDecay: CFG.decay, uBurn: CFG.burn }, [1 / DYE.w, 1 / DYE.h]); dye.swap();
  }
  function render(pw, ph) {
    if (pw && (c.width !== pw || c.height !== ph)) { c.width = pw; c.height = ph; }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, c.width, c.height); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    if (idle()) return false;
    const pal = PALETTE[CFG.palette] || PALETTE.ink;
    run('show', null, { uDye: dye.r, uDyeTexel: [1 / DYE.w, 1 / DYE.h], uThin: pal.thin, uDense: pal.dense, uSheen: pal.sheen, uSheenAmt: pal.sheenAmt }); return true;
  }
  function clear() { for (const b of [vel, dye, prs]) for (const x of [b.r, b.w]) { gl.bindFramebuffer(gl.FRAMEBUFFER, x.f); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); } parts.length = 0; pending.length = 0; lastSplat = -99; }
  // 碎片（画在调用方的 2D 画布上，逻辑坐标）
  const rnd = (a, b) => a + (b - a) * Math.random();
  const rockPts = () => Array.from({ length: 6 }, (_, i) => { const a = i / 6 * 6.283 + rnd(-.3, .3), r = rnd(.6, 1); return [Math.cos(a) * r, Math.sin(a) * r * .8]; });
  const flake = (x, y, vx, vy, col) => parts.push({ k: 'flake', x, y, vx, vy, g: 40, drag: 2.2, s: rnd(3, 5.5), rot: rnd(0, 6), spin: rnd(-9, 9), t: 0, life: rnd(.9, 1.5), c: col || (CFG.palette === 'qingjin' ? (Math.random() < .35 ? '#c9a24a' : '#0d2a38') : '#16130f') });
  // GPT 画的刀气（10-25 用户看了程序画的弯刀：「你这项一个弧形，不行，可以接上gpt 那张图在里面吗？」）：和游戏同一张 img/fx_paint.png（工具/vfx/cut_paint.py 转的光），
  // blade 那一格是一道竖着的拱形刀光（外弧朝上）。量过：外沿弧心在格内 (197, 212)、半径 187；从左脚（约 99°）经顶部扫到右脚（约 38°）共 299°，绕 (197, 300) 转
  const PAINT = { img: new Image(), meta: null }; PAINT.img.src = (opt.base || '') + 'img/fx_paint.png'; fetch((opt.base || '') + 'img/fx_paint.json').then(r => r.json()).then(j => { PAINT.meta = j; }).catch(() => {});
  const paintOk = () => PAINT.meta && PAINT.img.complete && PAINT.img.naturalWidth > 0;
  const OFF = document.createElement('canvas'), OX = OFF.getContext('2d');
  const BL = { ox: 197, oy: 212, r: 187, mx: 197, my: 300, a0: 99 * Math.PI / 180, span: 299 / 360 };
  function paintRect(nm) { const m = PAINT.meta[nm]; return [m.cell[0] + m.box[0], m.cell[1] + m.box[1], m.box[2], m.box[3]]; }
  // 画一整张（飞行的刀光）：中心在 (x, y)，长边画 w，rot 把画里「朝上」转到哪
  function drawPaint(g, nm, x, y, w, rot, alpha = 1, glow = .35) { if (!paintOk() || !PAINT.meta[nm]) return false; const [sx, sy, sw, sh] = paintRect(nm), k = w / Math.max(sw, sh);
    g.save(); g.translate(x, y); g.rotate(rot); g.globalAlpha = alpha; g.drawImage(PAINT.img, sx, sy, sw, sh, -sw * k / 2, -sh * k / 2, sw * k, sh * k);
    if (glow) { g.globalCompositeOperation = 'lighter'; g.globalAlpha = alpha * glow; g.drawImage(PAINT.img, sx, sy, sw, sh, -sw * k / 2, -sh * k / 2, sw * k, sh * k); } g.restore(); return true; }
  // 青龙斩的刀：这张画按扫的进度从一只脚经顶部显到另一只脚（锥形渐变当遮罩），刀头一点金光；扫完从刀尾收掉
  function drawBladePaint(g, p) {
    const [sx, sy, sw, sh] = paintRect('blade'), SW = .16, HOLD = .06, e = u => 1 - Math.pow(1 - Math.min(1, Math.max(0, u)), 3);
    const lead = e(p.t / SW), fade = Math.min(1, Math.max(0, (p.t - SW - HOLD) / (p.life - SW - HOLD))), tail = fade * fade;
    if (OFF.width !== sw || OFF.height !== sh) { OFF.width = sw; OFF.height = sh; }
    OX.globalCompositeOperation = 'source-over'; OX.clearRect(0, 0, sw, sh); OX.drawImage(PAINT.img, sx, sy, sw, sh, 0, 0, sw, sh);
    const fl = BL.span * lead, ft = BL.span * tail;
    if (OX.createConicGradient) { const cg = OX.createConicGradient(BL.a0, BL.mx, BL.my), stops = ft > 0 ? [[0, 0], [ft, 0], [ft + .07, 1], [fl - .012, 1], [fl + .01, 0], [1, 0]] : [[0, 1], [fl - .012, 1], [fl + .01, 0], [1, 0]];
      let last = 0; for (const [f, a] of stops) { const ff = Math.min(1, Math.max(last, f)); cg.addColorStop(ff, `rgba(0,0,0,${a})`); last = ff; }
      OX.globalCompositeOperation = 'destination-in'; OX.fillStyle = cg; OX.fillRect(0, 0, sw, sh); }
    const k = p.R / BL.r, al = 1 - fade * .4;
    g.save(); g.translate(p.cx, p.cy); g.scale(p.dir < 0 ? -k : k, k * .62);                                                            // 竖向压扁：贴着战场横扫，不立成拱门 g.globalAlpha = al; g.drawImage(OFF, -BL.ox, -BL.oy);
    g.globalCompositeOperation = 'lighter'; g.globalAlpha = .4 * al; g.drawImage(OFF, -BL.ox, -BL.oy);                                    // 叠一遍光
    if (lead < 1 || p.t < SW + HOLD) { const A = BL.a0 + 6.2832 * fl, hx = BL.mx + Math.cos(A) * 190 - BL.ox, hy = BL.my + Math.sin(A) * 190 - BL.oy, rr = 70;   // 刀头一点金光
      const gr = g.createRadialGradient(hx, hy, 0, hx, hy, rr); gr.addColorStop(0, 'rgba(255,236,170,.9)'); gr.addColorStop(1, 'rgba(255,220,140,0)'); g.globalAlpha = 1; g.fillStyle = gr; g.fillRect(hx - rr, hy - rr, rr * 2, rr * 2); }
    g.restore();
  }
  // 弯刀光（10-25 用户：「青龙斩缺乏那个弯刀的斩」）——程序画的，现在只在画稿没读到时用：刀头沿弧从一头扫到另一头（0.16 秒），刀尖锐、刀身后半段最厚、刀尾细；
  // 扫完刀尾追上刀头收掉。青金：刀身石青、外沿泥金；黑墨：银白。墨浪跟在刀后面翻
  function drawBlade(g, p) {
    const SW = .16, e = u => 1 - Math.pow(1 - Math.min(1, Math.max(0, u)), 3), lead = e(p.t / SW), fade = Math.min(1, Math.max(0, (p.t - SW) / (p.life - SW)));
    const t0 = Math.max(0, lead - .65), tail = t0 + fade * (lead - t0); if (lead - tail < .01) return;
    const wmax = p.R * .3, N = 48, out = [], inn = [], qj = CFG.palette === 'qingjin';
    for (let i = 0; i <= N; i++) { const k = i / N, u = tail + (lead - tail) * k, a = p.a0 + (p.a1 - p.a0) * u, w = wmax * Math.pow(Math.sin(Math.PI * k), .6) * (.55 + .45 * k) * (1 - fade * .5), c = Math.cos(a), s2 = Math.sin(a);
      out.push([p.cx + c * p.R, p.cy + s2 * p.R * .8]); inn.push([p.cx + c * (p.R - w), p.cy + s2 * (p.R - w) * .8]); }
    const path = () => { g.beginPath(); out.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); for (let i = inn.length - 1; i >= 0; i--) g.lineTo(inn[i][0], inn[i][1]); g.closePath(); };
    const al = 1 - fade * fade; g.save();
    const line = (pts, w, col, a2) => { g.globalAlpha = a2; g.strokeStyle = col; g.lineWidth = w; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.stroke(); };
    const grd = g.createLinearGradient(out[N >> 1][0], out[N >> 1][1], inn[N >> 1][0], inn[N >> 1][1]);                                        // 刀身：刃口亮、往刀背渐深
    if (qj) { grd.addColorStop(0, '#9ff0dc'); grd.addColorStop(.35, '#3aa996'); grd.addColorStop(1, '#165a58'); } else { grd.addColorStop(0, '#ffffff'); grd.addColorStop(.4, '#cfd6dc'); grd.addColorStop(1, '#7d8790'); }
    g.globalAlpha = .94 * al; g.fillStyle = grd; path(); g.fill();
    line(inn, 1.4, qj ? '#0b3332' : '#3b434a', .7 * al);                                                                                         // 刀背一道深线，月牙才有形
    g.globalCompositeOperation = 'lighter'; g.shadowColor = qj ? '#f2c14e' : '#ffffff'; g.shadowBlur = 12; g.globalAlpha = .22 * al; g.fillStyle = qj ? '#7fe6cf' : '#ffffff'; path(); g.fill();   // 淡淡一层光，不冲白
    g.globalCompositeOperation = 'source-over'; g.shadowBlur = 6; line(out, 2.6, qj ? '#ffd978' : '#ffffff', al);                                    // 外沿刃口（泥金）
    g.globalCompositeOperation = 'lighter'; g.shadowBlur = 0;                                                                                       // 三道刀风：贴着刀弧、落在刀后面一截
    [[.86, .5, 1.4], [.74, .62, 1.1], [1.1, .4, 1.2]].forEach(([rk, lag, wd]) => { const hi = Math.max(tail, lead - .06), lo = Math.max(tail, hi - lag); if (hi - lo < .02) return; const pts = [];
      for (let i = 0; i <= 24; i++) { const u = lo + (hi - lo) * i / 24, a = p.a0 + (p.a1 - p.a0) * u; pts.push([p.cx + Math.cos(a) * p.R * rk, p.cy + Math.sin(a) * p.R * rk * .8]); }
      line(pts, wd, qj ? '#ffe7a0' : '#ffffff', .45 * al * (1 - fade)); });
    if (fade < .3) { const [hx, hy] = out[out.length - 1]; const gr = g.createRadialGradient(hx, hy, 0, hx, hy, p.R * .22); gr.addColorStop(0, 'rgba(255,236,170,' + .8 * (1 - fade / .3) + ')'); gr.addColorStop(1, 'rgba(255,220,140,0)'); g.globalCompositeOperation = 'lighter'; g.fillStyle = gr; g.shadowBlur = 0; g.globalAlpha = 1; g.fillRect(hx - p.R * .22, hy - p.R * .22, p.R * .44, p.R * .44); }   // 刀头一点金光
    g.restore();
  }
  // 火星（10-25 用户圈着一根根直的淡黄短线：「这是什么，这些要优化啊」）：一个发光的亮点，后面拖一小段渐细渐淡、跟着轨迹弯的尾巴，一闪一闪
  function drawSpark(g, p, a, col) {
    const h = p.hist || (p.hist = []); h.push([p.x, p.y]); if (h.length > 6) h.shift();
    const fl = .65 + .35 * Math.sin(p.t * 40 + p.s * 9); g.save(); g.globalCompositeOperation = 'lighter'; g.lineCap = 'round';
    for (let i = 1; i < h.length; i++) { const u = i / (h.length - 1); g.globalAlpha = a * fl * u * .8; g.strokeStyle = col; g.lineWidth = p.s * (.3 + .9 * u); g.beginPath(); g.moveTo(h[i - 1][0], h[i - 1][1]); g.lineTo(h[i][0], h[i][1]); g.stroke(); }
    const r = p.s * 2.2, gr = g.createRadialGradient(p.x, p.y, 0, p.x, p.y, r); gr.addColorStop(0, 'rgba(255,250,225,1)'); gr.addColorStop(.35, col); gr.addColorStop(1, 'rgba(255,120,30,0)');
    g.globalAlpha = a * fl; g.fillStyle = gr; g.fillRect(p.x - r, p.y - r, r * 2, r * 2); g.restore();
  }
  function drawParts(g) {
    for (const p of parts) { const a = Math.min(1, (p.life - p.t) / .3);
      if (p.k === 'blade') { if (paintOk() && PAINT.meta.blade) drawBladePaint(g, p); else drawBlade(g, p); continue; }
      if (p.k === 'rock') { g.save(); g.translate(p.x, p.y); g.rotate(p.rot); g.globalAlpha = a; g.fillStyle = p.c; g.beginPath(); p.pts.forEach(([px, py], i) => i ? g.lineTo(px * p.s, py * p.s) : g.moveTo(px * p.s, py * p.s)); g.closePath(); g.fill(); g.fillStyle = 'rgba(255,190,110,.35)'; g.beginPath(); g.arc(-p.s * .2, -p.s * .25, p.s * .35, 0, 6.283); g.fill(); g.restore(); }
      else if (p.k === 'flake') { g.save(); g.translate(p.x, p.y); g.rotate(p.rot); g.scale(1, Math.abs(Math.cos(p.t * 7 + p.rot)) * .8 + .2); g.globalAlpha = a * .9; g.fillStyle = p.c; g.beginPath(); g.moveTo(-p.s, 0); g.quadraticCurveTo(0, -p.s * .55, p.s, 0); g.quadraticCurveTo(0, p.s * .35, -p.s, 0); g.fill(); g.restore(); }
      else if (p.k === 'ember') drawSpark(g, p, a, p.c);
      else { const sp = Math.hypot(p.vx, p.vy) || 1, l = Math.min(14, sp * .02); g.globalAlpha = a; g.strokeStyle = p.c; g.lineWidth = p.s; g.lineCap = 'round'; g.beginPath(); g.moveTo(p.x, p.y); g.lineTo(p.x - p.vx / sp * l, p.y - p.vy / sp * l); g.stroke(); } }
    g.globalAlpha = 1;
  }
  const fx = {
    // 青龙斩：刀头沿一道上弧扫过去（0.18 秒），刀路上甩出墨丝，速度顺着刀走、往外翻；刀过之后墨浪往上卷，卷出飞片
    qinglong(cx, cy, R = 120, dir = 1, o = {}) {                                                // o.ink === false：只要刀，不翻墨（10-25 用户：「不要浓雾了，就中间那个就很好」）
      const a0 = Math.PI * (dir > 0 ? 1.12 : 1.88), a1 = Math.PI * (dir > 0 ? 1.88 : 1.12), N = 26;
      parts.push({ k: 'blade', cx, cy, R: R * 1.04, a0, a1, dir, x: 0, y: 0, vx: 0, vy: 0, g: 0, rot: 0, spin: 0, t: 0, life: .5 });   // 刀走在墨浪外沿一点
      if (o.ink === false) return;
      for (let i = 0; i <= N; i++) at(.18 * i / N, () => { const u = i / N, a = a0 + (a1 - a0) * u, x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * R * .8, tx = -Math.sin(a) * dir, ty = Math.cos(a) * .8 * dir, ox = Math.cos(a), oy = Math.sin(a);
        const amp = Math.sin(Math.PI * u) * .7 + .3, j = rnd(-1, 1);
        splat(x + ox * j * 6, y + oy * j * 5, (tx * 1100 + ox * (260 + 300 * j)) * amp, (ty * 1100 + oy * (260 + 300 * j)) * amp, 5 + 5 * amp, [1.5 * amp, 0, 0, 0]);
        splat(x - ox * 10, y - oy * 8, (tx * 500 - ox * 200) * amp + rnd(-150, 150), (ty * 500 - oy * 200) * amp + rnd(-150, 150), 6, [1 * amp, 0, 0, 0]);
        splat(x + ox * 14, y + oy * 12, ox * 500 + tx * 300, oy * 500 + ty * 300 - 150, 7, [0, 0, 0, 1.2 * amp]);
        if (i % 3 === 0) flake(x, y, tx * 520 + ox * rnd(80, 260), ty * 520 + oy * rnd(80, 260) - 60); });
      at(.22, () => { for (let k = 0; k < 5; k++) { const a = a0 + (a1 - a0) * (k + .5) / 5, x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * R * .8; splat(x, y, Math.cos(a) * 380 + rnd(-160, 160), -420 + Math.sin(a) * 160, 7, [.6, 0, 0, .35]); } });
    },
    // 当阳一喝：地上一点炸开——火往四周和上方喷，带烟；地面扬尘；碎石、火星飞出去
    roar(x, y) {
      for (let k = 0; k < 14; k++) { const a = Math.PI * (1.05 + .9 * k / 13) + rnd(-.08, .08), sp = rnd(600, 1100); splat(x + Math.cos(a) * 10, y + Math.sin(a) * 6, Math.cos(a) * sp, Math.sin(a) * sp * .8 - 150, rnd(8, 13), [0, rnd(1.1, 1.7), .5, 0]); }
      for (let i = 0; i < 10; i++) at(i * .035, () => splat(x + rnd(-18, 18), y - 8, rnd(-160, 160), rnd(-650, -400), rnd(8, 12), [0, 1.2, .4, 0]));
      at(.06, () => { for (let k = 0; k < 7; k++) { const a = Math.PI * (1.0 + k / 6) + rnd(-.1, .1), sp = rnd(180, 320); splat(x + Math.cos(a) * 30, y + 6, Math.cos(a) * sp, rnd(-220, -120), rnd(10, 16), [0, .1, .7, 0]); } });   // 地面扬尘：慢、往上，不卷成两个轮子
      for (let i = 0; i < 12; i++) { const a = Math.PI * rnd(1.1, 1.9), sp = rnd(220, 520); parts.push({ k: 'rock', x: x + rnd(-10, 10), y: y - 4, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 900, s: rnd(3, 7), rot: rnd(0, 6), spin: rnd(-12, 12), t: 0, life: rnd(1, 1.6), c: ['#3a3029', '#4b3d33', '#2a231e'][i % 3], pts: rockPts(), ground: y + rnd(0, 30) }); }
      for (let i = 0; i < 9; i++) { const a = Math.PI * rnd(1.15, 1.85), sp = rnd(200, 420); parts.push({ k: 'ember', x, y: y - 6, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 520, drag: 1.2, s: rnd(1.4, 2.2), rot: 0, spin: 0, t: 0, life: rnd(.6, 1), c: '#ff9a2e' }); }
    },
    // 火丝：一股细火绕着往上盘（不对称、带随机，两股对称的像个蝴蝶结）
    fireWhip(x, y) {
      const N = 110, ph = rnd(0, 6.283), sgn = Math.random() < .5 ? 1 : -1;                      // 点得密，连成一条火带，不是一串珠子
      for (let i = 0; i < N; i++) at(i * .0068, () => { const u = i / N, a = ph + u * Math.PI * 2.6 * sgn, r = (40 + u * 70) * rnd(.85, 1.15), px = x + Math.cos(a) * r + u * 30 * sgn, py = y - 10 - u * 230 + Math.sin(a) * r * .4;
        splat(px, py, -Math.sin(a) * 300 * sgn + rnd(-60, 60), Math.cos(a) * 120 * sgn - 140, 3.5 + u * 1.5, [0, 1.25, .2, 0]); });   // 慢一点，留下一条火带，不甩成火球
    },
    // 水箭：顺着兵器喷出去的一股白色水雾，越往前越散，带水珠
    jet(x0, y0, x1, y1) {
      const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, N = 18;
      for (let i = 0; i < N; i++) at(i * .012, () => { const u = i / N, x = x0 + dx * u, y = y0 + dy * u, sp = 1300 * (1 - u * .4), side = rnd(-1, 1);
        for (const off of [-1, 0, 1]) { const o = off * (4 + u * 14) + side * 4; splat(x - uy * o, y + ux * o, ux * sp - uy * o * 14, uy * sp + ux * o * 14, 5 + u * 9, [0, 0, 0, (off ? 1.4 : 2.4) * (1 - u * .35)]); } });
      for (let i = 0; i < 18; i++) { const u = rnd(.1, .9), sp = rnd(400, 900), a = Math.atan2(uy, ux) + rnd(-.5, .5); parts.push({ k: 'drop', x: x0 + dx * u, y: y0 + dy * u, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 500, s: rnd(1.6, 2.6), rot: 0, spin: 0, t: 0, life: rnd(.35, .7), c: '#f4f8ff' }); }
    },
    // 墨龙：一股墨从下往上盘旋着冲起来
    inkDragon(x, y) {
      const N = 26;
      for (let i = 0; i < N; i++) at(i * .025, () => { const u = i / N, a = u * Math.PI * 3.2, px = x + Math.sin(a) * 60 * (1 - u * .4), py = y - u * 330, vx = Math.cos(a) * 520, vy = -620;
        splat(px, py, vx, vy, 9 - u * 3, [1.3, 0, 0, .2]); if (i % 3 === 0) { splat(px + Math.cos(a) * 18, py, vx * .6, vy * .6, 6, [0, 0, 0, 1.2]); flake(px, py, vx * .7, vy * .5); } });
    },
  };
  return { canvas: c, cfg: CFG, splat, step, render, clear, drawParts, drawPaint, paintOk, idle, fx, get t() { return t; } };
}
window.Moliu = { create, PALETTE };
})();
