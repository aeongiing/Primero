"""[여원] 카테고리 팝업 정밀 캡처 도구.

판매 폼에서 카테고리 팝업을 연 뒤, 팝업 안 항목들의 "정확한 CSS 경로"를 떠서
헤더 메뉴와 구분되는 스코프 셀렉터를 찾는다.

핵심: 터미널로 alt-tab 하면 팝업이 닫힐 수 있으므로, input() 대신 '카운트다운'
으로 자동 캡처한다. 창에서 카테고리 팝업을 연 채로 기다리면 자동 저장된다.

사용법: python scripts/capture_popup.py bunjang https://m.bunjang.co.kr/products/new [대기초]
저장: captured/<이름>.popup.json (+ .popup.html)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_COLLECT_JS = r"""
() => {
  function cssPath(el) {
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 7) {
      let sel = el.tagName.toLowerCase();
      if (el.id) { parts.unshift(sel + '#' + el.id); break; }
      const cls = (typeof el.className === 'string' && el.className.trim())
        ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
      let nth = 1, sib = el;
      while ((sib = sib.previousElementSibling)) { if (sib.tagName === el.tagName) nth++; }
      parts.unshift(sel + cls + ':nth-of-type(' + nth + ')');
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  const targets = ['여성의류','남성의류','아우터','상의','하의','니트','티셔츠','코트',
                   '점퍼','바지','패션의류','패션잡화','수입','명품','상품 상태','사이즈'];
  const all = Array.from(document.querySelectorAll('button,a,li,span,div,[role]'));
  const out = [];
  for (const el of all) {
    const t = (el.innerText || '').trim();
    if (!t || t.length > 14) continue;
    if (targets.some(x => t === x || t.includes(x))) {
      out.push({
        tag: el.tagName.toLowerCase(),
        text: t.slice(0, 24),
        id: el.id || '',
        cls: (typeof el.className === 'string' ? el.className : '').slice(0, 80),
        role: el.getAttribute('role') || '',
        path: cssPath(el),
      });
    }
  }
  return out.slice(0, 150);
}
"""


def capture(name: str, start_url: str, wait_sec: int) -> None:
    from playwright.sync_api import sync_playwright

    out_dir = Path(__file__).resolve().parent.parent / "captured"
    out_dir.mkdir(exist_ok=True)
    auth = Path(__file__).resolve().parent.parent / "auth" / f"{name.split('_')[0]}.json"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            **({"storage_state": str(auth)} if auth.exists() else {})
        )
        page = context.new_page()
        page.goto(start_url, wait_until="domcontentloaded")

        print("\n" + "=" * 60)
        print(f"지금부터 {wait_sec}초 안에, 창에서 '카테고리' 버튼을 눌러")
        print("카테고리 팝업/트리를 '열어둔 상태'로 두세요.")
        print("터미널로 돌아오지 마세요(그대로 두면 자동 캡처).")
        print("=" * 60)
        for remaining in range(wait_sec, 0, -1):
            print(f"  캡처까지 {remaining}초...", end="\r")
            page.wait_for_timeout(1000)
        print("\n캡처 중...")

        items = page.evaluate(_COLLECT_JS)
        html = page.content()
        (out_dir / f"{name}.popup.json").write_text(
            json.dumps({"url": page.url, "items": items}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out_dir / f"{name}.popup.html").write_text(html, encoding="utf-8")
        print(f"저장: captured/{name}.popup.json ({len(items)}개 항목)")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python scripts/capture_popup.py <이름> <URL> [대기초=12]")
        raise SystemExit(1)
    wait = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    capture(sys.argv[1], sys.argv[2], wait)
