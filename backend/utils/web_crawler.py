"""
Web Crawler Tool Module

This module provides asynchronous web scraping functionality for extracting content
from web pages and PDF documents. It uses trafilatura for main content extraction
and pdfplumber for PDF processing.

Key Features:
-------------
- Asynchronous HTTP requests with aiohttp
- HTML content extraction with trafilatura
- PDF text extraction with pdfplumber
- Automatic content type detection
- Robust error handling
- SSL/TLS support

Supported Content Types:
-----------------------
- HTML web pages
- PDF documents
"""

import aiohttp
import random
import asyncio
import ssl
import json
import httpx
import trafilatura
from typing import Union, Optional
from pydantic import BaseModel, Field
from playwright.async_api import BrowserContext, async_playwright, Browser, Playwright
import pdfplumber
from io import BytesIO

# Config
PER_URL_TIMEOUT = 10
HTTPX_TIMEOUT = 4
CONCURRENCY = 10
BLOCKED_RESOURCES = {"image", "media", "font", "other"}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

ssl_context = ssl.create_default_context()

# Shared aiohttp session — reuses TCP connections across all crawl calls
_httpx_client: Optional[httpx.AsyncClient] = None
_httpx_lock = asyncio.Lock()


async def get_httpx_client() -> httpx.AsyncClient:
    global _httpx_client
    async with _httpx_lock:
        if _httpx_client is None or _httpx_client.is_closed:
            _httpx_client = httpx.AsyncClient(
                http2=True,
                verify=False,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=40,
                    keepalive_expiry=15,
                ),
                timeout=httpx.Timeout(
                    connect=3.0, read=HTTPX_TIMEOUT, write=3.0, pool=3.0
                ),
                headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                },
            )
    return _httpx_client


async def close_httpx_client():
    global _httpx_client
    if _httpx_client and not _httpx_client.is_closed:
        await _httpx_client.aclose()
        _httpx_client = None


_playwright_instance: Optional[Playwright] = None
_browser_instance: Optional[Browser] = None
_browser_lock = asyncio.Lock()
_shared_context: Optional[BrowserContext] = None
_browser_lock = asyncio.Lock()

PLAYWRIGHT_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-gpu",
    "--no-first-run",
    "--ignore-certificate-errors",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
]

async def get_shared_context() -> BrowserContext:
    global _playwright_instance, _browser_instance, _shared_context
    async with _browser_lock:
        if _browser_instance is None or not _browser_instance.is_connected():
            _playwright_instance = await async_playwright().start()
            _browser_instance = await _playwright_instance.chromium.launch(
                headless=True, args=PLAYWRIGHT_ARGS
            )
            _shared_context = await _browser_instance.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=random.choice(USER_AGENTS),
                locale="en-US",
                java_script_enabled=True,
                ignore_https_errors=True,
            )
    return _shared_context


async def close_browser():
    global _playwright_instance, _browser_instance, _shared_context
    if _shared_context:
        await _shared_context.close()
        _shared_context = None
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None


async def close_browser():
    global _playwright_instance, _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None


class ScrapeResult(BaseModel):
    """
    Structured result from web scraping operation.

    Attributes:
        url (str): The URL of the scraped webpage or PDF.
        text (str): The full extracted text content.
        title (str): The title of the webpage or PDF.
        description (str): A short description or summary of the content.
        method (str): The method used to fetch the content (e.g., "httpx", "playwright").
        error (str): Error message if scraping failed, otherwise None.
    """

    url: str = Field(description="The URL of the webpage")
    text: str = Field(description="The full text content of the webpage")
    title: str = Field(description="The title of the webpage")
    description: str = Field(description="A short description of the webpage")
    method: Optional[str] = Field(description="The method used to fetch the page")
    error: Optional[str] = Field(
        default=None, description="Error message if scraping failed"
    )


async def fetch_httpx(url: str) -> tuple[str | bytes, bool, int]:
    client = await get_httpx_client()
    try:
        resp = await client.get(url)
        ct = resp.headers.get("content-type", "").lower()
        is_pdf = "application/pdf" in ct
        if resp.status_code == 200:
            return resp.content, is_pdf, resp.status_code
        return "", False, resp.status_code
    except httpx.TimeoutException:
        return "", False, 0
    except Exception:
        return "", False, 0


async def fetch_playwright(url: str) -> tuple[str | bytes, bool]:
    context = await get_shared_context()
    page = await context.new_page()

    # Block heavy resources — biggest Playwright speedup
    async def block_heavy(route):
        if route.request.resource_type in BLOCKED_RESOURCES:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", block_heavy)

    try:
        response = await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=7000,
        )
        if response is None:
            return "", False

        ct = response.headers.get("content-type", "").lower()
        if "application/pdf" in ct:
            return await response.body(), True
        
        await asyncio.sleep(0.5)
        html = await page.content()
        return html, False

    except Exception as e:
        print(f"[playwright] {type(e).__name__} {url}: {e}")
        return "", False
    finally:
        await page.close()


async def extract_pdf(pdf_bytes: bytes) -> tuple[str, str, str]:
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            title = pdf.metadata.get("Title", "") or ""
            if not title and pdf.pages:
                lines = [
                    l.strip()
                    for l in (pdf.pages[0].extract_text() or "").split("\n")
                    if l.strip()
                ]
                title = lines[0] if lines else ""
            desc = " ".join(text.split("\n")[:3])[:200]
        return text, title, desc
    except Exception as e:
        print(f"[pdf] {e}")
        return "", "", ""


_semaphore: Optional[asyncio.Semaphore] = None


def get_semaphore():
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(CONCURRENCY)
    return _semaphore


async def web_crawler(url: str) -> ScrapeResult:
    if not url:
        return ScrapeResult(
            url=url,
            text="",
            title="",
            description="",
            method="failed",
            error="empty url",
        )
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    async with get_semaphore():
        try:
            return await asyncio.wait_for(_race_fetch(url), timeout=PER_URL_TIMEOUT)
        except asyncio.TimeoutError:
            print(f"[crawler] hard timeout ({PER_URL_TIMEOUT}s) for {url}")
            return ScrapeResult(
                url=url,
                text="",
                title="",
                description="",
                method="failed",
                error="timeout",
            )


def is_thin(text: str, min_chars: int = 200) -> bool:
    return not text or len(text.strip()) < min_chars

def extract_html(html: str, url: str) -> tuple[str, str, str]:
    data = trafilatura.extract(
        html, url=url, with_metadata=False,
        output_format="markdown",
        include_tables=True,
        include_links=True,
        include_images=True,
        include_formatting=True,
        favor_precision=True
    )
    if data and not is_thin(data):
        metadata = trafilatura.extract(html, url=url, output_format="json", with_metadata=True)
        title, desc = "", ""
        if metadata:
            try:
                m = json.loads(metadata)
                title = m.get("title") or ""
                desc = m.get("description") or ""
            except: pass
        return title, desc, data
            
    fallback_txt = trafilatura.html2text(html) or ""
    return "Scraped Page", "", fallback_txt

async def _race_fetch(url: str) -> ScrapeResult:
    httpx_task = asyncio.create_task(fetch_httpx(url))
    pw_task = asyncio.create_task(fetch_playwright(url))

    title, desc, text = "", "", ""
    content, is_pdf, status = "", False, 0

    try:
        done, pending = await asyncio.wait(
            {httpx_task}, timeout=HTTPX_TIMEOUT, return_when=asyncio.FIRST_COMPLETED
        )

        if httpx_task in done:
            content, is_pdf, status = httpx_task.result()
            if status == 200 and content:
                if is_pdf:
                    pw_task.cancel()
                    t, d, tx = await extract_pdf(content)
                    return ScrapeResult(
                        url=url, text=tx, title=t, description=d, method="httpx-pdf"
                    )

                title, desc, text = extract_html(content, url)
                if not is_thin(text):
                    pw_task.cancel()
                    return ScrapeResult(
                        url=url, text=text, title=title, description=desc, method="httpx"
                    )
    except Exception:
        pass

    try:
        remaining = max(PER_URL_TIMEOUT - HTTPX_TIMEOUT - 0.1, 1.0)
        pw_content, pw_is_pdf = await asyncio.wait_for(pw_task, timeout=remaining)

        if pw_is_pdf and pw_content:
            t, d, tx = await extract_pdf(pw_content)
            return ScrapeResult(
                url=url, text=tx, title=t, description=d, method="playwright-pdf"
            )

        if pw_content:
            t, d, tx = extract_html(pw_content, url)
            if not is_thin(tx):
                return ScrapeResult(
                    url=url, text=tx, title=t, description=d, method="playwright"
                )
    except Exception:
        pass
    finally:
        if not httpx_task.done():
            httpx_task.cancel()
        if not pw_task.done():
            pw_task.cancel()

    best_text = text if not is_thin(text) else ""
    best_title = title

    return ScrapeResult(
        url=url,
        text=best_text,
        title=best_title if best_title else url[:50],
        description=desc if desc else "",
        method="partial" if best_text else "failed",
        error="" if best_text else f"no content extracted (httpx status={status})",
    )
 
async def shutdown():
    await close_httpx_client()
    await close_browser()


if __name__ == "__main__":
    result = asyncio.run(
        web_crawler(
            "https://en.wikipedia.org/wiki/Apple_Inc"
        )
    )
    print(result)