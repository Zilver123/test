# 🤖 Agent Testing Handbook: Robust Testing for AI-Powered Video Pipelines

## Purpose
This guide details how an agent or developer can **robustly test** an AI-powered, multi-tool video generation pipeline (like the short-form video generator). It covers multi-stage TDD, real-data end-to-end (E2E) testing, common pitfalls, debugging, and best practices for automation and observability.

---

## 1. Testing Philosophy
- **Test Like a User:** Simulate real user flows (URL, uploads, prompt, edit, render).
- **Multi-Stage:** Test each tool/module in isolation and in full-pipeline integration.
- **Real Data:** Use real product URLs and media, not just mocks.
- **Observability:** Print/log all inputs/outputs at every stage.
- **Fail Loud:** Assert on every contract, output, and side effect.

---

## 2. Multi-Stage Test Pattern

### Stage 1: Input & Scraping
- **Input:** Product URL, creative prompt, (optionally) uploaded media.
- **Test:** Assert output includes scraped title, full description, and all media (uploaded + scraped URLs).
- **Print:** Inputs and outputs for traceability.

### Stage 2: Media Analysis
- **Input:** All media assets (local and remote).
- **Test:** Assert each media asset is described (non-empty, relevant description).
- **Print:** Media paths and descriptions.

### Stage 3: Storyboard Generation
- **Input:** JSON schema with product info, media, and prompt.
- **Test:** Assert storyboard contains a creative script, all media, and correct timings (sequential, non-overlapping, sum to total duration).
- **Print:** Storyboard JSON.

### Stage 4: Video Rendering
- **Input:** Storyboard JSON.
- **Test:** Assert video is correct length, all media are present in frames (use perceptual hash or pixel mean), and output is browser-compatible (H.264, 9:16).
- **Print:** Video path, duration, frame hashes, and any errors.

### Stage 5: Full Pipeline Analysis
- **Test:** Review all previous outputs. Assert all requirements are met. Print summary.

---

## 3. Example: Bulletproof E2E Test (Pytest)
```python
# See test_full_flow.py for a real example

def test_multistage_real_data_pipeline(tmp_path):
    # Stage 1: Input
    response = client.post("/api/input", data={...})
    assert ... # title, description, media
    print(response.json())
    # Stage 2: Media Analysis
    ...
    # Stage 3: Storyboard
    ...
    # Stage 4: Render Video
    ...
    # Stage 5: Analyze Video
    ...
```

---

## 4. Debugging & Observability
- **Print Everything:** Inputs, outputs, errors, logs.
- **Check Video in Browser:** If black, check codec/container.
- **Check Frame Content:** Use phash or pixel mean to match frames to input images.
- **Check API Contracts:** All media must be present and mapped.
- **Widget Errors:** In Flutter, check widget tree for ParentDataWidget issues.

---

## 5. Common Pitfalls & Solutions
| Pitfall | Solution |
|---------|----------|
| Video black in browser | Use H.264/AVC, yuv420p, +faststart |
| Media missing in video | Map storyboard file paths to local files |
| Widget overflow/errors | Use SizedBox, not Expanded in Center |
| Test passes with mocks only | Use real URLs and media |
| Frame mismatch | Resize/pad images before phash |

---

## 6. Automation & CI
- Run all tests on every commit.
- Fail build if any stage fails.
- Print all logs for review.

---

## 7. References
- See `instructions.md` for PRD and agent design.
- See `test_full_flow.py` for robust E2E test patterns.
- See `AGENT_LEARNINGS_AND_HANDBOOK.md` for project-specific learnings.

---

*Update this handbook as new tools, tests, or pitfalls are discovered.* 