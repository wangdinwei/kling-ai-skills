# Kling AI Skills · 可灵 AI 视频生成技能包

A curated set of [Hermes Agent](https://hermes-agent.nousresearch.com/docs) skills for building
production pipelines on **Kling AI (可灵)** — text-to-image, text-to-video, character reference
(MultiShot), lipsync MV assembly, prompt quality gating, and API integration.

> All skills are sanitized: **no API keys, no personal data, no client data.** Plug in your own
> `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` via environment variables.

## Skills

| Skill | What it does |
|---|---|
| `kling-character-image-workflow` | Generate multi-angle character reference images via AI MultiShot, then register them as reusable Kling **elements** |
| `kling-character-image-pipeline` | End-to-end character image generation pipeline |
| `kling-prompt-quality-gate` | 8-point quality checklist + style templates + validation for Kling video prompts |
| `kling-prompt-post-enhance` | Post-enhance / rewrite Kling prompts |
| `kling-cross-shot-consistency-prompt` | Keep a character/scene consistent across shots |
| `kling-duration-rounding` | Handle Kling clip duration rounding quirks |
| `kling-api-balance-query` | Query Kling account balance / quota via API |
| `kling-cli-install-china` | Install the Kling CLI behind the China network |
| `kling-lipsync-mv-assembly` | Lipsync music-video assembly (face-ratio measurement, param pitfalls, segment → concat → burn subtitles) |
| `kling-turbo-trial-video-pipeline` | Turbo trial video pipeline |

## Authentication (JWT, HS256)

Kling's API uses a signed JWT (not a plain bearer token):

```python
import json, base64, hmac, hashlib, time
ak = "YOUR_KLING_ACCESS_KEY"      # from env, never hardcode
sk = "YOUR_KLING_SECRET_KEY"
now = int(time.time())
header = {"alg": "HS256", "typ": "JWT"}
payload = {"iss": ak, "exp": now + 1800, "nbf": now - 5}
b64 = lambda d: base64.urlsafe_b64encode(d).decode().rstrip("=")
hb = b64(json.dumps(header, separators=(",", ":")).encode())
pb = b64(json.dumps(payload, separators=(",", ":")).encode())
sig = hmac.new(sk.encode(), f"{hb}.{pb}".encode(), hashlib.sha256).digest()
token = f"{hb}.{pb}.{b64(sig)}"   # valid ~30 min
```

- Base URL: `https://api-beijing.klingai.com`
- Key endpoints covered: `POST /v1/images/generations`, `POST /v1/general/ai-multi-shot`,
  `POST /v1/general/advanced-custom-elements`, `GET /v1/general/ai-multi-shot/{task_id}`, video generation, balance query.

## Usage

Copy any skill folder into your Hermes skills directory and export your keys:

```bash
export KLING_ACCESS_KEY="..."   # your own
export KLING_SECRET_KEY="..."
cp -r kling-character-image-workflow ~/.hermes/profiles/<profile>/skills/
```

## License

MIT — see [LICENSE](LICENSE).
