"""
generate_pages.py
=================
지역별 HTML 자동 생성 + sitemap.xml 생성 + JSON 복사

실행 방법:
  cd C:\\개인\\wooahouse\\wooaparking
  python scripts/generate_pages.py

필요 패키지:
  pip install jinja2 python-dotenv
"""

import json
import os
import shutil
from datetime import date
from pathlib import Path

try:
    from jinja2 import Environment, BaseLoader
except ImportError:
    print("jinja2가 설치되지 않았습니다. 실행: pip install jinja2")
    raise

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 없어도 환경변수 직접 설정 가능

ROOT = Path(__file__).parent.parent
DATA_SRC = ROOT / "data" / "parking"
DATA_DEST = ROOT / "docs" / "data" / "parking"
PAGES_DIR = ROOT / "docs" / "지역"
SITEMAP_OUT = ROOT / "docs" / "sitemap.xml"

KAKAO_APP_KEY = os.environ.get("KAKAO_MAP_KEY", "YOUR_KAKAO_APP_KEY_HERE")
TODAY = date.today().isoformat()
BASE_URL = "https://wooaparking.wooahouse.com"

# 시도 → 짧은 이름 (title용)
SIDO_SHORT = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북",
    "경상남도": "경남", "제주특별자치도": "제주",
}

# 지역 대표 좌표 (지도 초기 중심)
SIDO_CENTER = {
    "서울특별시":    (37.5665, 126.9780),
    "부산광역시":    (35.1796, 129.0756),
    "대구광역시":    (35.8714, 128.6014),
    "인천광역시":    (37.4563, 126.7052),
    "광주광역시":    (35.1595, 126.8526),
    "대전광역시":    (36.3504, 127.3845),
    "울산광역시":    (35.5384, 129.3114),
    "세종특별자치시": (36.4800, 127.2890),
    "경기도":        (37.4138, 127.5183),
    "강원특별자치도": (37.8228, 128.1555),
    "충청북도":      (36.6357, 127.4913),
    "충청남도":      (36.5184, 126.8000),
    "전북특별자치도": (35.7175, 127.1530),
    "전라남도":      (34.8679, 126.9910),
    "경상북도":      (36.4919, 128.8889),
    "경상남도":      (35.4606, 128.2132),
    "제주특별자치도": (33.4890, 126.4983),
}

REGION_PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ short }} 공영주차장 목록 — 위치 요금 운영시간 | 우아파킹</title>
  <meta name="description" content="{{ sido }} 공영주차장 {{ count }}개 위치와 요금, 운영시간을 확인하세요. 노상/노외 주차장 정보를 지도에서 바로 확인.">
  <meta name="keywords" content="{{ short }} 공영주차장,{{ short }} 무료주차장,{{ short }} 주차장 요금,{{ short }} 공영주차장 위치,{{ short }} 노상주차장,{{ short }} 노외주차장">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{{ base_url }}/지역/{{ sido }}.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{ short }} 공영주차장 목록 | 우아파킹">
  <meta property="og:description" content="{{ sido }} 공영주차장 {{ count }}개 위치, 요금, 운영시간 안내">
  <meta property="og:url" content="{{ base_url }}/지역/{{ sido }}.html">
  <meta name="twitter:card" content="summary">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "{{ short }} 공영주차장 목록",
    "description": "{{ sido }} 공영주차장 {{ count }}개 위치, 요금, 운영시간",
    "url": "{{ base_url }}/지역/{{ sido }}.html"
  }
  </script>
</head>
<body>

<header class="site-header">
  <div class="header-inner">
    <a href="../" class="site-logo">
      <span class="logo-icon">🅿️</span>
      <span class="logo-text">우아파킹</span>
    </a>
    <nav class="header-nav">
      <a href="../">주차장 찾기</a>
      <a href="./" class="active-nav">지역별</a>
      <a href="https://wooahouse.com" target="_blank" rel="noopener">WooaHouse →</a>
    </nav>
    <button class="mobile-menu-btn" aria-label="메뉴">☰</button>
  </div>
</header>

<!-- 히어로 -->
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

<!-- 탭 -->
<div class="tab-bar">
  <div class="tab-inner">
    <button class="tab-btn active" data-tab="전체">전체 <span class="tab-cnt">{{ count }}</span></button>
    <button class="tab-btn" data-tab="노상">노상주차장</button>
    <button class="tab-btn" data-tab="노외">노외주차장</button>
    <button class="tab-btn" data-tab="부설">부설주차장</button>
    <button class="tab-btn" data-tab="무료">무료</button>
  </div>
</div>

<!-- 탭 하단 배너 광고 -->
<div class="tab-bottom-ad">
  <ins class="adsbygoogle"
       style="display:inline-block;width:728px;max-width:100%;height:90px"
       data-ad-client="ca-pub-6464921081676309"
       data-ad-slot="7080296704"></ins>
</div>

<!-- 레이아웃 -->
<div class="region-layout">
  <!-- 목록 -->
  <div class="region-list-col">
    <div class="result-header">
      <div class="result-count">총 <strong id="listCount">{{ count }}</strong>개</div>
      <a href="../" class="result-back">← 전국 검색</a>
    </div>
    <div id="parkingList">
      <div class="loading-state"><div class="spinner"></div><br>불러오는 중...</div>
    </div>
    <div id="loadMore" style="text-align:center;margin:20px 0;display:none;">
      <button id="loadMoreBtn" style="padding:10px 28px;background:var(--primary);color:#fff;border-radius:8px;font-size:.9rem;font-weight:600;">더 보기</button>
    </div>
  </div>

  <!-- 지도 + 광고 -->
  <div class="region-aside">
    <div id="region-map">
      <div class="map-placeholder">
        <div class="icon">🗺️</div>
        <p>지도 로딩 중...</p>
      </div>
    </div>
    <div class="mid-ad" style="margin-top:16px;min-height:600px;">
      <div class="ad-label">📢 광고</div>
      <div>300×600 (사이드바)</div>
    </div>
  </div>
</div>

<!-- SEO 텍스트 -->
<section class="seo-section">
  <h2>{{ sido }} 공영주차장 안내</h2>
  <p>
    {{ sido }}의 공영주차장은 총 {{ count }}개소로, 노상주차장·노외주차장·부설주차장으로 구분됩니다.
    {{ short }} 공영주차장은 민영 주차장보다 저렴한 요금으로 이용할 수 있으며 운영 시간 내 주차가 가능합니다.
    {{ short }} 무료주차장, {{ short }} 저렴한 주차장을 찾으신다면 위 목록에서 요금 정보를 확인하시고,
    지도보기 또는 길찾기 버튼으로 바로 이동하세요.
  </p>
</section>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-col">
        <p class="footer-logo">🅿️ 우아파킹</p>
        <p>전국 공영주차장 정보<br>설치 불필요 · 로그인 불필요</p>
        <a href="https://wooahouse.com" target="_blank" style="color:#10B981;margin-top:8px;display:inline-block;">wooahouse.com →</a>
      </div>
      <div class="footer-col">
        <p class="footer-heading">다른 지역 보기</p>
        <a href="서울특별시.html">서울특별시</a>
        <a href="경기도.html">경기도</a>
        <a href="부산광역시.html">부산광역시</a>
        <a href="인천광역시.html">인천광역시</a>
        <a href="대구광역시.html">대구광역시</a>
        <a href="경상북도.html">경상북도</a>
      </div>
      <div class="footer-col">
        <p class="footer-heading">WooaHouse 서비스</p>
        <a href="https://pdfkit.wooahouse.com" target="_blank">📄 WooaPDF</a>
        <a href="https://imagekit.wooahouse.com" target="_blank">🖼️ WooaImage</a>
        <a href="https://textkit.wooahouse.com" target="_blank">📝 WooaText</a>
        <a href="https://qrkit.wooahouse.com" target="_blank">🔲 WooaQR</a>
      </div>
      <div class="footer-col">
        <p class="footer-heading">정보</p>
        <a href="../privacy.html">개인정보처리방침</a>
        <a href="../">메인으로</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2026 WooaHouse. All rights reserved.</p>
      <p>데이터 출처: 공공데이터포털 전국주차장정보표준데이터</p>
    </div>
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

SITEMAP_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
{region_urls}
</urlset>
"""

SITEMAP_ENTRY = """\
  <url>
    <loc>{base_url}/지역/{sido}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>"""


def copy_json_files():
    """data/parking/ → docs/data/parking/ 복사"""
    DATA_DEST.mkdir(parents=True, exist_ok=True)
    copied = 0
    for f in DATA_SRC.glob("*.json"):
        dest = DATA_DEST / f.name
        shutil.copy2(f, dest)
        copied += 1
    print(f"  JSON 복사: {copied}개 파일 → docs/data/parking/")


def generate_region_pages():
    """지역별 HTML 생성"""
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(REGION_PAGE_TEMPLATE)

    generated = []
    for json_file in sorted(DATA_SRC.glob("*.json")):
        sido = json_file.stem
        if sido not in SIDO_SHORT:
            print(f"  건너뜀 (알 수 없는 시도): {sido}")
            continue

        # 레코드 수 파악
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        count = len(data.get("records", []))

        short = SIDO_SHORT[sido]
        center = SIDO_CENTER.get(sido, (36.5, 127.8))

        html = tmpl.render(
            sido=sido,
            short=short,
            count=f"{count:,}",
            base_url=BASE_URL,
            today=TODAY,
            center_lat=center[0],
            center_lon=center[1],
            kakao_key=KAKAO_APP_KEY,
        )

        out_path = PAGES_DIR / f"{sido}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"  생성: 지역/{sido}.html ({count:,}건)")
        generated.append(sido)

    return generated


def generate_sitemap(sidos):
    """sitemap.xml 생성"""
    entries = "\n".join(
        SITEMAP_ENTRY.format(base_url=BASE_URL, sido=s, today=TODAY)
        for s in sidos
    )
    xml = SITEMAP_TEMPLATE.format(base_url=BASE_URL, today=TODAY, region_urls=entries)
    SITEMAP_OUT.write_text(xml, encoding="utf-8")
    print(f"  sitemap.xml 생성 ({len(sidos) + 1}개 URL)")


def main():
    print("=" * 50)
    print("wooaparking 페이지 생성기")
    print("=" * 50)

    print("\n[1/3] JSON 파일 복사...")
    copy_json_files()

    print("\n[2/3] 지역별 HTML 생성...")
    sidos = generate_region_pages()

    print("\n[3/3] sitemap.xml 생성...")
    generate_sitemap(sidos)

    print(f"\n완료! {len(sidos)}개 지역 페이지 생성됨")
    print(f"   → {PAGES_DIR}")


if __name__ == "__main__":
    main()
