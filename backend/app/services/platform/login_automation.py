"""번개장터 카카오 로그인 자동화.

번개장터 로그인 페이지에서 카카오 로그인 버튼 클릭 →
카카오 이메일/비밀번호 입력 → 세션 쿠키 저장.
"""

import asyncio
import json
from pathlib import Path


async def bunjang_kakao_login(email: str, password: str, session_path: str) -> dict:
    """번개장터 카카오 로그인 후 세션을 파일로 저장하고 storage_state 반환."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            viewport={"width": 390, "height": 844},
        )
        page = await context.new_page()

        try:
            # 1. 번개장터 로그인 페이지
            await page.goto("https://m.bunjang.co.kr/login", wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)

            # 2. 앱 다운로드 팝업 닫기 (bun-ui-portal)
            try:
                close_btn = page.locator('.bun-ui-portal button, [class*="_app-nudge"] button, [class*="close"], [aria-label*="닫기"]')
                if await close_btn.first.is_visible(timeout=3000):
                    await close_btn.first.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # 3. 카카오 로그인 버튼 클릭 (팝업이 있으면 force=True로 강제 클릭)
            kakao_btn = page.locator('a[href*="kakao"], button:has-text("카카오"), a:has-text("카카오")')
            await kakao_btn.first.click(force=True)
            await page.wait_for_timeout(2000)

            # 3. 카카오 로그인 팝업/페이지에서 이메일/PW 입력
            await page.wait_for_selector('#loginId--1, input[name="loginId"], input[placeholder*="이메일"]', timeout=10000)
            await page.fill('#loginId--1, input[name="loginId"], input[placeholder*="이메일"]', email)
            await page.fill('#password--2, input[name="password"], input[type="password"]', password)

            # 4. 로그인 버튼 클릭
            await page.click('button[type="submit"], input[type="submit"], button:has-text("로그인")')
            await page.wait_for_timeout(3000)

            # 5. 번개장터 메인으로 돌아올 때까지 대기 (최대 10초)
            try:
                await page.wait_for_url("**/bunjang.co.kr/**", timeout=10000)
            except Exception:
                pass

            # 6. 로그인 성공 확인 (마이페이지 링크 존재)
            await page.wait_for_timeout(2000)
            current_url = page.url
            if "login" in current_url and "error" in current_url:
                raise ValueError("카카오 로그인 실패: 이메일 또는 비밀번호를 확인해주세요")

            # 7. 세션 저장
            Path(session_path).parent.mkdir(parents=True, exist_ok=True)
            storage = await context.storage_state(path=session_path)

            return storage

        finally:
            await browser.close()
