"""헤드풀 브라우저로 수동 로그인 후 storage_state 저장.

사용법:
  .venv/bin/python scripts/capture_session.py bunjang
  .venv/bin/python scripts/capture_session.py junggonara
"""
import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

PLATFORMS = {
    "bunjang": {
        "url": "https://m.bunjang.co.kr/login",
        "success": "https://m.bunjang.co.kr",
    },
    "junggonara": {
        "url": "https://web.joongna.com/signin",
        "success": "https://web.joongna.com",
    },
}

AUTH_DIR = Path(__file__).resolve().parent.parent / "auth"


async def capture(platform: str):
    cfg = PLATFORMS[platform]
    AUTH_DIR.mkdir(exist_ok=True)
    out = AUTH_DIR / f"{platform}.json"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(cfg["url"])

        print(f"\n🔐 브라우저에서 {platform} 로그인을 완료하세요.")
        print("   로그인 완료 후 Enter 를 누르세요.\n")

        # 사용자가 Enter 누를 때까지 대기
        await asyncio.get_event_loop().run_in_executor(None, input, "로그인 완료 후 Enter: ")

        await context.storage_state(path=str(out))
        await browser.close()

    print(f"✅ 세션 저장 완료: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=PLATFORMS.keys())
    args = parser.parse_args()
    asyncio.run(capture(args.platform))
