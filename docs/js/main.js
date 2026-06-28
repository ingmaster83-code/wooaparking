/* ===== wooaparking — main.js ===== */

// 시도명 → JSON 파일명 매핑
const SIDO_FILE_MAP = {
  '서울특별시': '서울특별시',
  '부산광역시': '부산광역시',
  '대구광역시': '대구광역시',
  '인천광역시': '인천광역시',
  '광주광역시': '광주광역시',
  '대전광역시': '대전광역시',
  '울산광역시': '울산광역시',
  '세종특별자치시': '세종특별자치시',
  '경기도': '경기도',
  '강원특별자치도': '강원특별자치도',
  '강원도': '강원특별자치도',
  '충청북도': '충청북도',
  '충청남도': '충청남도',
  '전북특별자치도': '전북특별자치도',
  '전라북도': '전북특별자치도',
  '전라남도': '전라남도',
  '경상북도': '경상북도',
  '경상남도': '경상남도',
  '제주특별자치도': '제주특별자치도',
  '제주도': '제주특별자치도',
};

// 짧은 지역명 → 시도명
const REGION_SHORT_MAP = {
  '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시',
  '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시',
  '울산': '울산광역시', '세종': '세종특별자치시', '경기': '경기도',
  '강원': '강원특별자치도', '충북': '충청북도', '충남': '충청남도',
  '전북': '전북특별자치도', '전남': '전라남도', '경북': '경상북도',
  '경남': '경상남도', '제주': '제주특별자치도',
};

const DATA_BASE = 'data/parking/';
const SEARCH_RADIUS = 1000; // meters

let map, geocoder, infowindow;
let markers = [];
let currentResults = [];
let kakaoLoaded = false;

// ── Kakao SDK 동적 로드 ──────────────────────────
function loadKakaoSDK() {
  return new Promise((resolve, reject) => {
    if (typeof kakao !== 'undefined' && kakao.maps) { resolve(); return; }
    const script = document.createElement('script');
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_APP_KEY}&libraries=services&autoload=false`;
    script.onload = () => kakao.maps.load(resolve);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// ── 지도 초기화 ──────────────────────────────────
function initMap() {
  const container = document.getElementById('map');
  if (!container) return;
  const options = {
    center: new kakao.maps.LatLng(36.5, 127.8),
    level: 13,
  };
  map = new kakao.maps.Map(container, options);
  geocoder = new kakao.maps.services.Geocoder();
  infowindow = new kakao.maps.InfoWindow({ zIndex: 1 });
  kakaoLoaded = true;
}

// ── 거리 계산 (Haversine) ─────────────────────────
function getDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── 주소에서 시도명 추출 ─────────────────────────
function extractSido(address) {
  if (!address) return null;
  const first = address.trim().split(/\s+/)[0];
  if (SIDO_FILE_MAP[first]) return SIDO_FILE_MAP[first];
  for (const [short, full] of Object.entries(REGION_SHORT_MAP)) {
    if (first.startsWith(short)) return full;
  }
  return null;
}

// ── JSON 로드 (캐시) ─────────────────────────────
const dataCache = {};
async function loadSidoData(sido) {
  if (dataCache[sido]) return dataCache[sido];
  const url = `${DATA_BASE}${encodeURIComponent(sido)}.json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`데이터 없음: ${sido}`);
  const json = await res.json();
  dataCache[sido] = json.records || [];
  return dataCache[sido];
}

// ── 검색 핵심 로직 ───────────────────────────────
async function searchNearby(lat, lon, sido) {
  showLoading();
  clearMarkers();

  // 지도 중심 이동
  if (kakaoLoaded) {
    const center = new kakao.maps.LatLng(lat, lon);
    map.setCenter(center);
    map.setLevel(5);

    // 내 위치 마커
    new kakao.maps.Marker({
      map,
      position: center,
      image: new kakao.maps.MarkerImage(
        'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/markerStar.png',
        new kakao.maps.Size(24, 35)
      ),
    });
  }

  let records;
  try {
    records = await loadSidoData(sido);
  } catch {
    showError(`${sido} 데이터를 불러올 수 없습니다.`);
    return;
  }

  const results = records
    .filter(r => r['위도'] && r['경도'])
    .map(r => ({
      ...r,
      distance: getDistance(lat, lon, parseFloat(r['위도']), parseFloat(r['경도'])),
    }))
    .filter(r => r.distance <= SEARCH_RADIUS)
    .sort((a, b) => a.distance - b.distance);

  currentResults = results;
  renderResults(results, lat, lon);
}

// ── 마커 생성 ────────────────────────────────────
function addMarker(record, index) {
  if (!kakaoLoaded || !record['위도'] || !record['경도']) return null;
  const pos = new kakao.maps.LatLng(parseFloat(record['위도']), parseFloat(record['경도']));
  const marker = new kakao.maps.Marker({ map, position: pos });

  kakao.maps.event.addListener(marker, 'click', () => {
    infowindow.setContent(buildInfoWindowContent(record));
    infowindow.open(map, marker);
    // 카드 하이라이트
    document.querySelectorAll('.parking-card').forEach(c => c.classList.remove('highlighted'));
    const card = document.getElementById(`card-${index}`);
    if (card) {
      card.classList.add('highlighted');
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  markers.push(marker);
  return marker;
}

function clearMarkers() {
  markers.forEach(m => m.setMap(null));
  markers = [];
  if (infowindow) infowindow.close();
}

// ── 인포윈도우 내용 ──────────────────────────────
function buildInfoWindowContent(r) {
  const addr = r['소재지도로명주소'] || r['소재지지번주소'] || '';
  const fee = buildFeeText(r);
  const lat = r['위도'], lon = r['경도'];
  const naviUrl = `https://map.kakao.com/link/to/${encodeURIComponent(r['주차장명'])},${lat},${lon}`;
  return `
    <div class="iw-wrap">
      <div class="iw-title">${r['주차장명'] || '주차장'}</div>
      ${addr ? `<div class="iw-row">📍 ${addr}</div>` : ''}
      ${fee ? `<div class="iw-row">💰 ${fee}</div>` : ''}
      ${r['주차구획수'] ? `<div class="iw-row">🚗 ${r['주차구획수']}면</div>` : ''}
      <a href="${naviUrl}" target="_blank" class="iw-link">길찾기 →</a>
    </div>`;
}

// ── 요금 텍스트 ──────────────────────────────────
function buildFeeText(r) {
  const base = r['주차기본요금'];
  const time = r['주차기본시간'];
  if (!base || base === '0' || base === '') return '무료';
  if (time) return `${time}분 ${Number(base).toLocaleString()}원`;
  return `${Number(base).toLocaleString()}원`;
}

// ── 운영시간 텍스트 ──────────────────────────────
function buildHoursText(r) {
  const start = r['평일운영시작시각'];
  const end = r['평일운영종료시각'];
  if (!start && !end) return '';
  if (start === '00:00' && end === '23:59') return '24시간';
  return `${start || '?'} ~ ${end || '?'}`;
}

// ── 결과 렌더링 ──────────────────────────────────
function renderResults(results, centerLat, centerLon) {
  const area = document.getElementById('result-area');
  if (!area) return;

  if (results.length === 0) {
    area.innerHTML = `
      <div class="empty-state">
        <div class="icon">🅿️</div>
        <p>반경 1km 내 공영주차장이 없습니다.<br>검색 범위를 넓히거나 다른 주소를 입력해 보세요.</p>
      </div>`;
    return;
  }

  const header = `
    <div class="result-header">
      <div class="result-count">반경 1km 내 <strong>${results.length}개</strong> 공영주차장</div>
    </div>`;

  const parts = [];
  results.forEach((r, i) => {
    addMarker(r, i);
    parts.push(buildCard(r, i));
    if ((i + 1) % 10 === 0 && i + 1 < results.length) parts.push(buildInlineAd());
  });

  area.innerHTML = header + `<div class="parking-list">${parts.join('')}</div>`;
  try { (adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}

  // 카드 클릭 → 마커 클릭 효과
  results.forEach((r, i) => {
    const card = document.getElementById(`card-${i}`);
    if (!card) return;
    card.addEventListener('click', () => {
      document.querySelectorAll('.parking-card').forEach(c => c.classList.remove('highlighted'));
      card.classList.add('highlighted');
      if (markers[i] && kakaoLoaded) {
        map.setCenter(markers[i].getPosition());
        infowindow.setContent(buildInfoWindowContent(r));
        infowindow.open(map, markers[i]);
      }
    });
  });
}

// ── 주차장 카드 HTML ─────────────────────────────
function buildCard(r, index) {
  const name = r['주차장명'] || '주차장';
  const addr = r['소재지도로명주소'] || r['소재지지번주소'] || '';
  const dist = r.distance < 1000
    ? `${Math.round(r.distance)}m`
    : `${(r.distance / 1000).toFixed(1)}km`;
  const gubun = r['주차장구분'] || '';
  const badgeClass = gubun.includes('노상') ? 'badge-nosang' : gubun.includes('노외') ? 'badge-nowai' : 'badge-buset';
  const fee = buildFeeText(r);
  const feeBadge = (fee === '무료') ? '<span class="badge badge-free">무료</span>' : '<span class="badge badge-paid">유료</span>';
  const hours = buildHoursText(r);
  const spaces = r['주차구획수'];
  const lat = r['위도'], lon = r['경도'];
  const naviUrl = `https://map.kakao.com/link/to/${encodeURIComponent(name)},${lat},${lon}`;

  return `
    <div class="parking-card" id="card-${index}" role="button" tabindex="0">
      <div class="card-top">
        <div class="card-name">${name}</div>
        <div class="card-distance">${dist}</div>
      </div>
      <div class="badge-wrap">
        ${gubun ? `<span class="badge ${badgeClass}">${gubun}</span>` : ''}
        ${feeBadge}
      </div>
      <div class="card-info">
        ${addr ? `<div class="card-row"><span class="icon">📍</span><span>${addr}</span></div>` : ''}
        ${hours ? `<div class="card-row"><span class="icon">⏰</span><span>평일 ${hours}</span></div>` : ''}
        <div class="card-row"><span class="icon">💰</span><span>${fee}</span></div>
        ${spaces ? `<div class="card-row"><span class="icon">🚗</span><span>총 ${spaces}면</span></div>` : ''}
      </div>
      <div class="card-actions">
        <span class="btn-map">🗺️ 지도에서 보기</span>
        <a href="${naviUrl}" target="_blank" class="btn-navi" onclick="event.stopPropagation()">길찾기 →</a>
      </div>
    </div>`;
}

// ── 인라인 광고 ──────────────────────────────────
function buildInlineAd() {
  return `<div class="inline-ad">
    <ins class="adsbygoogle" style="display:block;width:100%;height:90px"
      data-ad-client="ca-pub-6464921081676309"
      data-ad-slot="7080296704"
      data-ad-format="auto" data-full-width-responsive="true"></ins>
  </div>`;
}

// ── 로딩 / 에러 상태 ─────────────────────────────
function showLoading() {
  const area = document.getElementById('result-area');
  if (area) area.innerHTML = `<div class="loading"><div class="spinner"></div><br>주변 주차장을 검색하는 중...</div>`;
}

function showError(msg) {
  const area = document.getElementById('result-area');
  if (area) area.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><p>${msg}</p></div>`;
}

// ── 주소 검색 ────────────────────────────────────
function handleSearch() {
  const query = document.getElementById('search-input')?.value.trim();
  if (!query) return;
  if (!kakaoLoaded) { alert('지도를 불러오는 중입니다. 잠시 후 다시 시도해 주세요.'); return; }

  geocoder.addressSearch(query, (result, status) => {
    if (status === kakao.maps.services.Status.OK) {
      handleGeocoderResult(result[0]);
    } else {
      // 키워드 검색 대체
      const ps = new kakao.maps.services.Places();
      ps.keywordSearch(query, (places, ps_status) => {
        if (ps_status === kakao.maps.services.Status.OK && places.length > 0) {
          handleGeocoderResult({ y: places[0].y, x: places[0].x, address_name: places[0].road_address_name || places[0].address_name });
        } else {
          showError('검색 결과가 없습니다. 더 정확한 주소를 입력해 보세요.');
        }
      });
    }
  });
}

function handleGeocoderResult(result) {
  const lat = parseFloat(result.y);
  const lon = parseFloat(result.x);
  const addr = result.address_name || '';
  const sido = extractSido(addr);
  if (!sido) {
    showError('해당 지역의 주차장 데이터를 찾을 수 없습니다.');
    return;
  }
  searchNearby(lat, lon, sido);
}

// ── 내 위치 ──────────────────────────────────────
function handleMyLocation() {
  if (!navigator.geolocation) { alert('이 브라우저는 위치 정보를 지원하지 않습니다.'); return; }
  if (!kakaoLoaded) { alert('지도를 불러오는 중입니다. 잠시 후 다시 시도해 주세요.'); return; }

  showLoading();
  navigator.geolocation.getCurrentPosition(
    pos => {
      const { latitude: lat, longitude: lon } = pos.coords;
      // 역지오코딩으로 시도 판별
      geocoder.coord2RegionCode(lon, lat, (result, status) => {
        if (status === kakao.maps.services.Status.OK) {
          const region1 = result[0]?.region_1depth_name || '';
          const sido = extractSido(region1) || SIDO_FILE_MAP[region1];
          if (sido) {
            searchNearby(lat, lon, sido);
          } else {
            showError('현재 위치의 지역 정보를 확인할 수 없습니다.');
          }
        } else {
          showError('위치 정보를 처리할 수 없습니다.');
        }
      });
    },
    err => {
      const msg = err.code === 1
        ? '위치 접근이 거부되었습니다. 브라우저 설정에서 위치 권한을 허용해 주세요.'
        : '위치 정보를 가져올 수 없습니다.';
      showError(msg);
    },
    { timeout: 8000 }
  );
}

// ── URL 쿼리 파라미터 처리 ────────────────────────
function handleUrlQuery() {
  const params = new URLSearchParams(location.search);
  const q = params.get('q');
  if (q) {
    const input = document.getElementById('search-input');
    if (input) { input.value = q; handleSearch(); }
  }
}

// ── 이벤트 바인딩 ────────────────────────────────
function bindEvents() {
  document.getElementById('btn-search')?.addEventListener('click', handleSearch);
  document.getElementById('btn-location')?.addEventListener('click', handleMyLocation);
  document.getElementById('search-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') handleSearch();
  });
}

// ── 초기화 ───────────────────────────────────────
async function init() {
  bindEvents();
  try {
    await loadKakaoSDK();
    initMap();
    handleUrlQuery();
  } catch {
    document.getElementById('map').innerHTML =
      '<div class="map-status">⚠️ 지도를 불러올 수 없습니다. config.js에 카카오맵 키를 설정해 주세요.</div>';
  }
}

document.addEventListener('DOMContentLoaded', init);
