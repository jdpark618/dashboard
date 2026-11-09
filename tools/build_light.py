"""index.html(다크) → light.html(라이트) 자동 생성. 직접 light.html 을 고치지 말고 여기 색 표를 고친다.
커밋할 때 .git/hooks/pre-commit 이 실행해 light.html 을 함께 커밋한다.
방식: 다크 전용으로 박힌 색(CSS·스크립트·Tailwind 설정)을 라이트 값으로 일괄 치환 — 다크 화면은 전혀 건드리지 않음.
실행: python tools/build_light.py  (저장소 루트에서)"""
import re, os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, dst = os.path.join(root, 'index.html'), os.path.join(root, 'light.html')
s = open(src, encoding='utf-8').read()

def once(a, b):
    global s
    assert s.count(a) == 1, f'build_light: 찾을 수 없음 → {a[:60]}'
    s = s.replace(a, b)

# 0) 이 파일은 라이트
once("const PAGE_THEME = 'dark';", "const PAGE_THEME = 'light';")
once('<head>', '<head>\n<!-- 자동 생성 파일: tools/build_light.py 가 index.html 에서 만듦. 직접 고치지 말 것 -->')

# 1) Tailwind 색: slate(뉴트럴)는 밝기를 뒤집고, 다크에서 글자용으로 쓰던 밝은 의미색(200~400)은 진하게
once("slate: { 50:'#f7f8f8', 100:'#e8eaed', 200:'#dfe1e3', 300:'#c3c7ca', 400:'#a0a7ad', 500:'#6f767b', 600:'#50575c', 700:'#343a3e', 800:'#292f33', 900:'#202428', 950:'#16191c' }",
     "slate: { 50:'#0f172a', 100:'#1e293b', 200:'#273449', 300:'#334155', 400:'#64748b', 500:'#94a3b8', 600:'#cbd5e1', 700:'#e2e8f0', 800:'#f1f5f9', 900:'#ffffff', 950:'#f7f8fa' }, " + ", ".join(
         f"{k}: {{ 200:'{a}', 300:'{a}', 400:'{b}' }}" for k, a, b in [
             ('amber', '#b45309', '#d97706'), ('emerald', '#047857', '#059669'), ('rose', '#be123c', '#e11d48'), ('red', '#b91c1c', '#dc2626'),
             ('sky', '#0369a1', '#0284c7'), ('teal', '#0f766e', '#0d9488'), ('violet', '#6d28d9', '#7c3aed'), ('blue', '#1d4ed8', '#2563eb'),
             ('green', '#15803d', '#16a34a'), ('yellow', '#a16207', '#ca8a04'), ('orange', '#c2410c', '#ea580c'), ('cyan', '#0e7490', '#0891b2'), ('pink', '#be185d', '#db2777')]))
once("indigo: { 100:'#e6e3ff', 200:'#d2ccff', 300:'#bdb5ff', 400:'#a59aff', 500:'#7d72f0', 600:'#6257e8', 700:'#5046c8', 800:'#3d3690', 900:'#302d4d' }",
     "indigo: { 100:'#2e2878', 200:'#3d3690', 300:'#4b40c8', 400:'#5b4fe0', 500:'#6257e8', 600:'#6257e8', 700:'#5046c8', 800:'#ddd8ff', 900:'#ece9ff' }")

# 1-1) 주간 리포트 결과물(A4 쪽)은 인쇄·PDF로 나가므로 다크 버전과 똑같이 — 색 변환에서 빼 두었다가 마지막에 되돌림
#      · CSS: '.rp-' 규칙 줄 (불러오는 중 표시 .rp-load 는 화면 일부라 변환)
#      · 스크립트: 리포트 그리는 부분 (RP_CLASSES ~ applyRankData 앞)
KEEP = []
def keep(m):
    KEEP.append(m.group(0)); return f'\x00KEEP{len(KEEP) - 1}\x00'
s = re.sub(r'^[^\n]*(?:\.rp-(?!load)|#reportPages|#rpPrintPages)[^\n]*$', keep, s, flags=re.M)   # 리포트 색 변수(--ink·--mute 등) 줄 포함
s = re.sub(r"const RP_CLASSES = .*?(?=function applyRankData\()", keep, s, flags=re.S)
assert len(KEEP) > 40, f'build_light: 리포트 보호 구간이 너무 적음 ({len(KEEP)})'

# 2) 직접 쓴 색 (CSS · 스크립트 안 인라인 색 모두)
HEX = {
    # 뉴트럴: 배경 → 흰/연회색, 글자 → 진회색
    '#15191c': '#f1f5f9', '#16191c': '#eef2f6', '#191d20': '#f7f8fa', '#1b1f22': '#f8fafc', '#1b2024': '#ffffff', '#1e2327': '#fafbfc',
    '#202428': '#ffffff', '#202529': '#ffffff', '#22272b': '#f8fafc', '#25292d': '#f8fafc', '#292e32': '#f8fafc', '#292f33': '#f1f5f9',
    '#2b3034': '#eef2f6', '#2b3236': '#e8ecf2', '#343a3e': '#e2e8f0', '#50575c': '#cbd5e1', '#6f767b': '#94a3b8', '#8a9298': '#64748b',
    '#929ba1': '#64748b', '#a0a7ad': '#64748b', '#c3c7ca': '#334155', '#dfe1e3': '#273449', '#e8eaed': '#1e293b', '#f7f8f8': '#0f172a',
    # 보라: 다크 바탕 위 밝은 보라 글자 → 진한 보라, 보라 틴트 바탕 → 연보라
    '#a59aff': '#5b4fe0', '#d2ccff': '#4b40c8', '#bdb5ff': '#4b40c8', '#302d4d': '#ece9ff',
    # 의미색 (매출·인기·상승·하락·신작 등): 흰 바탕에서 읽히는 진한 값
    '#fbbf24': '#d97706', '#2dd4bf': '#0d9488', '#f87171': '#dc2626', '#60a5fa': '#2563eb', '#a78bfa': '#7c3aed', '#fb7185': '#e11d48',
    '#34d399': '#059669', '#86efac': '#15803d', '#fcd34d': '#b45309', '#fde68a': '#92400e', '#93c5fd': '#1d4ed8', '#fca5a5': '#b91c1c',
    '#c4b5fd': '#6d28d9', '#99f6e4': '#0f766e', '#38bdf8': '#0284c7', '#22d3ee': '#0891b2', '#f59e0b': '#d97706', '#a3e635': '#4d7c0f',
}
s = re.sub(r'#[0-9a-fA-F]{6}\b', lambda m: HEX.get(m.group(0).lower(), m.group(0)), s)
RGBA = {
    '52,58,62': '226,232,240', '41,47,51': '241,245,249', '32,36,40': '255,255,255', '80,87,92': '203,213,225', '160,167,173': '100,116,139',
    '25,29,32': '247,248,250', '111,118,123': '148,163,184',
    '251,191,36': '217,119,6', '45,212,191': '13,148,136', '248,113,113': '220,38,38', '96,165,250': '37,99,235', '167,139,250': '124,58,237',
    '165,154,255': '91,79,224', '189,181,255': '91,79,224', '245,158,11': '217,119,6',
}
s = re.sub(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', lambda m: 'rgba(' + RGBA.get(f'{m.group(1)},{m.group(2)},{m.group(3)}', f'{m.group(1)},{m.group(2)},{m.group(3)}'), s)

# 2-0) 그림자: 다크용 진한 검정 그림자(rgba(0,0,0,.3~.6))는 흰 바탕에서 얼룩처럼 보이므로 남색 계열로 1/5 세기
def soft(m):
    return re.sub(r'rgba\(0,\s*0,\s*0,\s*([.\d]+)\)', lambda a: f'rgba(15,23,42,{round(float(a.group(1)) * .2, 3)})', m.group(0))
s = re.sub(r'box-shadow:[^;}]*', soft, s)

# 2-1) 흰 글자: 흰 바탕에서 안 보이는 곳만 진하게 (빨강 배지 위 흰 글자 · 주간 리포트는 그대로)
s = s.replace('color:#ffffff', 'color:#2e2878')
s = '\n'.join(l if ('hd-new' in l or 'rp-' in l) else re.sub(r'color:#fff\b', 'color:#0f172a', l) for l in s.split('\n'))
s = s.replace('hover:text-white', 'hover:text-slate-50')
once("ctx.fillStyle = p.hl ? '#ffffff'", "ctx.fillStyle = p.hl ? '#0f172a'")

# 3) 그 밖의 다크 전용 설정
once('color-scheme: dark;', 'color-scheme: light;')
once('<meta name="theme-color" content="#f7f8fa">', '<meta name="theme-color" content="#ffffff">')
# 그림자는 흰 바탕에서 훨씬 옅게 · 로고 타일은 원래 연보라 · 애플 아이콘은 선택된(보라) 버튼 위에서 흰색
once('</head>', """<style>/* 라이트 보정 (tools/build_light.py) */
#gdCty .mk-seg button i.fa-brands { color:inherit !important; }   /* 상세 패널 스토어 버튼 아이콘 = 대시보드 스토어 선택과 같은 색 (선택 흰색 · 기본 회색) */
.gl-flag { box-shadow:0 0 0 1px rgba(15,23,42,.10), 0 1px 2px rgba(15,23,42,.14); }   /* 흰 바탕 국기(일본 등)가 배경에 묻히지 않게 */
.sb-logo { background:#ece9ff !important; color:#3d3690 !important; }
:root { --line:#e8ecf2; }
.top-bar { background:#ffffff !important; }
.card { background:#ffffff; border:1px solid #e8ecf2; box-shadow:0 1px 2px rgba(15,23,42,.03); }
#detailPanel, #releaseDetailPanel { box-shadow:0 1px 2px rgba(15,23,42,.03); }
/* Tailwind 그림자(shadow-lg · shadow-black/30 등)도 옅게 — 일간 순위 필터바 등 */
.shadow-lg { box-shadow:0 1px 2px rgba(15,23,42,.03) !important; }
#rankTools { border:1px solid #e8ecf2; }
/* 테마 스위치: 밝은 바탕 위 흰 캡슐 */
.theme-seg { background:#eef2f6; border-color:#e2e8f0; } .theme-seg .ts-knob { background:#ffffff; box-shadow:0 1px 2px rgba(15,23,42,.12); }
#detailPanel:not(.translate-x-full) { box-shadow:-12px 0 32px rgba(16,24,40,.12) !important; }
.mk-seg button.on .fa-apple, .mk-seg button.on .text-slate-100 { color:#fff !important; }
/* 게임 상세 국가 × 스토어 표: 흰 표 + 회색 머리글 + 또렷한 칸 구분 (다크의 톤온톤을 그대로 뒤집으면 머리글·본문이 같은 회색이 됨) */
:is(#detailPanel) .gd-ctab { background:#fff !important; box-shadow:0 0 0 1px #e8ecf2; }
.gd-ctab thead th { background:#f8fafc; color:#64748b; }
.gd-ctab2 th.gd-sh { color:#1e293b; }
.gd-ctab2 tbody td { border-top:1px solid #eef2f6; }
.gd-ctab2 td:first-child { background:#fbfcfd; }
.gd-ctab2 td.on { background:#f1efff !important; }
</style>
</head>""")
# 4) 글자만 따뜻한 회색 (11/04 노션풍에서 유지) — 바탕·선은 1안 무채색(쿨 그레이) 그대로 둠 (11/05)
WARM = {'#0f172a': '#37352f', '#1e293b': '#37352f', '#273449': '#45433d', '#334155': '#55534e', '#64748b': '#787774', '#94a3b8': '#a5a4a0'}
s = re.sub(r'#[0-9a-fA-F]{6}\b', lambda m: WARM.get(m.group(0).lower(), m.group(0)), s)
WARM_RGBA = {'100,116,139': '120,119,116', '148,163,184': '165,164,160'}
s = re.sub(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', lambda m: 'rgba(' + WARM_RGBA.get(f'{m.group(1)},{m.group(2)},{m.group(3)}', f'{m.group(1)},{m.group(2)},{m.group(3)}'), s)
s = s.replace('border-bottom:1px solid rgba(241,245,249,.8)', 'border-bottom:1px solid #eceef1')   # 카드 머리·달력 행 구분선: 흰 카드 위에서도 보이게
once('</head>', """<style>/* 프레임 (tools/build_light.py, 11/05 1안) — 본문 바탕 아주 연한 회색 + 카드 흰색 + 얇은 테두리, 글자는 따뜻한 회색 유지 */
body, main { background:#f6f7f9 !important; }
.top-bar { background:#ffffff !important; }
.side-nav { background:#ffffff !important; }   /* 틀(로고·상단 바·메뉴) = 흰색 한 톤, 본문만 연회색 */
.card { background:#ffffff !important; border-color:#e6e8ed !important; box-shadow:none !important; transition:box-shadow .15s; }
.card:hover { box-shadow:0 2px 8px rgba(15,23,42,.05) !important; }   /* 그림자는 마우스를 올렸을 때만 약하게 */
.card thead.bg-slate-900 { background:#ffffff !important; }   /* 카드 안 고정 표 머리 = 카드 색 */
.inbox { background:#f4f6f9 !important; }   /* 카드 안의 카드: 흰 카드 위 연회색 면 + 아주 옅은 테두리 (11/09) */
.inbox:not(.border-indigo-500):not([class*="hover:border"]:hover) { border-color:#eef0f4 !important; }
.inbox .bg-slate-950 { background-color:#e7eaef !important; }
.gd-ctab2 thead tr:first-child th.gd-sh { border-bottom-color:#e3e5ea !important; }   /* 상세 표: 스토어 이름 줄 ↔ 매출·인기 줄 구분선 */
.gs-tab.on { background:#5046c8 !important; color:#ffffff !important; }   /* 순위 비교 검색 드롭다운 탭: 다른 선택 버튼과 같은 진한 보라 + 흰 글자 (다크용 흰 글자가 연보라 위에서 안 보이던 것) */
.cal-navbtn, .cal-today-btn, .more-btn { background:#ffffff !important; border-color:#e6e8ed !important; }   /* 달력 이전/다음 · 오늘 · 목록/더보기 버튼: 페이지 배경(#f6f7f9)에 묻혀서 카드처럼 흰 바탕 + 테두리 (11/06) */
.cal-navbtn:hover, .cal-today-btn:hover, .more-btn:hover { border-color:#5046c8 !important; }
.rank-chip { background:#f6f7f9 !important; border-color:#e6e8ed !important; color:#37352f !important; }   /* 흰 카드 안 순위 칩: 연회색 칩 */
.summary-card-hover:hover, .wl-row:hover, .cal-row:hover, [class*="hover:bg-slate-8"]:hover { background:#f8f9fb !important; }   /* 행 Hover */
:root { --line:#e6e8ed !important; }
.card-hd, .cal-row { border-bottom-color:#eceef1 !important; }
/* 선: 원래 라이트에서 안 보이던 흰 선은 계속 안 보이게, 보이던 선만 같은 대비로 */
[class*="border-slate-9"] { border-color:transparent !important; }
[class*="divide-slate-9"] > :not(:first-child) { border-color:transparent !important; }
[class*="border-slate-8"] { border-color:#eceef1 !important; }
[class*="border-slate-7"] { border-color:#e3e5ea !important; }
</style>
</head>""")
s = re.sub(r'\x00KEEP(\d+)\x00', lambda m: KEEP[int(m.group(1))], s)   # 리포트 구간 원래대로 (모든 변환이 끝난 뒤)
open(dst, 'w', encoding='utf-8', newline='\n').write(s)
print(f'light.html 생성 ({len(s):,}자)')
