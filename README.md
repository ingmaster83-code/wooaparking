# wooaparking

전국 공영주차장 정보 검색 사이트 — [wooaparking.wooahouse.com](https://wooaparking.wooahouse.com)

## 기술 스택
- HTML / CSS / Vanilla JS
- 카카오맵 JavaScript API
- 데이터: 전국주차장정보표준데이터 (18,527건)
- 배포: GitHub Pages (`docs/` 폴더)

## 초기 설정

### 1. 카카오맵 키 설정
```js
// docs/js/config.js
const KAKAO_APP_KEY = '발급받은_키_입력';
```
- [카카오 개발자센터](https://developers.kakao.com) → 내 애플리케이션 → JavaScript 키
- 플랫폼 등록: `https://wooaparking.wooahouse.com`

### 2. 지역별 페이지 생성
```bash
pip install jinja2 python-dotenv
python scripts/generate_pages.py
```

### 3. .env (선택)
```
KAKAO_MAP_KEY=카카오맵_JavaScript키
```

## 폴더 구조
```
wooaparking/
├── data/parking/          # 원본 JSON (시도별, 18,527건)
├── docs/                  # GitHub Pages 루트
│   ├── index.html         # 메인 검색 페이지
│   ├── css/style.css
│   ├── js/
│   │   ├── config.js      # ← 카카오맵 키 설정
│   │   ├── main.js        # 메인 페이지 로직
│   │   └── region.js      # 지역별 페이지 로직
│   ├── data/parking/      # JSON 복사본 (GitHub Pages 서빙)
│   └── 지역/              # 시도별 HTML (자동 생성)
└── scripts/
    └── generate_pages.py  # 지역 페이지 생성기
```

## 데이터 업데이트
1. 공공데이터포털에서 최신 JSON 다운로드
2. `split_parking_by_sido.py` 실행 → `data/parking/` 재생성
3. `scripts/generate_pages.py` 실행 → `docs/` 재생성
4. 커밋 & 푸시

## GitHub Pages 설정
- Settings → Pages → Source: `docs/` 폴더
- Custom domain: `wooaparking.wooahouse.com`
- Cloudflare CNAME 추가
