# TikTok Boost Orchestrator

Multi-provider TikTok engagement automation bot with intelligent rotation, CAPTCHA bypass, and cooldown management.

## Features

- **Multi-Provider Rotation**: Automatically switches between Zefoy, Fireliker, Mytoolstown, and Vipto
- **Cooldown-Aware**: Monitors cooldown timers and rotates to available providers
- **CAPTCHA Bypass**: OCR solving for image CAPTCHAs, with fallback to 2captcha/Anti-Captcha APIs
- **Credit Farming**: Auto-farms credits on Mytoolstown before spending
- **Proxy Support**: Rotates proxies to avoid IP bans
- **Anti-Detection**: Stealth browser automation with human-like behavior
- **Statistics Tracking**: Tracks success/failure rates per provider and service
- **Auto-Restart**: Recovers from crashes automatically

## Supported Services

| Service    | Zefoy | Fireliker | Mytoolstown | Vipto |
|-----------|-------|-----------|-------------|-------|
| Followers | Yes   | Yes       | Yes         | Yes   |
| Hearts    | Yes   | Yes       | Yes         | Yes   |
| Views     | Yes   | Yes       | Yes         | Yes   |
| Shares    | Yes   | Yes       | No          | Yes   |
| Favorites | Yes   | No        | No          | Yes   |

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install Tesseract OCR (required for image CAPTCHA solving)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows:
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
```

## Configuration

Edit `config.yaml`:

```yaml
target:
  username: "your_tiktok_username"
  video_url: "https://www.tiktok.com/@username/video/1234567890"

services:
  - followers
  - views
  - likes
  - shares

providers:
  zefoy:
    enabled: true
    captcha_solver: "ocr"  # Options: ocr, 2captcha, anticaptcha, manual
    # api_key_2captcha: "YOUR_KEY"
    browser_mode: "headless"
```

## Usage

```bash
python main.py
```

The bot will:
1. Initialize all enabled providers
2. Solve any CAPTCHAs automatically
3. Start boosting your TikTok account
4. Rotate providers when cooldowns are hit
5. Report statistics every 5 minutes

## Project Structure

```
tiktok_boost_orchestrator/
├── config.yaml              # User configuration
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── README.md               # This file
├── core/
│   ├── captcha_solver.py    # CAPTCHA solving pipeline
│   ├── orchestrator.py      # Main rotation logic
│   ├── proxy_manager.py     # Proxy rotation
│   └── utils.py             # Utilities & statistics
├── providers/
│   ├── base.py              # Abstract base class
│   ├── zefoy.py             # Zefoy adapter (browser)
│   ├── fireliker.py         # Fireliker adapter (HTTP)
│   ├── mytoolstown.py       # Mytoolstown adapter (credits)
│   └── vipto.py             # Vipto adapter (browser)
└── sessions/
    └── .gitkeep             # Session persistence directory
```

## CAPTCHA Solving

### Free OCR (Default)
Uses Tesseract OCR with image preprocessing. Works for simple text CAPTCHAs.

### Paid Services
Configure API keys in `config.yaml`:
- **2captcha**: https://2captcha.com
- **Anti-Captcha**: https://anti-captcha.com

## Proxy Configuration

Add proxies to `config.yaml` or create a proxy list file:

```yaml
global:
  proxy_list_file: "proxies.txt"
```

`proxies.txt` format (one per line):
```
http://user:pass@host:port
socks5://host:port
host:port
```

## Troubleshooting

**Cloudflare blocks access:**
- Use residential proxies
- Switch to browser mode: `browser_mode: "visible"` to see what's happening
- Increase delay settings

**CAPTCHA solving fails:**
- Use paid CAPTCHA service for better accuracy
- Switch to manual mode for debugging

**Provider shows "Not working":**
- The site may have changed their layout
- Check browser mode to see the actual page state
- Update selectors in the provider adapter

## License

For educational purposes only.
