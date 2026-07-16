#!/usr/bin/env python3
"""Launch Streamlit and capture synthetic-only application screenshots with Playwright."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CHROME_PATH = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a broadly available system font and fall back safely."""
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def placeholder(path: Path, title: str, bullets: list[str], accent: tuple[int, int, int]) -> None:
    """Create a clean preview card when browser automation is unavailable."""
    width, height = 1440, 900
    image = Image.new("RGB", (width, height), (245, 247, 250))
    draw = ImageDraw.Draw(image)
    font_small = load_font(24)
    font_body = load_font(32)
    font_heading = load_font(34, bold=True)
    font_title = load_font(44, bold=True)

    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=28, fill="white")
    draw.rounded_rectangle((90, 90, width - 90, 186), radius=22, fill=accent)
    draw.text((120, 116), "first1000days-linked-cohort-lab", fill="white", font=font_small)
    draw.text((120, 144), title, fill="white", font=font_title)

    draw.rounded_rectangle((90, 225, width - 90, 810), radius=24, outline=(222, 226, 232), width=2)
    draw.text((125, 260), "Synthetic methods demonstration", fill=(33, 37, 41), font=font_heading)
    draw.text(
        (125, 318),
        "Preview generated because automated browser capture was unavailable in this environment.",
        fill=(90, 98, 108),
        font=font_body,
    )

    top = 395
    for bullet in bullets:
        draw.rounded_rectangle((125, top, 135, top + 10), radius=5, fill=accent)
        draw.text((160, top - 22), bullet, fill=(45, 52, 54), font=font_body)
        top += 90

    draw.text(
        (125, 745),
        "Run python scripts/capture_screenshots.py locally to replace this preview with a live app screenshot.",
        fill=(110, 118, 129),
        font=font_small,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def streamlit_log_tail(process: subprocess.Popen[str], limit: int = 2000) -> str:
    """Return the most useful available tail of Streamlit startup output."""
    if process.stdout is None:
        return "No Streamlit stdout was captured."
    output = process.stdout.read()
    output = output.strip()
    if not output:
        return "No Streamlit startup output was captured."
    return output[-limit:]


def wait_for_health(process: subprocess.Popen[str], url: str, timeout: int = 60) -> None:
    """Wait for Streamlit health endpoint to become ready."""
    start = time.time()
    while time.time() - start < timeout:
        if process.poll() is not None:
            tail = streamlit_log_tail(process)
            raise RuntimeError(f"Streamlit exited before becoming ready (exit code {process.returncode}).\n{tail}")
        try:
            with urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    tail = streamlit_log_tail(process)
    raise TimeoutError(f"Streamlit health endpoint did not become ready: {url}\n{tail}")


def capture_screenshots_with_playwright(output: Path, port: int) -> None:
    """Capture screenshots using Playwright with Chrome."""
    from playwright.sync_api import sync_playwright
    
    if not CHROME_PATH.exists():
        raise FileNotFoundError(f"Chrome not found at {CHROME_PATH}. Please install Google Chrome.")
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME_PATH),
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1440,900"
            ]
        )
        
        try:
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1
            )
            page = context.new_page()
            
            # صفحه اصلی
            print("📄 Navigating to main page...")
            page.goto(f"http://127.0.0.1:{port}", wait_until="networkidle")
            
            # ⭐ صبر ۱۰ ثانیه برای بارگذاری کامل
            print("⏳ Waiting 10 seconds for page to fully load...")
            time.sleep(20)
            
            # اسکرین‌شات اصلی
            print("📸 Capturing overview.png...")
            page.screenshot(path=str(output / "overview.png"), full_page=True)
            print("✅ overview.png captured")
            
            # اسکرین‌شات سایر صفحات
            for label, filename in [
                ("Causal Design Lab", "causal_design_lab.png"),
                ("Precision Risk Evaluation", "prediction_evaluation.png"),
            ]:
                try:
                    print(f"📄 Navigating to '{label}'...")
                    page.get_by_text(label, exact=True).first.click()
                    
                    # ⭐ صبر ۱۰ ثانیه برای بارگذاری هر صفحه
                    print("⏳ Waiting 10 seconds for page to load...")
                    time.sleep(20)
                    
                    print(f"📸 Capturing {filename}...")
                    page.screenshot(path=str(output / filename), full_page=True)
                    print(f"✅ {filename} captured")
                except Exception as e:
                    print(f"⚠️ Could not capture {filename}: {e}")
            
        finally:
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--port", type=int, default=8510)
    args = parser.parse_args()
    output = args.root / "assets" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    
    # راه‌اندازی Streamlit
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(args.port),
        "--server.headless",
        "true",
        "--logger.level",
        "error",
    ]
    
    process = subprocess.Popen(
        command, 
        cwd=args.root, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    try:
        print(f"⏳ Starting Streamlit on port {args.port}...")
        wait_for_health(process, f"http://127.0.0.1:{args.port}/_stcore/health")
        print("✅ Streamlit is ready!")
        
        print("📸 Capturing screenshots with Playwright...")
        capture_screenshots_with_playwright(output, args.port)
        print(f"🎉 All screenshots captured successfully in {output}")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Please install Google Chrome from: https://www.google.com/chrome/")
        create_placeholders(output)
        
    except Exception as exc:
        print(f"⚠️ Browser capture failed; creating preview cards instead: {exc}")
        create_placeholders(output)
        
    finally:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            print("⚠️ Streamlit process killed")


def create_placeholders(output: Path) -> None:
    """Create placeholder images for all pages."""
    placeholder(
        output / "overview.png",
        "Overview",
        [
            "Synthetic linked-cohort construction with transparent first-1,000-days definitions.",
            "Linkage-quality auditing, cohort flow reporting, and architecture overview.",
            "No real patient, education, hospital, or administrative data.",
        ],
        accent=(32, 99, 155),
    )
    placeholder(
        output / "causal_design_lab.png",
        "Causal Design Lab",
        [
            "Side-by-side synthetic comparison of naive, adjusted, and sibling designs.",
            "Known simulation truth retained outside routine analyses.",
            "Results labelled as methods demonstration rather than empirical inference.",
        ],
        accent=(34, 139, 120),
    )
    placeholder(
        output / "prediction_evaluation.png",
        "Precision Risk Evaluation",
        [
            "Family-grouped discrimination, calibration, and subgroup summaries.",
            "Aggregate evaluation only with no individual risk ranking or intervention use.",
            "Synthetic early-life educational-trajectory target rather than suicide prediction.",
        ],
        accent=(180, 95, 45),
    )
    print("📋 Polished preview cards created successfully")


if __name__ == "__main__":
    main()