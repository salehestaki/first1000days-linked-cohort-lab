# Screenshot capture instructions

Run `python scripts/capture_screenshots.py`. The script launches Streamlit on a local port, waits for the health endpoint, uses the installed Chromium browser through Playwright, captures Overview, Causal Design Lab and Precision Risk Evaluation, then stops the server. If browser automation is unavailable, it creates clearly labelled placeholders rather than fabricated application screenshots. Before manual capture, verify that only synthetic identifiers are visible.
