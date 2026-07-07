"""지역 페이지에서 region-map div 제거"""
from pathlib import Path

OLD = '<div id="region-map"><div class="map-placeholder"><div class="icon">🗺️</div><p>지도 로딩 중...</p></div></div>'
NEW = ''

docs = Path(__file__).parent.parent / 'docs'
files = list(docs.glob('지역/**/*.html')) + list(docs.glob('지역/*.html'))

updated = 0
for f in files:
    text = f.read_text(encoding='utf-8')
    if OLD in text:
        f.write_text(text.replace(OLD, NEW), encoding='utf-8')
        updated += 1

print(f'완료: {updated}개 파일에서 region-map 제거')
