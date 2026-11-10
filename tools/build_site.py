"""배포용 사이트(_site/) 만들기 — GitHub Actions(.github/workflows/pages.yml)가 푸시 때마다 실행.
소스(index.html)는 지금처럼 Tailwind CDN 을 쓰는 채로 두고(로컬에서 파일만 열어도 그대로 보임),
배포본에서만 CDN 스크립트를 '미리 만든 CSS 파일'로 바꾼다 → 첫 화면을 막던 CDN 스크립트(런타임 CSS 생성)가 사라짐.

하는 일
  1. tools/build_light.py 로 light.html 을 다시 만든다 (커밋본이 낡았어도 배포본은 항상 최신)
  2. 저장소 파일을 _site/ 로 복사 (도구·숨김 폴더 제외)
  3. index.html · light.html 마다: 페이지 안의 tailwind.config 를 그대로 써서 CSS 를 빌드하고,
     CDN 스크립트 + 설정 스크립트를 <link rel="stylesheet" href="tw.<테마>.<해시>.css"> 로 바꾼다

실행: python tools/build_site.py   (저장소 루트에서)
Tailwind 실행 파일: 환경변수 TAILWIND_BIN (단독 실행 파일 경로) 이 있으면 그것, 없으면 npx tailwindcss@<버전>
주의: 클래스 이름을 조각내어 이어 붙이면(예: 'w-' + n) 빌드가 찾지 못한다. 완성된 이름을 소스에 그대로 적을 것."""
import hashlib, os, re, shutil, subprocess, sys, tempfile

TAILWIND_VERSION = '3.4.17'   # cdn.tailwindcss.com 이 내려 주는 버전과 같게 유지
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(root, '_site')
SKIP = {'.git', '.github', '.claude', 'tools', '_site', 'adtest', 'node_modules'}
PAGES = [('index.html', 'dark'), ('light.html', 'light')]

CDN_TAG = '<script src="https://cdn.tailwindcss.com"></script>'
CONFIG_RE = re.compile(r'<script>tailwind\.config = (\{.*?\});</script>', re.S)
PRECONNECT = '<link rel="preconnect" href="https://cdn.tailwindcss.com">\n'


def tailwind_cmd():
    exe = os.environ.get('TAILWIND_BIN')
    if exe:
        return [exe]
    npx = shutil.which('npx') or shutil.which('npx.cmd')
    if not npx:
        sys.exit('build_site: TAILWIND_BIN 도 npx 도 없음')
    return [npx, '--yes', f'tailwindcss@{TAILWIND_VERSION}']


def build_css(html_path, config_js, tmp):
    """그 페이지 하나를 훑어 쓰인 클래스만 담은 CSS (압축) 를 돌려준다."""
    cfg, src, dst = (os.path.join(tmp, n) for n in ('tailwind.config.js', 'in.css', 'out.css'))
    content = html_path.replace('\\', '/')
    with open(cfg, 'w', encoding='utf-8') as f:
        f.write(f"module.exports = Object.assign({config_js}, {{ content: ['{content}'] }});\n")
    with open(src, 'w', encoding='utf-8') as f:
        f.write('@tailwind base;\n@tailwind components;\n@tailwind utilities;\n')
    subprocess.run(tailwind_cmd() + ['-c', cfg, '-i', src, '-o', dst, '--minify'], check=True, cwd=tmp)
    return open(dst, encoding='utf-8').read()


def main():
    subprocess.run([sys.executable, os.path.join(root, 'tools', 'build_light.py')], check=True, cwd=root)

    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    for name in os.listdir(root):
        if name in SKIP or name.startswith('.'):
            continue
        s, d = os.path.join(root, name), os.path.join(out, name)
        shutil.copytree(s, d) if os.path.isdir(s) else shutil.copy2(s, d)
    open(os.path.join(out, '.nojekyll'), 'w').close()

    with tempfile.TemporaryDirectory() as tmp:
        for page, theme in PAGES:
            path = os.path.join(out, page)
            html = open(path, encoding='utf-8').read()
            m = CONFIG_RE.search(html)
            assert html.count(CDN_TAG) == 1 and m, f'build_site: {page} 에서 Tailwind CDN 스크립트·설정을 찾을 수 없음'
            css = build_css(path, m.group(1), tmp)
            name = f"tw.{theme}.{hashlib.sha256(css.encode('utf-8')).hexdigest()[:10]}.css"
            with open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n') as f:
                f.write(css)
            # CDN 은 만든 CSS 를 <head> 맨 끝에 넣는다 → 같은 자리(페이지 자체 <style> 뒤)에 두어야 우선순위가 그대로
            assert html.count('</head>') == 1, f'build_site: {page} 의 </head> 가 하나가 아님'
            html = html.replace(m.group(0), '').replace(CDN_TAG, '').replace(PRECONNECT, '').replace('</head>', f'<link rel="stylesheet" href="{name}">\n</head>')
            assert 'cdn.tailwindcss.com' not in html, f'build_site: {page} 에 Tailwind CDN 참조가 남음'
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(html)
            print(f'{page}: {name} ({len(css):,}자)')
    print(f'_site 생성: {out}')


if __name__ == '__main__':
    main()
