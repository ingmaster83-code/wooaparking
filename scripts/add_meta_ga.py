"""전체 HTML에 네이버 인증 메타태그 + GA 코드 삽입"""
from pathlib import Path

NAVER = '  <meta name="naver-site-verification" content="f854df366d7f2c4483a4c6410bba4b9a6f060be3" />'
GA = (
    '  <!-- Google Analytics -->\n'
    '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>\n'
    '  <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
    "gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>"
)

INSERT = NAVER + '\n' + GA + '\n'

docs = Path(__file__).parent.parent / 'docs'
files = list(docs.glob('*.html')) + list(docs.glob('지역/**/*.html'))

updated = 0
skipped = 0
for f in files:
    text = f.read_text(encoding='utf-8')
    if 'G-9ZGENFSXWC' in text:
        skipped += 1
        continue
    new_text = text.replace('</head>', INSERT + '</head>', 1)
    f.write_text(new_text, encoding='utf-8')
    updated += 1

print(f'완료: {updated}개 업데이트, {skipped}개 스킵')
