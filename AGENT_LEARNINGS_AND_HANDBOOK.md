# 🧠 Agent Handbook: AI-Powered Short-Form Video Generator

## Overview
This document captures all key learnings, pitfalls, solutions, and best practices from the development and debugging of the AI-powered short-form video generator MVP. It is intended for future agents or developers to quickly get up to speed, understand the architecture, and continue or debug the project efficiently.

---

## 1. Project Architecture
- **Backend:** FastAPI, modular tools (scrape, analyze, storyboard, render), OpenCV + ffmpeg for video.
- **Frontend:** Flutter web, platform view for video, robust error handling.
- **Testing:** End-to-end, multi-stage, real-data tests ensure pipeline integrity.

---

## 2. Backend Learnings
### Video Rendering
- **Codec Pitfall:** OpenCV's default 'mp4v' codec is not browser-compatible (Chrome needs H.264/AVC).
- **Solution:** Always post-process with ffmpeg: `ffmpeg -y -i output.mp4 -c:v libx264 -pix_fmt yuv420p -movflags +faststart output_h264.mp4` and replace the original file.
- **Aspect Ratio:** Output videos must be 9:16 (e.g., 720x1280) for TikTok. Resize and pad images to fit.
- **Media Mapping:** Always map storyboard file paths to local file paths for correct frame order.

### API Contracts
- `/api/input` must return all media (uploaded + scraped) in `media_files`.
- `/api/render_video` must receive `media_files` in the same order as storyboard `media`.

### Debugging
- Use logs to trace every step: downloads, image reads, frame writes, ffmpeg output.
- If video is black in browser but plays locally, it's a codec/container issue.

---

## 3. Frontend Learnings
### Video Playback in Flutter Web
- **Pitfall:** Chrome shows black video if codec is wrong or if platform view is misused.
- **Solution:** Use a custom `WebVideoPlayer` widget with `HtmlElementView`, unique `viewType`, and always update `src` and call `load()` on change.
- **Sizing:** Set explicit width/height. Wrap in `SizedBox`, not `Expanded` inside `Center` (causes ParentDataWidget errors).
- **Error Handling:** Show clear UI errors for failed loads or overflows.
- **Deprecation:** Use `dart:ui_web` for `platformViewRegistry` (old import is deprecated).

### UI Pitfalls
- **RenderFlex Overflow:** Don't use `Expanded` inside `Center`. Use `SizedBox` or place `Expanded` inside a `Column` or `Row` only.

---

## 4. Testing & TDD
- **Multi-Stage Test:** Implement a test that covers scraping, media analysis, storyboard generation, and video rendering, using real product URLs and prompts.
- **Video Validation:** Use perceptual hash (phash) to match video frames to input images after resizing/padding.
- **Print Inputs/Outputs:** Always print all stage inputs/outputs for observability.

---

## 5. Debugging Checklist
- **Video black in browser:** Check codec (must be H.264/AVC in MP4).
- **Video not updating in UI:** Ensure video element is re-registered and `src` is updated with `load()`.
- **RenderFlex/ParentDataWidget errors:** Check widget tree; use `SizedBox` for fixed size, `Expanded` only in `Flex` parents.
- **API returns missing media:** Ensure all media (uploaded + scraped) are included in `media_files` and mapped correctly.

---

## 6. Next Steps & Extensibility
- Add audio support (AAC) for richer videos.
- Improve UI/UX: progress bars, error messages, mobile support.
- Modularize tools for easy replacement or upgrade.
- Document all new tools and endpoints with example inputs/outputs.

---

## 7. References
- See `instructions.md` for PRD and agent design.
- See `test_full_flow.py` for robust end-to-end tests.
- See `main.dart` for the latest video player implementation.

---

*This handbook should be updated by every agent or developer who makes significant changes or learns new lessons from the project.* 