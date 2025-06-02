# 📚 Project Documentation: AI-Powered Short-Form Video Generator

## Overview
This project generates short-form marketing videos from product URLs, uploaded media, and creative prompts using an AI agent and modular tools. Users can edit the storyboard and regenerate videos iteratively.

---

## Architecture
- **Backend:** FastAPI, modular tools (scrape, analyze, storyboard, render), OpenCV + ffmpeg for video.
- **Frontend:** Flutter web, custom video player, storyboard editor.
- **Agent:** Orchestrates tools for scraping, analysis, storyboard, and rendering.

---

## File Structure
```
video_mvp/
├── backend/
│   ├── main.py
│   ├── agents/
│   ├── tools/
│   ├── services/
│   └── utils/
├── frontend/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── pages/
│   │   └── components/
└── README.md
```

---

## Backend
### Key Tools
- **scrape_url_tool:** Scrapes product metadata and images from e-commerce URLs.
- **analyze_media_tool:** Uses AI to describe uploaded/scraped media.
- **generate_storyboard_tool:** Generates a storyboard (script, timings, media mapping).
- **render_video_tool:** Renders video from storyboard using OpenCV + ffmpeg.

### API Endpoints
- `POST /api/input`: Accepts product URL, prompt, and media. Returns product info, media, and storyboard.
- `POST /api/render_video`: Accepts storyboard and media files. Returns video path.

---

## Frontend
- **Flutter web app** with:
  - Input form (URL, prompt, uploads)
  - Storyboard editor
  - Video preview (custom HtmlElementView for web)
- **Best Practices:**
  - Use absolute URLs for video playback
  - Handle widget tree errors (see AGENT_LEARNINGS_AND_HANDBOOK.md)

---

## Testing Strategy
- **Multi-Stage E2E Test:** Covers scraping, analysis, storyboard, and video rendering with real data.
- **Video Validation:** Uses perceptual hash to match video frames to input images.
- **Prints all inputs/outputs for observability.**

---

## Developer Setup
1. **Clone repo & install dependencies:**
   - Python: `pip install -r requirements.txt`
   - Flutter: `flutter pub get`
2. **Start backend:**
   - `uvicorn video_mvp.backend.main:app --reload --port 8000`
3. **Start frontend:**
   - `cd video_mvp/frontend && flutter run -d chrome`
4. **Run tests:**
   - `pytest -s video_mvp/backend/tests/test_full_flow.py`

---

## Extensibility
- Add new tools by following the `@function_tool` pattern.
- Modularize and document all new endpoints.
- Update tests and handbooks with every major change.

---

## References
- See `instructions.md` for PRD and agent design.
- See `AGENT_LEARNINGS_AND_HANDBOOK.md` for troubleshooting and best practices.
- See `test_full_flow.py` for E2E test patterns.

---

*Keep this documentation up to date as the project evolves.* 