#!/usr/bin/env python3
"""Launch Streamlit and capture synthetic-only application screenshots with Playwright."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def placeholder(path: Path, title: str, error: str) -> None:
    """Create a clearly labelled placeholder when browser automation is unavailable."""

    image = Image.new("RGB", (1440, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((70, 70, 1370, 830), outline="black", width=3)
    draw.text((110, 120), "SCREENSHOT PLACEHOLDER — browser capture unavailable", fill="black")
    draw.text((110, 180), title, fill="black")
    draw.multiline_text((110, 250), error[:700], fill="black", spacing=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def wait_for_health(url: str, timeout: int = 60) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urlopen(url, timeout=2) as response:  # noqa: S310 - local health endpoint only
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"Streamlit health endpoint did not become ready: {url}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--port", type=int, default=8510)
    args = parser.parse_args()
    output = args.root / "assets" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(args.port), "--server.headless", "true"]
    process = subprocess.Popen(command, cwd=args.root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_health(f"http://127.0.0.1:{args.port}/_stcore/health")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            page.goto(f"http://127.0.0.1:{args.port}", wait_until="networkidle")
            page.screenshot(path=str(output / "overview.png"), full_page=True)
            for label, filename in [
                ("Causal Design Lab", "causal_design_lab.png"),
                ("Precision Risk Evaluation", "prediction_evaluation.png"),
            ]:
                page.get_by_text(label, exact=True).first.click()
                page.wait_for_timeout(2500)
                page.screenshot(path=str(output / filename), full_page=True)
            browser.close()
        print(f"Captured screenshots in {output}")
    except Exception as exc:
        placeholder(output / "overview.png", "Overview", str(exc))
        placeholder(output / "causal_design_lab.png", "Causal Design Lab", str(exc))
        placeholder(output / "prediction_evaluation.png", "Precision Risk Evaluation", str(exc))
        print(f"Browser capture failed; labelled placeholders created: {exc}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
