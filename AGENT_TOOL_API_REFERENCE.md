# 🛠️ Agent & Tool API Reference

This document provides explicit input/output schemas and usage notes for all major agent and tool functions in the AI-powered short-form video generator pipeline. Use this as the source of truth for agent coding, debugging, and handoff.

---

## 1. Tool: `scrape_url_tool`
**Description:** Scrapes product metadata and media assets from an e-commerce URL.

**Input:**
| Name | Type | Description | Required | Example |
|------|------|-------------|----------|---------|
| url  | str  | Product page URL | Yes | "https://example.com/product/123" |

**Output:**
```json
{
  "title": "Product Name",
  "description": "Full product description...",
  "images": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ]
}
```
**Errors:**
- 400 if URL is invalid or unreachable.
- 404 if product not found.

---

## 2. Tool: `analyze_media_tool`
**Description:** Uses LLM/Vision model to describe uploaded or scraped media assets.

**Input:**
| Name | Type | Description | Required | Example |
|------|------|-------------|----------|---------|
| media_path | str | Path or URL to image/video | Yes | "uploads/image1.jpg" |

**Output:**
```json
{
  "description": "A plush toy on a white background."
}
```
**Errors:**
- 400 if file is missing or unreadable.
- 422 if media type is unsupported.

---

## 3. Tool: `generate_storyboard_tool` (LLM)
**Description:** Uses LLM to generate a storyboard (script, timings, media mapping) from product info, media, and creative prompt.

**Input:**
| Name | Type | Description | Required | Example |
|------|------|-------------|----------|---------|
| creative_prompt | str | User's creative prompt | Yes | "10 sec TikTok ad" |
| product | dict | {"title": str, "description": str} | Yes | {"title": "Plush", "description": "..."} |
| media | list | List of {"path": str, "description": str} | Yes | [{"path": "uploads/img1.jpg", "description": "..."}] |

**Output:**
```json
{
  "script": "Meet our new plush! ...",
  "media": [
    {"start": "00:00", "end": "00:03", "file": "uploads/img1.jpg"},
    {"start": "00:03", "end": "00:06", "file": "uploads/img2.jpg"}
  ]
}
```
**Notes:**
- Timings must be sequential, non-overlapping, and sum to total duration.
- Script should be creative and based on prompt/product info.
- All media in input should be mapped in output.

**Errors:**
- 400 if input is missing required fields.
- 422 if LLM output is not valid JSON or missing fields.

---

## 4. Tool: `render_video_tool`
**Description:** Renders a video from the storyboard and media files. Uses OpenCV + ffmpeg.

**Input:**
| Name | Type | Description | Required | Example |
|------|------|-------------|----------|---------|
| storyboard | dict | Storyboard JSON (see above) | Yes | { ... } |
| media_files | list | List of local file paths (ordered as in storyboard) | Yes | ["uploads/img1.jpg", ...] |

**Output:**
```json
{
  "video_path": "uploads/output.mp4"
}
```
**Notes:**
- Output video is 9:16, H.264, browser-compatible.
- All storyboard media must be present in video.

**Errors:**
- 400 if files are missing or unreadable.
- 500 if video rendering fails.

---

## 5. Agent Orchestration: `video_builder_agent`
**Description:** Orchestrates the above tools to process user input, generate a storyboard, and render the video.

**Input:**
| Name | Type | Description | Required | Example |
|------|------|-------------|----------|---------|
| product_url | str | Product page URL | Optional | "https://example.com/product/123" |
| creative_prompt | str | User's creative prompt | Yes | "10 sec TikTok ad" |
| media | list | Uploaded media files | Optional | ["uploads/img1.jpg"] |

**Output:**
```json
{
  "product": { ... },
  "media": [ ... ],
  "storyboard": { ... },
  "video_path": "uploads/output.mp4"
}
```
**Notes:**
- Follows the full flow: scrape → analyze → storyboard (LLM) → render.
- Returns all intermediate and final outputs for observability.

**Errors:**
- Propagates errors from any tool in the chain.

---

*Update this reference as new tools or agent functions are added or changed.* 