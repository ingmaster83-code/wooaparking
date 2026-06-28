"""
generate_sub_pages.py
======================
구/군 단위, 동/읍/면 단위 주차장 페이지 자동 생성
+ 시도 페이지에 구 네비게이션 추가

실행: python scripts/generate_sub_pages.py
"""

import json, re, sys
from pathlib import Path
from datetime import date
from collections import defaultdict

try:
    from jinja2 import Environment, BaseLoader
except ImportError:
    print("pip install jinja2"); raise

ROOT       = Path(__file__).parent.parent
DATA_DIR   = ROOT / "docs" / "data" / "parking"
PAGES_DIR  = ROOT / "docs" / "지역"
SITEMAP_OUT = ROOT / "docs" / "sitemap.xml"
TODAY      = date.today().isoformat()
BASE_URL   = "https://wooaparking.wooahouse.com"

MIN_DONG_RECORDS = 3   # 동 페이지 생성 최소 주차장 수
MIN_GU_RECORDS   = 1

SIDO_SHORT = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북",
    "경상남도": "경남", "제주특별자치도": "제주",
}

# ── 주소 파싱 ─────────────────────────────────────
def parse_gu_dong(address, sido):
    """주소에서 구/군(시) and 동/읍/면 추출"""
    if not address:
        return None, None
    addr = address.replace(sido, '', 1).strip()
    tokens = addr.split()

    gu = None
    dong = None
    for token in tokens:
        # 숫자·특수문자 포함 토큰은 번지수이므로 중단
        if re.search(r'\d', token):
            break
        if re.search(r'(구|군)$', token):
            gu = token           # 구/군이 나오면 업데이트 (시 위에 구가 있는 경우)
        elif re.search(r'시$', token) and not gu:
            gu = token           # 도 내 시 (이천시, 의왕시 등)
        elif re.search(r'(동|읍|면)$', token):
            dong = token
            break
    return gu, dong


# ── 데이터 로드 및 분류 ───────────────────────────
def build_hierarchy():
    """
    Returns:
        {sido: {gu: {dong: [records]}}}
    """
    hierarchy = {}
    for f in sorted(DATA_DIR.glob("*.json")):
        sido = f.stem
        if sido not in SIDO_SHORT:
            continue
        with open(f, encoding='utf-8') as fp:
            records = json.load(fp).get('records', [])

        gu_map = defaultdict(lambda: defaultdict(list))
        no_gu = []
        for r in records:
            addr = r.get('소재지지번주소') or r.get('소재지도로명주소') or ''
            gu, dong = parse_gu_dong(addr, sido)
            if gu:
                dong_key = dong or '__기타__'
                gu_map[gu][dong_key].append(r)
            else:
                no_gu.append(r)

        hierarchy[sido] = {
            'records': records,
            'gu_map': {g: dict(dm) for g, dm in gu_map.items()},
            'no_gu': no_gu,
        }
        print(f"  [{sido}] {len(records):,}건 → {len(gu_map)}개 구/군")
    return hierarchy


# ══════════════════ HTML 템플릿 ══════════════════ #

# ── 시도 페이지 (구 네비 추가 버전) ──────────────
SIDO_TMPL = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ short }} 공영주차장 {{ count }}개 목록 — 위치·요금·운영시간 | 우아파킹</title>
  <meta name="description" content="{{ sido }} 공영주차장 {{ count }}개 위치와 요금을 한눈에. 노상·노외·무료 주차장을 지도에서 바로 확인하세요.">
  <meta name="keywords" content="{{ short }} 공영주차장,{{ short }} 무료주차장,{{ short }} 주차장 요금,{{ short }} 주차장 위치,{{ short }} 노상주차장,{{ short }} 노외주차장">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{{ base_url }}/지역/{{ sido }}.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{ short }} 공영주차장 {{ count }}개 목록 | 우아파킹">
  <meta property="og:description" content="{{ sido }} 공영주차장 {{ count }}개 위치, 요금, 운영시간 안내">
  <meta property="og:url" content="{{ base_url }}/지역/{{ sido }}.html">
  <meta name="twitter:card" content="summary">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"CollectionPage",
   "name":"{{ short }} 공영주차장 목록","url":"{{ base_url }}/지역/{{ sido }}.html",
   "description":"{{ sido }} 공영주차장 {{ count }}개 위치, 요금, 운영시간"}
  </script>
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="../" class="site-logo"><span class="logo-icon">🅿️</span><span class="logo-text">우아파킹</span></a>
    <nav class="header-nav">
      <a href="../">주차장 찾기</a>
      <a href="./" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
</header>

<section class="region-hero">
  <nav class="breadcrumb-hero">
    <a href="../">홈</a> <span>›</span> <span>지역별</span> <span>›</span> <span>{{ sido }}</span>
  </nav>
  <h1>🅿️ {{ sido }} 공영주차장</h1>
  <p class="sub">{{ count }}개 공영주차장 위치, 요금, 운영시간을 확인하세요</p>
  <p class="keywords">{{ short }} 공영주차장 · {{ short }} 무료주차장 · {{ short }} 주차요금 · {{ short }} 노상주차장</p>
  <div class="region-search-bar">
    <input type="text" id="regionSearchInput" placeholder="주차장명 또는 주소 검색">
    <button id="regionSearchBtn">검색</button>
  </div>
</section>

<!-- 구/군 네비게이션 -->
<div class="sub-nav-bar">
  <div class="sub-nav-inner">
    <span class="sub-nav-label">{{ short }} 구/군 선택</span>
    <div class="sub-nav-btns">
      {% for gu in gu_list %}<a href="{{ sido }}/{{ gu }}.html" class="btn-sub-nav">{{ gu }}</a>{% endfor %}
    </div>
  </div>
</div>

<div class="tab-bar">
  <div class="tab-inner">
    <button class="tab-btn active" data-tab="전체">전체 <span class="tab-cnt">{{ count }}</span></button>
    <button class="tab-btn" data-tab="노상">노상주차장</button>
    <button class="tab-btn" data-tab="노외">노외주차장</button>
    <button class="tab-btn" data-tab="부설">부설주차장</button>
    <button class="tab-btn" data-tab="무료">무료</button>
  </div>
</div>

<div class="tab-bottom-ad">
  <ins class="adsbygoogle" style="display:inline-block;width:728px;max-width:100%;height:90px"
       data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins>
</div>

<div class="region-layout">
  <div class="region-list-col">
    <div class="result-header">
      <div class="result-count">총 <strong id="listCount">{{ count }}</strong>개</div>
      <a href="../" class="result-back">← 전국 검색</a>
    </div>
    <div id="parkingList"><div class="loading-state"><div class="spinner"></div><br>불러오는 중...</div></div>
    <div id="loadMore" style="text-align:center;margin:20px 0;display:none;">
      <button id="loadMoreBtn" style="padding:10px 28px;background:var(--primary);color:#fff;border-radius:8px;font-size:.9rem;font-weight:600;">더 보기</button>
    </div>
  </div>
  <div class="region-aside">
    <div id="region-map"><div class="map-placeholder"><div class="icon">🗺️</div><p>지도 로딩 중...</p></div></div>
    <div class="mid-ad" style="margin-top:16px;min-height:600px;">
      <div class="ad-label">📢 광고</div>
      <ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins>
    </div>
  </div>
</div>

<section class="seo-section">
  <h2>{{ sido }} 공영주차장 안내</h2>
  <p>{{ sido }}의 공영주차장은 총 {{ count }}개소로 노상·노외·부설주차장으로 구분됩니다.
  {{ short }} 공영주차장은 민영 대비 저렴한 요금으로 이용 가능하며,
  {{ gu_seo_text }} 등 각 지역별 공영주차장 정보를 확인하세요.
  {{ short }} 무료주차장은 요금 필터로 빠르게 확인할 수 있습니다.</p>
</section>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col"><p class="footer-logo">🅿️ 우아파킹</p><p>전국 공영주차장 정보<br>설치 불필요 · 로그인 불필요</p><a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a></div>
      <div class="footer-col"><p class="footer-heading">{{ short }} 구/군별</p>{% for gu in gu_list[:6] %}<a href="{{ sido }}/{{ gu }}.html">{{ gu }}</a>{% endfor %}</div>
      <div class="footer-col"><p class="footer-heading">다른 지역</p><a href="서울특별시.html">서울특별시</a><a href="경기도.html">경기도</a><a href="부산광역시.html">부산광역시</a><a href="인천광역시.html">인천광역시</a><a href="대구광역시.html">대구광역시</a></div>
      <div class="footer-col"><p class="footer-heading">정보</p><a href="../privacy.html">개인정보처리방침</a><a href="../">메인으로</a></div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p><p>데이터 출처: 공공데이터포털 전국주차장정보표준데이터</p></div>
  </div>
</footer>

<script src="../js/config.js"></script>
<script>
  const PARKING_DATA_URL = '../data/parking/{{ sido }}.json';
  const REGION_NAME = '{{ sido }}';
  const REGION_SHORT = '{{ short }}';
</script>
<script src="../js/region.js"></script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</body>
</html>
"""

# ── 구/군 페이지 ──────────────────────────────────
GU_TMPL = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ gu }} 공영주차장 {{ count }}개 — 위치·요금·운영시간 | 우아파킹</title>
  <meta name="description" content="{{ gu }} 공영주차장 {{ count }}개 위치와 요금 안내. {{ dong_sample }} 등 {{ gu }} 전체 공영·무료 주차장 정보를 지도에서 확인하세요.">
  <meta name="keywords" content="{{ gu }} 공영주차장,{{ gu }} 무료주차장,{{ gu }} 주차장 요금,{{ gu }} 주차장 위치,{{ sido_short }} {{ gu }} 주차장">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{{ base_url }}/지역/{{ sido }}/{{ gu }}.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{ gu }} 공영주차장 {{ count }}개 | 우아파킹">
  <meta property="og:description" content="{{ gu }} 공영주차장 {{ count }}개 위치, 요금, 운영시간">
  <meta property="og:url" content="{{ base_url }}/지역/{{ sido }}/{{ gu }}.html">
  <meta name="twitter:card" content="summary">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../css/style.css">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"CollectionPage",
   "name":"{{ gu }} 공영주차장 목록","url":"{{ base_url }}/지역/{{ sido }}/{{ gu }}.html",
   "description":"{{ gu }} 공영주차장 {{ count }}개 위치, 요금, 운영시간"}
  </script>
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="../../" class="site-logo"><span class="logo-icon">🅿️</span><span class="logo-text">우아파킹</span></a>
    <nav class="header-nav">
      <a href="../../">주차장 찾기</a>
      <a href="../" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
</header>

<section class="region-hero">
  <nav class="breadcrumb-hero">
    <a href="../../">홈</a> <span>›</span> <a href="../{{ sido }}.html">{{ sido }}</a> <span>›</span> <span>{{ gu }}</span>
  </nav>
  <h1>🅿️ {{ gu }} 공영주차장</h1>
  <p class="sub">{{ count }}개 공영주차장 위치, 요금, 운영시간을 확인하세요</p>
  <p class="keywords">{{ gu }} 공영주차장 · {{ gu }} 무료주차장 · {{ gu }} 주차요금 · {{ sido_short }} {{ gu }} 주차장</p>
  <div class="region-search-bar">
    <input type="text" id="regionSearchInput" placeholder="주차장명 또는 동 이름 검색">
    <button id="regionSearchBtn">검색</button>
  </div>
</section>

<!-- 동/읍/면 네비게이션 -->
<div class="sub-nav-bar">
  <div class="sub-nav-inner">
    <span class="sub-nav-label">{{ gu }} 동/읍/면</span>
    <div class="sub-nav-btns">
      {% for dong, cnt in dong_list %}<a href="{{ gu }}/{{ dong }}.html" class="btn-sub-nav">{{ dong }} <span class="sub-cnt">{{ cnt }}</span></a>{% endfor %}
    </div>
  </div>
</div>

<div class="tab-bar">
  <div class="tab-inner">
    <button class="tab-btn active" data-tab="전체">전체 <span class="tab-cnt">{{ count }}</span></button>
    <button class="tab-btn" data-tab="노상">노상주차장</button>
    <button class="tab-btn" data-tab="노외">노외주차장</button>
    <button class="tab-btn" data-tab="부설">부설주차장</button>
    <button class="tab-btn" data-tab="무료">무료</button>
  </div>
</div>

<div class="tab-bottom-ad">
  <ins class="adsbygoogle" style="display:inline-block;width:728px;max-width:100%;height:90px"
       data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins>
</div>

<div class="region-layout">
  <div class="region-list-col">
    <div class="result-header">
      <div class="result-count">총 <strong id="listCount">{{ count }}</strong>개</div>
      <a href="../{{ sido }}.html" class="result-back">← {{ sido }}</a>
    </div>
    <div id="parkingList"><div class="loading-state"><div class="spinner"></div><br>불러오는 중...</div></div>
    <div id="loadMore" style="text-align:center;margin:20px 0;display:none;">
      <button id="loadMoreBtn" style="padding:10px 28px;background:var(--primary);color:#fff;border-radius:8px;font-size:.9rem;font-weight:600;">더 보기</button>
    </div>
  </div>
  <div class="region-aside">
    <div id="region-map"><div class="map-placeholder"><div class="icon">🗺️</div><p>지도 로딩 중...</p></div></div>
    <div class="mid-ad" style="margin-top:16px;min-height:600px;">
      <div class="ad-label">📢 광고</div>
      <ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins>
    </div>
  </div>
</div>

<section class="seo-section">
  <h2>{{ gu }} 공영주차장 안내</h2>
  <p>{{ gu }} 공영주차장은 총 {{ count }}개소로, {{ dong_sample }} 등에 분포합니다.
  {{ gu }} 무료주차장 및 유료 공영주차장 요금과 운영시간을 위 목록에서 확인하시고,
  지도보기·길찾기로 바로 이동하세요. {{ sido_short }} {{ gu }} 주차장 요금은 민영 대비 저렴합니다.</p>
</section>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col"><p class="footer-logo">🅿️ 우아파킹</p><p>전국 공영주차장 정보<br>설치 불필요 · 로그인 불필요</p><a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a></div>
      <div class="footer-col"><p class="footer-heading">{{ gu }} 동/읍/면</p>{% for dong, cnt in dong_list[:6] %}<a href="{{ gu }}/{{ dong }}.html">{{ dong }}</a>{% endfor %}</div>
      <div class="footer-col"><p class="footer-heading">{{ sido }}</p><a href="../{{ sido }}.html">{{ sido }} 전체</a>{% for g, _ in sibling_gu[:5] %}<a href="{{ g }}.html">{{ g }}</a>{% endfor %}</div>
      <div class="footer-col"><p class="footer-heading">정보</p><a href="../../privacy.html">개인정보처리방침</a><a href="../../">메인으로</a></div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p><p>데이터 출처: 공공데이터포털 전국주차장정보표준데이터</p></div>
  </div>
</footer>

<script src="../../js/config.js"></script>
<script>
  const PARKING_RECORDS = {{ records_json }};
  const REGION_NAME = '{{ gu }}';
  const REGION_SHORT = '{{ gu }}';
</script>
<script src="../../js/region.js"></script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</body>
</html>
"""

# ── 동/읍/면 페이지 ───────────────────────────────
DONG_TMPL = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ dong }} 공영주차장 {{ count }}개 — 위치·요금·운영시간 | 우아파킹</title>
  <meta name="description" content="{{ gu }} {{ dong }} 공영주차장 {{ count }}개 위치와 요금 안내. {{ dong }} 무료주차장, 노상·노외 주차장 정보를 지도에서 바로 확인하세요.">
  <meta name="keywords" content="{{ dong }} 공영주차장,{{ dong }} 주차장,{{ dong }} 무료주차장,{{ gu }} {{ dong }} 주차장,{{ sido_short }} {{ dong }} 공영주차장">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{{ base_url }}/지역/{{ sido }}/{{ gu }}/{{ dong }}.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{ dong }} 공영주차장 {{ count }}개 | 우아파킹">
  <meta property="og:description" content="{{ gu }} {{ dong }} 공영주차장 {{ count }}개 위치, 요금, 운영시간">
  <meta property="og:url" content="{{ base_url }}/지역/{{ sido }}/{{ gu }}/{{ dong }}.html">
  <meta name="twitter:card" content="summary">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../../../css/style.css">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"CollectionPage",
   "name":"{{ dong }} 공영주차장 목록","url":"{{ base_url }}/지역/{{ sido }}/{{ gu }}/{{ dong }}.html",
   "description":"{{ gu }} {{ dong }} 공영주차장 {{ count }}개 위치, 요금, 운영시간"}
  </script>
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <a href="../../../" class="site-logo"><span class="logo-icon">🅿️</span><span class="logo-text">우아파킹</span></a>
    <nav class="header-nav">
      <a href="../../../">주차장 찾기</a>
      <a href="../../" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
</header>

<section class="region-hero">
  <nav class="breadcrumb-hero">
    <a href="../../../">홈</a> <span>›</span>
    <a href="../../{{ sido }}.html">{{ sido }}</a> <span>›</span>
    <a href="../{{ gu }}.html">{{ gu }}</a> <span>›</span>
    <span>{{ dong }}</span>
  </nav>
  <h1>🅿️ {{ dong }} 공영주차장</h1>
  <p class="sub">{{ count }}개 공영주차장 위치, 요금, 운영시간을 확인하세요</p>
  <p class="keywords">{{ dong }} 공영주차장 · {{ dong }} 무료주차장 · {{ gu }} {{ dong }} 주차장</p>
  <div class="region-search-bar">
    <input type="text" id="regionSearchInput" placeholder="주차장명 또는 주소 검색">
    <button id="regionSearchBtn">검색</button>
  </div>
</section>

<!-- 같은 구의 다른 동 네비게이션 -->
<div class="sub-nav-bar">
  <div class="sub-nav-inner">
    <span class="sub-nav-label">{{ gu }} 다른 동</span>
    <div class="sub-nav-btns">
      {% for d, cnt in sibling_dong %}<a href="{{ d }}.html" class="btn-sub-nav {% if d == dong %}active{% endif %}">{{ d }} <span class="sub-cnt">{{ cnt }}</span></a>{% endfor %}
    </div>
  </div>
</div>

<div class="tab-bar">
  <div class="tab-inner">
    <button class="tab-btn active" data-tab="전체">전체 <span class="tab-cnt">{{ count }}</span></button>
    <button class="tab-btn" data-tab="노상">노상주차장</button>
    <button class="tab-btn" data-tab="노외">노외주차장</button>
    <button class="tab-btn" data-tab="부설">부설주차장</button>
    <button class="tab-btn" data-tab="무료">무료</button>
  </div>
</div>

<div class="tab-bottom-ad">
  <ins class="adsbygoogle" style="display:inline-block;width:728px;max-width:100%;height:90px"
       data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins>
</div>

<div class="region-layout">
  <div class="region-list-col">
    <div class="result-header">
      <div class="result-count">총 <strong id="listCount">{{ count }}</strong>개</div>
      <a href="../{{ gu }}.html" class="result-back">← {{ gu }}</a>
    </div>
    <div id="parkingList"><div class="loading-state"><div class="spinner"></div><br>불러오는 중...</div></div>
    <div id="loadMore" style="text-align:center;margin:20px 0;display:none;">
      <button id="loadMoreBtn" style="padding:10px 28px;background:var(--primary);color:#fff;border-radius:8px;font-size:.9rem;font-weight:600;">더 보기</button>
    </div>
  </div>
  <div class="region-aside">
    <div id="region-map"><div class="map-placeholder"><div class="icon">🗺️</div><p>지도 로딩 중...</p></div></div>
    <div class="mid-ad" style="margin-top:16px;min-height:600px;">
      <div class="ad-label">📢 광고</div>
      <ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px"
           data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins>
    </div>
  </div>
</div>

<section class="seo-section">
  <h2>{{ dong }} 공영주차장 안내</h2>
  <p>{{ gu }} {{ dong }}의 공영주차장은 총 {{ count }}개소입니다.
  {{ dong }} 무료주차장 및 유료 공영주차장 요금·운영시간을 위 목록에서 확인하시고,
  지도보기·길찾기 버튼으로 바로 이동하세요.
  {{ sido_short }} {{ gu }} 공영주차장 전체 목록은 <a href="../{{ gu }}.html">{{ gu }} 주차장 페이지</a>에서 확인하세요.</p>
</section>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col"><p class="footer-logo">🅿️ 우아파킹</p><p>전국 공영주차장 정보<br>설치 불필요 · 로그인 불필요</p><a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a></div>
      <div class="footer-col"><p class="footer-heading">{{ gu }} 다른 동</p>{% for d, cnt in sibling_dong[:6] %}<a href="{{ d }}.html">{{ d }}</a>{% endfor %}</div>
      <div class="footer-col"><p class="footer-heading">상위 지역</p><a href="../{{ gu }}.html">{{ gu }} 전체</a><a href="../../{{ sido }}.html">{{ sido }} 전체</a></div>
      <div class="footer-col"><p class="footer-heading">정보</p><a href="../../../privacy.html">개인정보처리방침</a><a href="../../../">메인으로</a></div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 WooaHouse. All rights reserved.</p><p>데이터 출처: 공공데이터포털 전국주차장정보표준데이터</p></div>
  </div>
</footer>

<script src="../../../js/config.js"></script>
<script>
  const PARKING_RECORDS = {{ records_json }};
  const REGION_NAME = '{{ dong }}';
  const REGION_SHORT = '{{ dong }}';
</script>
<script src="../../../js/region.js"></script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
</body>
</html>
"""


# ══════════════════ 생성 함수 ═══════════════════ #

env = Environment(loader=BaseLoader())

def generate_sido_pages(hierarchy):
    """시도 페이지 재생성 (구 네비 포함)"""
    tmpl = env.from_string(SIDO_TMPL)
    count = 0
    for sido, data in hierarchy.items():
        gu_list = sorted(data['gu_map'].keys())
        gu_seo_text = '·'.join(gu_list[:5])
        html = tmpl.render(
            sido=sido, short=SIDO_SHORT[sido],
            count=f"{len(data['records']):,}",
            gu_list=gu_list, gu_seo_text=gu_seo_text,
            base_url=BASE_URL,
        )
        out = PAGES_DIR / f"{sido}.html"
        out.write_text(html, encoding='utf-8')
        count += 1
    print(f"  시도 페이지 {count}개 재생성")
    return count


def generate_gu_pages(hierarchy):
    """구/군 단위 페이지 생성"""
    tmpl = env.from_string(GU_TMPL)
    total = 0
    for sido, data in hierarchy.items():
        gu_map = data['gu_map']
        sibling_gu = [(g, sum(len(v) for v in dm.values()))
                      for g, dm in sorted(gu_map.items())]

        for gu, dong_map in gu_map.items():
            records = []
            dong_list = []
            for dong, recs in sorted(dong_map.items()):
                if dong == '__기타__':
                    records.extend(recs)
                    continue
                records.extend(recs)
                if len(recs) >= MIN_DONG_RECORDS:
                    dong_list.append((dong, len(recs)))

            dong_list.sort(key=lambda x: -x[1])  # 많은 순
            dong_sample = '·'.join(d for d, _ in dong_list[:5])

            out_dir = PAGES_DIR / sido
            out_dir.mkdir(parents=True, exist_ok=True)

            html = tmpl.render(
                sido=sido, sido_short=SIDO_SHORT[sido],
                gu=gu, count=f"{len(records):,}",
                dong_list=dong_list, dong_sample=dong_sample,
                sibling_gu=[(g, c) for g, c in sibling_gu if g != gu],
                records_json=json.dumps(records, ensure_ascii=False),
                base_url=BASE_URL,
            )
            (out_dir / f"{gu}.html").write_text(html, encoding='utf-8')
            total += 1

    print(f"  구/군 페이지 {total}개 생성")
    return total


def generate_dong_pages(hierarchy):
    """동/읍/면 단위 페이지 생성"""
    tmpl = env.from_string(DONG_TMPL)
    total = 0
    skipped = 0
    for sido, data in hierarchy.items():
        for gu, dong_map in data['gu_map'].items():
            # 동 목록 (임계값 이상인 것만)
            valid_dongs = {d: r for d, r in dong_map.items()
                           if d != '__기타__' and len(r) >= MIN_DONG_RECORDS}
            sibling_dong = sorted([(d, len(r)) for d, r in valid_dongs.items()],
                                   key=lambda x: -x[1])

            for dong, records in valid_dongs.items():
                out_dir = PAGES_DIR / sido / gu
                out_dir.mkdir(parents=True, exist_ok=True)

                html = tmpl.render(
                    sido=sido, sido_short=SIDO_SHORT[sido],
                    gu=gu, dong=dong,
                    count=f"{len(records):,}",
                    sibling_dong=sibling_dong,
                    records_json=json.dumps(records, ensure_ascii=False),
                    base_url=BASE_URL,
                )
                (out_dir / f"{dong}.html").write_text(html, encoding='utf-8')
                total += 1
            skipped += len([d for d, r in dong_map.items()
                            if d != '__기타__' and len(r) < MIN_DONG_RECORDS])

    print(f"  동/읍/면 페이지 {total}개 생성 (thin content {skipped}개 제외)")
    return total


def generate_sitemap(hierarchy):
    """전체 sitemap.xml 재생성"""
    urls = [f"  <url><loc>{BASE_URL}/</loc><lastmod>{TODAY}</lastmod><priority>1.0</priority></url>"]

    for sido in sorted(hierarchy.keys()):
        urls.append(f"  <url><loc>{BASE_URL}/지역/{sido}.html</loc><lastmod>{TODAY}</lastmod><priority>0.8</priority></url>")
        gu_map = hierarchy[sido]['gu_map']
        for gu in sorted(gu_map.keys()):
            urls.append(f"  <url><loc>{BASE_URL}/지역/{sido}/{gu}.html</loc><lastmod>{TODAY}</lastmod><priority>0.7</priority></url>")
            for dong, recs in sorted(gu_map[gu].items()):
                if dong == '__기타__' or len(recs) < MIN_DONG_RECORDS:
                    continue
                urls.append(f"  <url><loc>{BASE_URL}/지역/{sido}/{gu}/{dong}.html</loc><lastmod>{TODAY}</lastmod><priority>0.6</priority></url>")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '\n'.join(urls) + '\n</urlset>\n'
    SITEMAP_OUT.write_text(xml, encoding='utf-8')
    url_count = len(urls)
    print(f"  sitemap.xml {url_count}개 URL")
    return url_count


def main():
    print("=" * 55)
    print("wooaparking 구/동 단위 페이지 생성기")
    print("=" * 55)

    print("\n[1/5] 데이터 로드 및 주소 파싱...")
    hierarchy = build_hierarchy()

    print("\n[2/5] 시도 페이지 재생성 (구 네비 추가)...")
    sido_cnt = generate_sido_pages(hierarchy)

    print("\n[3/5] 구/군 페이지 생성...")
    gu_cnt = generate_gu_pages(hierarchy)

    print("\n[4/5] 동/읍/면 페이지 생성...")
    dong_cnt = generate_dong_pages(hierarchy)

    print("\n[5/5] sitemap.xml 생성...")
    url_cnt = generate_sitemap(hierarchy)

    print(f"""
완료!
  시도  : {sido_cnt}개
  구/군 : {gu_cnt}개
  동/읍/면: {dong_cnt}개
  총 페이지: {sido_cnt + gu_cnt + dong_cnt}개
  sitemap: {url_cnt}개 URL
""")


if __name__ == "__main__":
    main()
