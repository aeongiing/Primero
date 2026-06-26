"""[여원] 로그인 세션 저장 도구.

브라우저에서 직접 로그인한 뒤, 그 로그인 상태(쿠키/스토리지)를 파일로 저장한다.
이후 자동화는 이 파일을 불러와 "이미 로그인된" 상태로 시작하므로, 캡차/2단계
인증 같은 폼 로그인 자동화를 우회할 수 있다.

사용법:
    python scripts/save_login.py bunjang https://m.bunjang.co.kr
    python scripts/save_login.py junggonara https://web.joongna.com

동작:
    1) 창이 뜨면 직접 로그인한다(카카오/네이버/휴대폰 인증 등 무엇이든).
    2) 로그인 완료 후 터미널로 돌아와 Enter 를 누른다.
    3) backend/auth/<이름>.json 에 세션이 저장된다.

⚠️ 생성된 auth/<이름>.json 은 로그인 토큰을 담은 비밀 파일이다. git 에 올리지
   않으며(.gitignore), 운영에서는 Secrets Manager 로 관리한다.
"""

import sys
from pathlib import Path


def save_login(name: str, start_url: str | None) -> None:
    from playwright.sync_api import sync_playwright

    auth_dir = Path(__file__).resolve().parent.parent / "auth"
    auth_dir.mkdir(exist_ok=True)
    out_path = auth_dir / f"{name}.json"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        if start_url:
            page.goto(start_url)

        print("\n" + "=" * 60)
        print("1) 뜬 창에서 직접 로그인하세요(어떤 방식이든 OK).")
        print("2) 로그인이 끝난 걸 확인하고, 이 터미널에서 Enter 를 누르세요.")
        print("   (브라우저 창은 닫지 마세요.)")
        print(f"   저장 위치: {out_path}")
        print("=" * 60)
        input("로그인 완료 후 Enter > ")

        context.storage_state(path=str(out_path))
        print(f"\n세션 저장 완료: {out_path}")
        print("이 파일은 비밀입니다. 공유/커밋하지 마세요.")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/save_login.py <이름> [시작URL]")
        raise SystemExit(1)
    save_login(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
