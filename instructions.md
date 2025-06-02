# 📍 Product Requirements Document (PRD): AI-Powered Short-Form Video Generator

## 🌟 Overview

This MVP project enables users to generate engaging short-form videos for product marketing using an AI agent powered by the OpenAI Agents SDK. The application accepts product URLs, uploaded media, and a creative prompt, producing a storyboard and final video output. Users can iteratively edit and regenerate videos through a storyboard interface.

## ✅ Core Features

### 1. User Flow

#### a. Input Phase

**User inputs:**
- Product page URL (optional)
- Uploaded media assets (images, video snippets)
- Creative prompt (e.g., "Create a 10-second TikTok ad")

**System actions:**
- Scrapes and analyzes the product page
- Processes and understands uploaded media
- Generates a storyboard with timing, script, and asset mapping using AI agent
- Creates a video from storyboard with tool

#### b. Edit Phase

Users receive an editable text storyboard:

```
[STORYBOARD]
[SCRIPT]
"Get yours today!"
[MEDIA]
00:00-00:03 - /uploads/image1.jpg
00:03-00:06 - /uploads/video1.mp4
[END STORYBOARD]
```

- User modifies storyboard text and clicks regenerate
- System regenerates the video from updated storyboard

## 🧐 AI Agent Design

### Single Agent: `video_builder_agent`

This agent uses multiple tools to modularly accomplish its tasks.

#### Agent Declaration Example (Agents SDK)

```python
from agents import Agent, FileSearchTool, Runner, WebSearchTool

agent = Agent(
    name="Assistant",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["VECTOR_STORE_ID"],
        ),
    ],
)

async def main():
    result = await Runner.run(agent, "Which coffee shop should I go to, taking into account my preferences and the weather today in SF?")
    print(result.final_output)
```

## 🔧 Tools

### 1. `scrape_url_tool`

Scrapes product metadata and media assets from e-commerce URLs.

### 2. `analyze_media_tool`

Uses OpenAI Vision or Replicate to describe uploaded media.

**Example (OpenAI Vision):**

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-4.1-mini",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "What's in this image?"},
            {"type": "input_image", "image_url": "https://example.com/image.jpg"}
        ]
    }]
)
print(response.output_text)
```

### 3. `generate_storyboard_tool`

Generates storyboard from input metadata, media descriptions, and user prompt.

**Storyboard Format:**

```
[STORYBOARD]
[SCRIPT]
"Introducing our new gadget!"
[MEDIA]
00:00-00:03 - image1.jpg
00:03-00:06 - video1.mp4
[END STORYBOARD]
```

### 4. `render_video_tool`

Renders the final video from storyboard using Replicate models.

**Example:**

```python
import replicate

output = replicate.run(
  "black-forest-labs/flux-schnell",
  input={"prompt": "a cinematic product reveal"}
)
with open("output.mp4", "wb") as f:
    f.write(output[0].read())
```

## 📁 File Structure

```
video_mvp/
|
├── backend/
│   ├── main.py                    # API endpoints
│   ├── agents/
│   │   └── video_agent.py         # Agent and tool registration
│   ├── tools/
│   │   ├── scrape_url.py
│   │   ├── analyze_media.py
│   │   ├── generate_storyboard.py
│   │   └── render_video.py
│   ├── services/
│   │   └── replicate_client.py
│   └── utils/
│       └── media_utils.py
|
├── frontend/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── pages/
│   │   │   ├── input_page.dart
│   │   │   └── editor_page.dart
│   │   └── components/
│   │       ├── storyboard_editor.dart
│   │       └── video_preview.dart
|
└── README.md
```

## 📗 Documentation and Examples

All tools must include testable example inputs and expected outputs. Where possible, tools use simple decorators like `@function_tool` for registration.

**Example Tool Pattern:**

```python
@function_tool
def scrape_url(url: str) -> dict:
    # return product title, description, images
```

## 🚀 Agent Best Practices Followed

| Principle            | Implementation Detail                                     |
| -------------------- | --------------------------------------------------------- |
| One Agent            | `video_builder_agent` with tools, no multi-agent setup    |
| Modular Tooling      | Tools are standalone, individually testable               |
| Iterative Generation | Editing flow enables iterative storyboard-to-video cycles |
| Simplicity First     | MVP avoids advanced scene detection or multi-modal chains |
| Observability        | Logs all tool input/output via middleware for debugging   |
| Extensibility        | Tools can be improved/replaced without agent redesign     |

---

## Agent/Tool Best Practices & Handoff Requirements

1. **Observability:**
   - All tools and agents must log their inputs, outputs, and errors for every invocation. This is required for debugging, agent handoff, and robust automation.

2. **Testing:**
   - Every tool and the full pipeline must have real-data, multi-stage, end-to-end tests. Tests must print all stage inputs/outputs and validate against the PRD.

3. **Documentation & Handoff:**
   - After any major change, update the relevant `.md` files (handbooks, changelogs, docs) with new learnings, pitfalls, or changes to agent/tool logic.

4. **API Contract Enforcement:**
   - All API endpoints and tool outputs must strictly follow the documented schema. If a contract changes, update all dependent code, docs, and tests.

5. **Agent SDK Compliance:**
   - All agent and tool code must follow the [Agents SDK documentation](agents.mdc) for registration, invocation, and modularity. Use `@function_tool` decorators and explicit tool schemas.

6. **UI/Frontend Robustness:**
   - All UI changes (especially for Flutter web) must be tested for widget tree errors and documented in the handbook if any pitfalls are found.

7. **Versioning and Changelog:**
   - When making breaking changes to tools, agents, or APIs, increment the version and document the change in `CHANGELOG_AGENT_NOTES.md`.

---

**Always consult `CURSOR_RULES.md` for the latest project rules and agent/developer expectations.**

*Would you like this PRD exported as a PDF or shared as a collaboration doc?*