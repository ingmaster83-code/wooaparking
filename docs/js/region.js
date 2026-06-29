/* ===== wooaparking — region.js ===== */
// REGION_NAME, REGION_SHORT, PARKING_DATA_URL 은 각 HTML에서 전역 정의

let modalMap = null;
let modalInfowindow = null;
let kakaoLoaded = false;
let allRecords = [];
let currentTab = '전체';
let shownCount = 0;
const PAGE = 50;

// ── Kakao SDK 로드 ───────────────────────────────
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

// ── 지도 모달 ────────────────────────────────────
function createMapModal() {
  if (document.getElementById('mapModal')) return;
  const modal = document.createElement('div');
  modal.id = 'mapModal';
  modal.innerHTML = `
    <div class="map-modal-backdrop"></div>
    <div class="map-modal-box">
      <div class="map-modal-header">
        <div class="map-modal-title" id="mapModalTitle"></div>
        <button class="map-modal-close" id="mapModalClose">✕</button>
      </div>
      <div class="map-modal-info" id="mapModalInfo"></div>
      <div id="mapModalMap"></div>
      <div class="map-modal-footer">
        <a id="mapModalNavi" href="#" class="btn-modal-navi">🗺️ 카카오맵 길찾기 →</a>
      </div>
    </div>`;
  document.body.appendChild(modal);

  document.getElementById('mapModalClose').addEventListener('click', closeMapModal);
  modal.querySelector('.map-modal-backdrop').addEventListener('click', closeMapModal);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMapModal(); });
}

function openMapModal(r) {
  createMapModal();
  const name = r['주차장명'] || '주차장';
  const addr = r['소재지도로명주소'] || r['소재지지번주소'] || '';
  const fee = buildFeeText(r);
  const hours = buildHoursText(r);
  const spaces = r['주차구획수'];

  document.getElementById('mapModalTitle').textContent = name;
  document.getElementById('mapModalInfo').innerHTML = `
    ${addr ? `<span>📍 ${addr}</span>` : ''}
    <span>💰 ${fee}</span>
    ${hours ? `<span>⏰ 평일 ${hours}</span>` : ''}
    ${spaces ? `<span>🚗 ${spaces}면</span>` : ''}`;

  const naviUrl = r['위도']
    ? `https://map.kakao.com/link/to/${encodeURIComponent(name)},${r['위도']},${r['경도']}`
    : `https://map.kakao.com/link/search/${encodeURIComponent(name)}`;
  document.getElementById('mapModalNavi').href = naviUrl;

  document.getElementById('mapModal').classList.add('open');
  document.body.style.overflow = 'hidden';

  // 지도 렌더링
  if (kakaoLoaded && r['위도'] && r['경도']) {
    setTimeout(() => initModalMap(r), 50);
  } else if (!r['위도']) {
    document.getElementById('mapModalMap').innerHTML =
      '<div class="map-no-coord">📍 좌표 정보가 없어 지도를 표시할 수 없습니다.</div>';
  } else {
    document.getElementById('mapModalMap').innerHTML =
      '<div class="map-no-coord">🗺️ 지도는 서비스 배포 후 이용 가능합니다.</div>';
  }
}

function initModalMap(r) {
  const container = document.getElementById('mapModalMap');
  container.innerHTML = '';
  const lat = parseFloat(r['위도']);
  const lng = parseFloat(r['경도']);
  const pos = new kakao.maps.LatLng(lat, lng);

  modalMap = new kakao.maps.Map(container, { center: pos, level: 4 });
  modalInfowindow = new kakao.maps.InfoWindow({ zIndex: 1 });

  const marker = new kakao.maps.Marker({ map: modalMap, position: pos });
  modalInfowindow.setContent(buildInfoWindow(r));
  modalInfowindow.open(modalMap, marker);
}

function closeMapModal() {
  const modal = document.getElementById('mapModal');
  if (modal) modal.classList.remove('open');
  document.body.style.overflow = '';
  // 모달 지도 정리
  if (modalMap) {
    modalMap = null;
    const container = document.getElementById('mapModalMap');
    if (container) container.innerHTML = '';
  }
}

// ── 인포윈도우 ───────────────────────────────────
function buildInfoWindow(r) {
  const addr = r['소재지도로명주소'] || r['소재지지번주소'] || '';
  const fee = buildFeeText(r);
  const naviUrl = `https://map.kakao.com/link/to/${encodeURIComponent(r['주차장명'] || '')},${r['위도']},${r['경도']}`;
  return `
    <div class="iw-wrap">
      <div class="iw-title">${r['주차장명'] || '주차장'}</div>
      ${addr ? `<div class="iw-row">📍 ${addr}</div>` : ''}
      ${fee ? `<div class="iw-row">💰 ${fee}</div>` : ''}
      ${r['주차구획수'] ? `<div class="iw-row">🚗 ${r['주차구획수']}면</div>` : ''}
      <a href="${naviUrl}" class="iw-link">길찾기 →</a>
    </div>`;
}

// ── 요금 / 운영시간 ──────────────────────────────
function buildFeeText(r) {
  if (r['요금정보'] === '무료') return '무료';
  const base = r['주차기본요금'];
  const time = r['주차기본시간'];
  if (!base || base === '0' || base === '') return '무료';
  if (time) return `${time}분 ${Number(base).toLocaleString()}원`;
  return `${Number(base).toLocaleString()}원`;
}

function buildHoursText(r) {
  const s = r['평일운영시작시각'], e = r['평일운영종료시각'];
  if (!s && !e) return '';
  if (s === '00:00' && e === '23:59') return '24시간';
  return `${s || '?'} ~ ${e || '?'}`;
}

// ── 카드 HTML ────────────────────────────────────
function buildCard(r, index) {
  const name = r['주차장명'] || '주차장';
  const addr = r['소재지도로명주소'] || r['소재지지번주소'] || '';
  const yuhyung = r['주차장유형'] || '';
  const gubun = r['주차장구분'] || '';
  const badgeClass = yuhyung === '노상' ? 'badge-nosang' : yuhyung === '노외' ? 'badge-nowai' : 'badge-buset';
  const isFree = r['요금정보'] === '무료' || !r['주차기본요금'] || r['주차기본요금'] === '0' || r['주차기본요금'] === '';
  const fee = buildFeeText(r);
  const feeBadge = isFree ? '<span class="badge badge-free">무료</span>' : '<span class="badge badge-paid">유료</span>';
  const hours = buildHoursText(r);
  const spaces = r['주차구획수'];
  const naviUrl = r['위도'] ? `https://map.kakao.com/link/to/${encodeURIComponent(name)},${r['위도']},${r['경도']}` : '#';

  return `
    <div class="parking-card" data-index="${index}">
      <div class="card-top">
        <div class="card-name">${name}</div>
      </div>
      <div class="badge-row">
        ${yuhyung ? `<span class="badge ${badgeClass}">${yuhyung}주차장</span>` : ''}
        ${gubun ? `<span class="badge badge-type">${gubun}</span>` : ''}
        ${feeBadge}
      </div>
      <div class="card-info">
        ${addr ? `<div class="card-row"><span class="ci">📍</span><span>${addr}</span></div>` : ''}
        ${hours ? `<div class="card-row"><span class="ci">⏰</span><span>평일 ${hours}</span></div>` : ''}
        <div class="card-row"><span class="ci">💰</span><span>${fee}</span></div>
        ${spaces ? `<div class="card-row"><span class="ci">🚗</span><span>총 ${spaces}면</span></div>` : ''}
      </div>
      <div class="card-actions">
        <button class="btn-map" data-index="${index}" onclick="event.stopPropagation()">🗺️ 지도에서 보기</button>
        ${r['위도'] ? `<a href="${naviUrl}" class="btn-navi" onclick="event.stopPropagation()">길찾기 →</a>` : ''}
      </div>
    </div>`;
}

// ── 인라인 광고 ──────────────────────────────────
function buildInlineAd() {
  return `<div class="inline-ad">
    <div class="ad-label">📢 광고</div>
    <ins class="adsbygoogle" style="display:block;width:100%;height:90px"
      data-ad-client="ca-pub-6464921081676309"
      data-ad-slot="7080296704"
      data-ad-format="auto" data-full-width-responsive="true"></ins>
  </div>`;
}

function buildCardsWithAds(records, from, to) {
  const parts = [];
  for (let i = from; i < to; i++) {
    parts.push(buildCard(records[i], i));
    if ((i - from + 1) % 10 === 0 && i + 1 < to) parts.push(buildInlineAd());
  }
  return parts.join('');
}

// ── 목록 렌더링 ──────────────────────────────────
function renderList(records) {
  const listEl = document.getElementById('parkingList');
  const countEl = document.getElementById('listCount');
  const loadMoreWrap = document.getElementById('loadMore');
  const loadMoreBtn = document.getElementById('loadMoreBtn');
  if (!listEl) return;

  if (countEl) countEl.textContent = records.length.toLocaleString();

  if (records.length === 0) {
    listEl.innerHTML = '<div class="empty-state"><div class="ei">🅿️</div><p>해당 구분의 주차장이 없습니다.</p></div>';
    if (loadMoreWrap) loadMoreWrap.style.display = 'none';
    return;
  }

  shownCount = Math.min(PAGE, records.length);
  listEl.innerHTML = buildCardsWithAds(records, 0, shownCount);

  if (loadMoreWrap && loadMoreBtn) {
    if (shownCount < records.length) {
      loadMoreBtn.textContent = `더 보기 (${(records.length - shownCount).toLocaleString()}개 남음)`;
      loadMoreWrap.style.display = 'block';
      loadMoreBtn.onclick = () => {
        const next = Math.min(shownCount + PAGE, records.length);
        const frag = document.createElement('div');
        frag.innerHTML = buildCardsWithAds(records, shownCount, next);
        while (frag.firstChild) listEl.insertBefore(frag.firstChild, loadMoreWrap);
        shownCount = next;
        if (shownCount >= records.length) loadMoreWrap.style.display = 'none';
        else loadMoreBtn.textContent = `더 보기 (${(records.length - shownCount).toLocaleString()}개 남음)`;
        bindCardEvents(listEl, records);
        try { (adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}
      };
    } else {
      loadMoreWrap.style.display = 'none';
    }
  }

  bindCardEvents(listEl, records);
  try { (adsbygoogle = window.adsbygoogle || []).push({}); } catch(e) {}
}

function bindCardEvents(listEl, records) {
  listEl.querySelectorAll('.btn-map').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.index);
      openMapModal(records[idx]);
    });
  });
}

// ── 탭 필터 ──────────────────────────────────────
function filterByTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  let filtered;
  if (tab === '전체') {
    filtered = allRecords;
  } else if (tab === '무료') {
    filtered = allRecords.filter(r =>
      r['요금정보'] === '무료' || !r['주차기본요금'] || r['주차기본요금'] === '0' || r['주차기본요금'] === ''
    );
  } else {
    filtered = allRecords.filter(r => (r['주차장유형'] || '') === tab);
  }
  renderList(filtered);
}

// ── 키워드 검색 ──────────────────────────────────
function filterByKeyword(keyword) {
  const kw = keyword.trim().toLowerCase();
  const base = currentTab === '전체' ? allRecords
    : currentTab === '무료' ? allRecords.filter(r => r['요금정보'] === '무료' || !r['주차기본요금'] || r['주차기본요금'] === '0' || r['주차기본요금'] === '')
    : allRecords.filter(r => (r['주차장유형'] || '') === currentTab);
  const filtered = kw
    ? base.filter(r =>
        (r['주차장명'] || '').toLowerCase().includes(kw) ||
        (r['소재지도로명주소'] || '').toLowerCase().includes(kw) ||
        (r['소재지지번주소'] || '').toLowerCase().includes(kw)
      )
    : base;
  renderList(filtered);
}

// ── 초기화 ───────────────────────────────────────
async function init() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => filterByTab(btn.dataset.tab));
  });

  const searchInput = document.getElementById('regionSearchInput');
  const searchBtn = document.getElementById('regionSearchBtn');
  searchInput?.addEventListener('keydown', e => { if (e.key === 'Enter') filterByKeyword(searchInput.value); });
  searchBtn?.addEventListener('click', () => filterByKeyword(searchInput?.value || ''));

  const listEl = document.getElementById('parkingList');
  if (typeof PARKING_RECORDS !== 'undefined') {
    allRecords = PARKING_RECORDS;
  } else {
    try {
      const res = await fetch(PARKING_DATA_URL);
      if (!res.ok) throw new Error('fetch failed');
      const json = await res.json();
      allRecords = json.records || [];
    } catch {
      if (listEl) listEl.innerHTML = '<div class="empty-state"><div class="ei">⚠️</div><p>데이터를 불러올 수 없습니다.</p></div>';
      return;
    }
  }

  // Kakao SDK 로드 (모달 지도용)
  try {
    await loadKakaoSDK();
    kakaoLoaded = true;
  } catch {
    kakaoLoaded = false;
  }

  renderList(allRecords);
}

document.addEventListener('DOMContentLoaded', init);
