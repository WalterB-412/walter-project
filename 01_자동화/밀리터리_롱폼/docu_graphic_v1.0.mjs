#!/usr/bin/env node
/**
 * docu_graphic_v1.0.mjs — 롱폼 다큐 정보 그래픽 렌더러 (2026-10-12, Walter 지시 4·5번)
 *
 * scenes.json에서 footage.type=="graphic" 씬을 찾아 HTML로 그린 뒤,
 * CSS 애니메이션을 프레임 단위로 캡처해 1920×1080 mp4(애니메이션)와 @2x png(완성 정지화면)를 만든다.
 *   _work/<run>/graphics/scene_<id>.mp4      ← military_build v1.5가 영상 입력으로 사용(모자란 길이는 끝 프레임 홀드)
 *   _work/<run>/graphics/scene_<id>@2x.png   ← 눈검수·preflight 존재 확인용
 *   _work/<run>/graphics/scene_<id>.html     ← 디버그(브라우저로 열어 확인)
 *   _work/<run>/graphics/index.json          ← footage_collect v1.7이 읽는다 [{scene_id,kind,title,video,png}]
 *
 * 그래픽 종류(footage.graphic.kind) — 상세 스펙은 그래픽_스펙_v1.0.md
 *   big_number   핵심 숫자 1개(카운트업)
 *   stat_compare 2~4개 항목 막대 비교
 *   timeline     연대기 3~6개 지점
 *   map          지도: 국가 강조·지점·경로·경계선·사거리 원 (Natural Earth, 퍼블릭 도메인)
 *   route        (구버전 호환) from/to 국가명 → map 경로로 변환
 *   spec_table   제원 비교표(최대 5행 × 3열)
 *
 * 설계 원칙
 *   · 화면 하단 y≥800은 비운다 — 나레이션 자막 띠가 그래픽 위에도 올라온다(layout.zones.subtitle).
 *   · 모든 그래픽은 출처(graphic.source)를 화면에 표기한다(preflight [GFX-SOURCE]가 강제).
 *   · 애니메이션은 0~ANIM_S 안에 끝나고, 이후는 완성 화면 홀드(빌드가 tpad로 늘린다).
 *
 * 사용:
 *   node docu_graphic_v1.0.mjs --run-id millong_NNN [--scene 12] [--html-only]
 * 의존성(이 폴더에서 1회): npm i puppeteer d3-geo topojson-client world-atlas
 *   (puppeteer 대신 puppeteer-core + 환경변수 CHROME_PATH도 가능)
 */
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const BASE = path.dirname(fileURLToPath(import.meta.url));
const LAYOUT = JSON.parse(fs.readFileSync(path.join(BASE, "layout.json"), "utf-8"));
const W = LAYOUT.canvas.w, H = LAYOUT.canvas.h, FPS = LAYOUT.canvas.fps;
const ANIM_S = 3.2;          // 애니메이션 길이(초). 이후는 완성 화면
const CLIP_S = 4.0;          // mp4 길이. 씬이 더 길면 빌드가 마지막 프레임을 홀드한다
const SAFE_BOTTOM = 800;     // 이 아래는 자막 띠 자리 — 그래픽 내용 금지

// ── 폰트: layout.fonts 단일 소스(빌드와 같은 파일) ─────────────────────────────
function fontPath() {
  const f = LAYOUT.fonts || {};
  const cands = [f.main, ...(f.fallbacks || [])].filter(Boolean).map(p => path.resolve(BASE, p));
  return cands.find(p => fs.existsSync(p)) || null;
}

// ── 국가 사전: 한국어 이름 → Natural Earth 이름 + 대표 좌표(수도) ────────────────
const COUNTRIES = {
  "대한민국": ["South Korea", 126.98, 37.57], "한국": ["South Korea", 126.98, 37.57],
  "북한": ["North Korea", 125.75, 39.02], "미국": ["United States of America", -77.04, 38.9],
  "일본": ["Japan", 139.69, 35.69], "중국": ["China", 116.4, 39.9], "러시아": ["Russia", 37.62, 55.75],
  "우크라이나": ["Ukraine", 30.52, 50.45], "폴란드": ["Poland", 21.01, 52.23],
  "노르웨이": ["Norway", 10.75, 59.91], "핀란드": ["Finland", 24.94, 60.17],
  "스웨덴": ["Sweden", 18.07, 59.33], "에스토니아": ["Estonia", 24.75, 59.44],
  "라트비아": ["Latvia", 24.11, 56.95], "리투아니아": ["Lithuania", 25.28, 54.69],
  "루마니아": ["Romania", 26.1, 44.43], "체코": ["Czechia", 14.42, 50.08],
  "슬로바키아": ["Slovakia", 17.11, 48.15], "헝가리": ["Hungary", 19.04, 47.5],
  "독일": ["Germany", 13.4, 52.52], "프랑스": ["France", 2.35, 48.86], "영국": ["United Kingdom", -0.13, 51.51],
  "이탈리아": ["Italy", 12.5, 41.9], "스페인": ["Spain", -3.7, 40.42], "튀르키예": ["Turkey", 32.85, 39.93],
  "터키": ["Turkey", 32.85, 39.93], "그리스": ["Greece", 23.73, 37.98], "이스라엘": ["Israel", 35.21, 31.77],
  "이란": ["Iran", 51.39, 35.69], "이라크": ["Iraq", 44.36, 33.31], "사우디아라비아": ["Saudi Arabia", 46.72, 24.71],
  "아랍에미리트": ["United Arab Emirates", 54.37, 24.45], "UAE": ["United Arab Emirates", 54.37, 24.45],
  "카타르": ["Qatar", 51.53, 25.29], "이집트": ["Egypt", 31.24, 30.04], "인도": ["India", 77.21, 28.61],
  "파키스탄": ["Pakistan", 73.05, 33.68], "호주": ["Australia", 149.13, -35.28], "필리핀": ["Philippines", 120.98, 14.6],
  "인도네시아": ["Indonesia", 106.85, -6.21], "말레이시아": ["Malaysia", 101.69, 3.14], "베트남": ["Vietnam", 105.85, 21.03],
  "태국": ["Thailand", 100.5, 13.76], "대만": ["Taiwan", 121.56, 25.03], "캐나다": ["Canada", -75.7, 45.42],
  "브라질": ["Brazil", -47.88, -15.79], "페루": ["Peru", -77.04, -12.05], "콜롬비아": ["Colombia", -74.07, 4.71],
  "남아프리카공화국": ["South Africa", 28.19, -25.75], "카자흐스탄": ["Kazakhstan", 71.45, 51.17],
  "몽골": ["Mongolia", 106.92, 47.92], "싱가포르": ["Singapore", 103.82, 1.35],
};
const resolveCountry = n => COUNTRIES[n] ? { ne: COUNTRIES[n][0], lonlat: [COUNTRIES[n][1], COUNTRIES[n][2]] }
                                         : { ne: n, lonlat: null };

// ── 공통 스타일 ────────────────────────────────────────────────────────────────
const C = { bg: "#0c0e11", panel: "#15191e", line: "#2a3038", text: "#f2f2f2", sub: "#a9b0b8",
            accent: "#e8b04b", accent2: "#5aa9e6", land: "#1e242b", landHi: "#3b4651", sea: "#0a0c0f" };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function page(g, body, extraCss = "") {
  const fp = fontPath();
  const face = fp ? `@font-face{font-family:Docu;src:url("${pathToFileURL(fp).href}");}` : "";
  return `<!doctype html><html><head><meta charset="utf-8"><style>
${face}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:${W}px;height:${H}px;overflow:hidden;background:${C.bg};color:${C.text};
  font-family:Docu,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
body{background:radial-gradient(ellipse at 30% 20%,#161b21 0%,${C.bg} 60%)}
.title{position:absolute;left:96px;top:72px;font-size:52px;letter-spacing:-.5px;
  animation:fadeUp .6s ease-out both}
.title small{display:block;font-size:30px;color:${C.sub};margin-top:10px;font-style:italic}
.source{position:absolute;left:96px;top:${SAFE_BOTTOM - 46}px;font-size:24px;color:${C.sub};
  animation:fade .6s .4s ease-out both}
.rule{position:absolute;left:96px;top:${SAFE_BOTTOM - 62}px;width:${W - 192}px;height:1px;background:${C.line}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.4)}70%{opacity:1;transform:scale(1.12)}100%{transform:scale(1)}}
@keyframes draw{to{stroke-dashoffset:0}}
${extraCss}
</style></head><body>
<div class="title">${esc(g.title)}${g.subtitle ? `<small>${esc(g.subtitle)}</small>` : ""}</div>
${body}
<div class="rule"></div>
<div class="source">${esc(g.source || "출처 미기재")}</div>
<script>
// 카운트업: data-count 요소는 애니메이션 시간에 맞춰 숫자를 채운다(프레임 캡처가 시간을 직접 지정)
window.__setTime = t => {
  document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; });
  document.querySelectorAll("[data-count]").forEach(el => {
    const to = parseFloat(el.dataset.count), d = parseFloat(el.dataset.dec || 0);
    const st = parseFloat(el.dataset.start || 0), du = parseFloat(el.dataset.dur || 1.6);
    const k = Math.min(Math.max((t - st) / du, 0), 1), e = 1 - Math.pow(1 - k, 3);
    el.textContent = (to * e).toLocaleString("ko-KR", {minimumFractionDigits: d, maximumFractionDigits: d});
  });
};
</script></body></html>`;
}

// ── big_number ────────────────────────────────────────────────────────────────
function bigNumber(g) {
  const num = parseFloat(String(g.value).replace(/,/g, ""));
  const dec = (String(g.value).split(".")[1] || "").length;
  const val = isFinite(num)
    ? `<span data-count="${num}" data-dec="${dec}" data-start="0.3" data-dur="1.6">0</span>`
    : esc(g.value);
  return page(g, `
<div style="position:absolute;left:0;right:0;top:250px;text-align:center;animation:fade .4s .2s both">
  <div style="font-size:220px;line-height:1;color:${C.accent};letter-spacing:-4px">${val}<span style="font-size:96px;color:${C.text};margin-left:12px">${esc(g.unit || "")}</span></div>
  <div style="font-size:48px;margin-top:34px;animation:fadeUp .6s 1.2s both">${esc(g.label || "")}</div>
  ${g.sub ? `<div style="font-size:32px;color:${C.sub};margin-top:16px;animation:fadeUp .6s 1.5s both">${esc(g.sub)}</div>` : ""}
</div>`);
}

// ── stat_compare (가로 막대) ─────────────────────────────────────────────────
function statCompare(g) {
  const items = (g.items || []).slice(0, 4);
  const max = Math.max(...items.map(i => +i.value || 0), 1);
  const top = 250, rowH = Math.min(120, 440 / Math.max(items.length, 1));
  const rows = items.map((it, i) => {
    const w = Math.max(6, (+it.value || 0) / max * 1080);
    const col = it.highlight ? C.accent : "#56616d";
    return `<div style="position:absolute;left:96px;top:${top + i * rowH}px;width:${W - 192}px;height:${rowH - 26}px">
      <div style="position:absolute;left:0;top:0;width:420px;font-size:40px;line-height:${rowH - 26}px;animation:fade .4s ${0.3 + i * 0.25}s both">${esc(it.label)}</div>
      <div style="position:absolute;left:440px;top:8px;height:${rowH - 42}px;width:${w}px;background:${col};transform-origin:left;
        animation:grow 1.1s ${0.4 + i * 0.25}s cubic-bezier(.2,.8,.2,1) both"></div>
      <div style="position:absolute;left:${460 + w}px;top:0;font-size:40px;line-height:${rowH - 26}px;color:${it.highlight ? C.accent : C.text};
        animation:fade .4s ${1.3 + i * 0.25}s both">${esc(it.value_label ?? it.value)}${esc(g.unit ? " " + g.unit : "")}</div></div>`;
  }).join("");
  return page(g, rows);
}

// ── timeline ──────────────────────────────────────────────────────────────────
function timeline(g) {
  const pts = (g.points || []).slice(0, 6);
  const x0 = 160, x1 = W - 160, y = 470, n = pts.length;
  const xs = pts.map((_, i) => n === 1 ? (x0 + x1) / 2 : x0 + (x1 - x0) * i / (n - 1));
  const items = pts.map((p, i) => {
    const d = 0.5 + i * (1.8 / Math.max(n - 1, 1)), hi = p.highlight || i === g.highlight;
    const up = i % 2 === 0;
    return `<div style="position:absolute;left:${xs[i] - 14}px;top:${y - 14}px;width:28px;height:28px;border-radius:50%;
        background:${hi ? C.accent : C.text};animation:pop .5s ${d}s both"></div>
      <div style="position:absolute;left:${xs[i] - 200}px;width:400px;text-align:center;top:${up ? y - 150 : y + 40}px;animation:fadeUp .5s ${d + 0.15}s both">
        <div style="font-size:46px;color:${hi ? C.accent : C.text}">${esc(p.year)}</div>
        <div style="font-size:30px;color:${C.sub};margin-top:8px;line-height:1.3">${esc(p.label)}</div></div>`;
  }).join("");
  return page(g, `<div style="position:absolute;left:${x0}px;top:${y - 2}px;width:${x1 - x0}px;height:4px;background:${C.line};
      transform-origin:left;animation:grow 2.2s .3s linear both"></div>${items}`);
}

// ── spec_table ────────────────────────────────────────────────────────────────
function specTable(g) {
  const cols = (g.columns || []).slice(0, 3), rows = (g.rows || []).slice(0, 5);
  const top = 230, rowH = 92, colW = [520, 560, 560];
  const head = cols.map((c, j) => `<div style="position:absolute;left:${96 + colW.slice(0, j).reduce((a, b) => a + b, 0)}px;top:${top}px;width:${colW[j]}px;
      font-size:40px;color:${j === 1 ? C.accent : C.text};animation:fade .4s .3s both">${esc(c)}</div>`).join("");
  const body = rows.map((r, i) => r.slice(0, 3).map((c, j) => `<div style="position:absolute;left:${96 + colW.slice(0, j).reduce((a, b) => a + b, 0)}px;
      top:${top + (i + 1) * rowH}px;width:${colW[j]}px;font-size:${j ? 40 : 34}px;color:${j ? C.text : C.sub};
      animation:fadeUp .45s ${0.6 + i * 0.3}s both">${esc(c)}</div>`).join("")
    + `<div style="position:absolute;left:96px;top:${top + (i + 1) * rowH - 20}px;width:${W - 192}px;height:1px;background:${C.line};
      transform-origin:left;animation:grow .6s ${0.5 + i * 0.3}s both"></div>`).join("");
  return page(g, head + body);
}

// ── map (Natural Earth) ───────────────────────────────────────────────────────
async function mapPage(g) {
  const { geoMercator, geoNaturalEarth1, geoPath, geoCircle, geoInterpolate, geoArea } = await import("d3-geo");
  const { feature } = await import("topojson-client");
  const box = { x: 96, y: 200, w: W - 192, h: SAFE_BOTTOM - 80 - 200 };   // 지도 영역(자막 띠 위)
  const hi = (g.highlight || []).map(h => typeof h === "string" ? { country: h } : h)
    .map(h => ({ ...h, ...resolveCountry(h.country) }));
  const pts = (g.points || []).map(p => ({ ...p, lonlat: p.lonlat || (p.country ? resolveCountry(p.country).lonlat : [p.lon, p.lat]) }));
  const routes = (g.routes || []).map(r => ({
    ...r,
    a: Array.isArray(r.from) ? r.from : resolveCountry(r.from).lonlat,
    b: Array.isArray(r.to) ? r.to : resolveCountry(r.to).lonlat,
  })).filter(r => r.a && r.b);
  const lines = (g.lines || []).filter(l => (l.coords || []).length >= 2);   // NLL·군사분계선 등 경계선
  const rings = (g.rings || []).map(r => ({ ...r, c: Array.isArray(r.center) ? r.center : resolveCountry(r.center).lonlat }));
  // 해상도: 표시 범위가 좁을수록 고해상도
  const lons = [], lats = [];
  [...pts.map(p => p.lonlat), ...routes.flatMap(r => [r.a, r.b]), ...rings.map(r => r.c),
   ...hi.map(h => h.lonlat)].filter(Boolean).forEach(([x, y]) => { lons.push(x); lats.push(y); });
  const span = lons.length ? Math.max(Math.max(...lons) - Math.min(...lons), Math.max(...lats) - Math.min(...lats)) : 360;
  const res = g.resolution || (span < 12 ? "10m" : span < 60 ? "50m" : "110m");
  const topo = require(`world-atlas/countries-${res}.json`);
  // 남극은 메르카토르에서 무한대로 펴져 화면 전체를 덮는다 — 항상 제외.
  // 반구보다 넓게 계산되는 폴리곤(감김 방향 역전 — 10m의 Maldives 실측)은 지구 전체를 칠하므로 제외
  const countries = feature(topo, topo.objects.countries).features
    .filter(f => f.properties.name !== "Antarctica" && geoArea(f) <= 2 * Math.PI);
  const byName = new Map(countries.map(f => [f.properties.name, f]));
  const missing = hi.filter(h => !byName.has(h.ne)).map(h => h.country);
  if (missing.length) console.error(`  ⚠️ 지도 국가명 미발견: ${missing.join(", ")} — Natural Earth 영문명 또는 사전(COUNTRIES)에 추가`);
  // 투영 맞춤: 강조국·지점·경로·원을 모두 담는 GeoJSON
  const fitFeats = [
    ...hi.filter(h => byName.has(h.ne)).map(h => byName.get(h.ne)),
    ...pts.map(p => ({ type: "Feature", geometry: { type: "Point", coordinates: p.lonlat } })),
    ...routes.map(r => ({ type: "Feature", geometry: { type: "LineString", coordinates: [r.a, r.b] } })),
    ...rings.map(r => ({ type: "Feature", geometry: geoCircle().center(r.c).radius(r.radius_km / 111.2)() })),
  ];
  // bbox [서경,남위,동경,북위]를 주면 그 범위만 맞춘다(강조국 전체를 담느라 확대가 풀리는 것 방지)
  const fitTarget = g.bbox
    ? [{ type: "Feature", geometry: { type: "LineString", coordinates: [[g.bbox[0], g.bbox[1]], [g.bbox[2], g.bbox[3]]] } }]
    : fitFeats;
  const pad = g.padding ?? (g.bbox ? 0.02 : 0.12);
  // 넓은 범위(대륙 간)는 왜곡이 적은 Natural Earth 투영, 좁은 범위는 메르카토르
  const proj = (span > 90 ? geoNaturalEarth1() : geoMercator()).fitExtent(
    [[box.x + box.w * pad, box.y + box.h * pad], [box.x + box.w * (1 - pad), box.y + box.h * (1 - pad)]],
    { type: "FeatureCollection", features: fitTarget.length ? fitTarget : countries });
  const gp = geoPath(proj);
  const hiSet = new Set(hi.map(h => h.ne));
  const land = countries.map(f => `<path d="${gp(f) || ""}" fill="${hiSet.has(f.properties.name) ? C.landHi : C.land}" stroke="#39424c" stroke-width="1"/>`).join("");
  const hiPaths = hi.filter(h => byName.has(h.ne)).map((h, i) =>
    `<path d="${gp(byName.get(h.ne))}" fill="${h.color || C.accent}" fill-opacity=".85" stroke="#fff" stroke-width="1.5"
      style="animation:fade .6s ${0.5 + i * 0.3}s both"/>`).join("");
  const routeSvg = routes.map((r, i) => {
    const interp = geoInterpolate(r.a, r.b), seg = 64;
    const d = gp({ type: "LineString", coordinates: Array.from({ length: seg + 1 }, (_, k) => interp(k / seg)) });
    return `<path d="${d}" fill="none" stroke="${C.accent}" stroke-width="5" stroke-linecap="round"
      pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" style="animation:draw 1.4s ${0.9 + i * 0.4}s ease-in-out forwards"/>`;
  }).join("");
  const ringSvg = rings.map((r, i) => {
    const d = gp(geoCircle().center(r.c).radius(r.radius_km / 111.2)());
    const [cx, cy] = proj(r.c);
    return `<g style="transform-origin:${cx}px ${cy}px;animation:pop .9s ${0.8 + i * 0.3}s both">
      <path d="${d}" fill="${C.accent2}" fill-opacity=".12" stroke="${C.accent2}" stroke-width="3" stroke-dasharray="10 8"/></g>`;
  }).join("");
  const lineSvg = lines.map((l, i) => {
    const d = gp({ type: "LineString", coordinates: l.coords });
    return `<path d="${d}" fill="none" stroke="${l.color || "#e25b4b"}" stroke-width="4"
      ${l.dash === false ? "" : 'stroke-dasharray="14 10"'} style="animation:fade .8s ${0.7 + i * 0.3}s both"/>`;
  }).join("");
  const ptSvg = pts.map((p, i) => {
    const [x, y] = proj(p.lonlat);
    return `<g style="transform-origin:${x}px ${y}px;animation:pop .5s ${1.0 + i * 0.25}s both">
      <circle cx="${x}" cy="${y}" r="11" fill="${p.color || C.text}" stroke="${C.bg}" stroke-width="3"/></g>`;
  }).join("");
  // 라벨은 HTML(폰트 일관) — 지점·경로 끝·원 라벨·강조국 라벨
  const labels = [
    ...pts.map((p, i) => { const [x, y] = proj(p.lonlat); return { x, y, t: p.label, d: 1.1 + i * 0.25, dx: p.label_dx ?? 22, dy: p.label_dy ?? -18 }; }),
    ...lines.filter(l => l.label).map((l, i) => { const [x, y] = proj(l.coords[l.label_at ?? l.coords.length - 1]); return { x, y, t: l.label, d: 1.0 + i * 0.3, dx: 10, dy: -10 }; }),
    ...rings.filter(r => r.label).map((r, i) => { const [x, y] = proj(r.c); const e = proj(geoCircle().center(r.c).radius(r.radius_km / 111.2)().coordinates[0][0]); return { x: e[0], y: e[1], t: r.label, d: 1.3 + i * 0.3, dx: 12, dy: -10 }; }),
    ...hi.filter(h => h.label && byName.has(h.ne)).map((h, i) => { const [x, y] = gp.centroid(byName.get(h.ne)); return { x, y, t: h.label, d: 0.8 + i * 0.3, dx: h.label_dx ?? -40, dy: h.label_dy ?? 0 }; }),
  ].filter(l => l.t && isFinite(l.x));
  // 라벨 겹침 회피: 위에서부터 놓고, 이미 놓인 라벨과 겹치면 아래로 민다(대략 폭 = 글자수×32px)
  const placed = [];
  for (const l of labels.sort((a, b) => (a.y + a.dy) - (b.y + b.dy))) {
    l.w = [...String(l.t)].length * 32 + 8; l.h = 42;
    let x = l.x + l.dx, y = l.y + l.dy - 22;
    for (let k = 0; k < 12 && placed.some(p => x < p.x + p.w && p.x < x + l.w && y < p.y + p.h && p.y < y + l.h); k++) y += 40;
    l.px = x; l.py = y; placed.push({ x, y, w: l.w, h: l.h });
  }
  const labelHtml = labels.map(l => `<div style="position:absolute;left:${l.px}px;top:${l.py}px;font-size:34px;
      white-space:nowrap;text-shadow:0 2px 6px #000,0 0 2px #000;animation:fade .4s ${l.d}s both">${esc(l.t)}</div>`).join("");
  const svg = `<svg width="${W}" height="${H}" style="position:absolute;left:0;top:0">
    <defs><clipPath id="clip"><rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" rx="6"/></clipPath></defs>
    <rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" fill="${C.sea}" rx="6"/>
    <g clip-path="url(#clip)"><g style="animation:fade .8s .1s both">${land}</g>${hiPaths}${lineSvg}${ringSvg}${routeSvg}${ptSvg}</g></svg>`;
  return page(g, svg + labelHtml);
}

function legacyRoute(g) {   // 스타일가이드 v1.3의 route(from/to 국가명) 호환
  return { ...g, kind: "map", highlight: [g.from, g.to].filter(Boolean).map(c => ({ country: c, label: c })),
           routes: [{ from: g.from, to: g.to }], subtitle: g.subtitle || g.note };
}

async function htmlFor(g) {
  switch (g.kind) {
    case "big_number": return bigNumber(g);
    case "stat_compare": return statCompare(g);
    case "timeline": return timeline(g);
    case "spec_table": return specTable(g);
    case "map": return mapPage(g);
    case "route": return mapPage(legacyRoute(g));
    default: throw new Error(`알 수 없는 graphic.kind: ${g.kind}`);
  }
}

// ── 캡처 ──────────────────────────────────────────────────────────────────────
async function launch() {
  let pp;
  try { pp = (await import("puppeteer")).default; }
  catch { pp = (await import("puppeteer-core")).default; }
  const opts = { args: ["--no-sandbox", "--allow-file-access-from-files", "--font-render-hinting=none"] };
  if (process.env.CHROME_PATH) opts.executablePath = process.env.CHROME_PATH;
  return pp.launch(opts);
}

function ffmpegPipe(out) {
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-r", String(FPS), out],
    { stdio: ["pipe", "inherit", "inherit"] });
  return ff;
}

async function render(browser, html, outBase) {
  fs.writeFileSync(outBase + ".html", html);
  const pg = await browser.newPage();
  await pg.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await pg.goto(pathToFileURL(outBase + ".html").href, { waitUntil: "load" });
  await pg.evaluate(() => document.fonts.ready);
  const ff = ffmpegPipe(outBase + ".mp4");
  const n = Math.round(CLIP_S * FPS);
  for (let i = 0; i < n; i++) {
    const t = Math.min(i / FPS, ANIM_S + 0.5);
    await pg.evaluate(t => window.__setTime(t), t);
    const buf = await pg.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg 실패"))));
  // 완성 정지화면 @2x
  await pg.setViewport({ width: W, height: H, deviceScaleFactor: 2 });
  await pg.evaluate(t => window.__setTime(t), ANIM_S + 1);
  await pg.screenshot({ path: outBase + "@2x.png" });
  await pg.close();
}

async function main() {
  const args = process.argv.slice(2);
  const arg = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
  const runId = arg("--run-id"), only = arg("--scene"), htmlOnly = args.includes("--html-only");
  if (!runId) { console.error("사용: node docu_graphic_v1.0.mjs --run-id millong_NNN [--scene N] [--html-only]"); process.exit(1); }
  const work = path.join(BASE, "_work", runId);
  const doc = JSON.parse(fs.readFileSync(path.join(work, "scenes.json"), "utf-8"));
  if (doc.run_id !== runId) { console.error("⛔ run_id 불일치"); process.exit(2); }
  const outDir = path.join(work, "graphics");
  fs.mkdirSync(outDir, { recursive: true });
  if (!fontPath()) console.error("  ⚠️ layout.json fonts의 폰트 파일을 못 찾았다 — 시스템 폰트로 렌더(빌드 자막과 글꼴이 달라진다)");
  const idxPath = path.join(outDir, "index.json");
  const index = fs.existsSync(idxPath) ? JSON.parse(fs.readFileSync(idxPath, "utf-8")) : [];
  const targets = doc.scenes.filter(s => (s.footage || {}).type === "graphic" && (!only || String(s.id) === only));
  if (!targets.length) { console.log("graphic 씬 없음"); return; }
  const browser = htmlOnly ? null : await launch();
  let fail = 0;
  for (const sc of targets) {
    const g = (sc.footage || {}).graphic;
    if (!g || !g.kind) { console.error(`  ⛔ 씬${sc.id}: footage.graphic.kind 없음`); fail++; continue; }
    if (!g.source) console.error(`  ⚠️ 씬${sc.id}: graphic.source 없음 — preflight [GFX-SOURCE]에서 막힌다`);
    const base = path.join(outDir, `scene_${sc.id}`);
    try {
      const html = await htmlFor(g);
      if (htmlOnly) { fs.writeFileSync(base + ".html", html); console.log(`  📝 씬${sc.id} ${g.kind} → ${base}.html`); continue; }
      await render(browser, html, base);
      const rec = { scene_id: sc.id, kind: g.kind, title: g.title || "", video: base + ".mp4", png: base + "@2x.png" };
      const k = index.findIndex(x => x.scene_id === sc.id);
      if (k >= 0) index[k] = rec; else index.push(rec);
      console.log(`  ✓ 씬${sc.id} ${g.kind} → scene_${sc.id}.mp4 / @2x.png`);
    } catch (e) { console.error(`  ⛔ 씬${sc.id} ${g.kind}: ${e.message}`); fail++; }
  }
  if (browser) await browser.close();
  fs.writeFileSync(idxPath, JSON.stringify(index, null, 2));
  console.log(`✅ graphics/index.json ${index.length}건${fail ? ` · 실패 ${fail}` : ""}`);
  process.exit(fail ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
