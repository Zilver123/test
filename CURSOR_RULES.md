WRITE TESTS FIRST, THEN THE CODE, THEN RUN THE TESTS AND UPDATE THE CODE UNTIL THE TESTS PASS. FINALLY RUN THE WORKING CODE LIVE FOR THE USER TO TRY

## 🔁 **1. Iterate Relentlessly**
* Always **test and iterate** until the goal is **fully met**.
* Don't stop at "working once." Ensure **robustness** and **edge cases** are handled.
* Favor **small, frequent updates** over large risky changes.

## 🔍 **2. Double-Check and Validate**
* **Review all outputs**, not just code. Validate behavior matches intent.
* **Check logs, console output, and side effects** for hidden issues.
* Use assertions or tests when possible. Consider writing quick unit tests.

## 🪛 **3. Debug Like a Detective**
* **Step back if stuck. Ask: what changed?**
* Use **logs, stack traces, and state inspection** to trace the source.
* **Isolate variables.** Reproduce in simpler form if needed.

## 🧠 **4. Always Think About Root Cause**
* Don't patch symptoms. **Trace back to what truly broke.**
* Think in systems: what assumptions are failing? What's not connected?

## 📜 **5. Follow the Source of Truth**
* **Always consult** `instructions.md`, README, spec docs, etc.
* Never assume — align behavior with the goal as described.
* If misaligned, **reframe the task**, then proceed.

## 🌐 **6. Search, Don't Stumble**
* Use docs, GitHub issues, Stack Overflow, and web search **freely**.
* Leverage examples, snippets, and known patterns. Avoid wasting cycles.

## 🔄 **7. Adapt When Stuck**
* If blocked: **pause, reframe**, and consider new approaches.
* Try top-down (architecture-first) or bottom-up (test/prototype-first).
* Let failures guide new insights — don't repeat the same path.

## 🧭 **8. Keep the Goal in Sight**
* **Regularly realign with the high-level goal.** Are you still moving toward it?
* Watch for rabbit holes. If deep in detail, ask: "Is this necessary?"

## 🧱 **9. Build in Steps, Log Progress**
* **Break work into visible steps** — even for agents, this helps trace logic.
* Leave **clear logs and intermediate outputs** to support transparency and traceability.

## 🧩 **10. Design for Continuity**
* Avoid brittle or hard-coded solutions. Think: "Can someone (or an agent) resume this?"
* Leave hints, TODOs, and breadcrumbs to support future autonomy or debugging.

## 11. Document & Handoff
* After any major change, bugfix, or discovery, update the relevant `.md` files:
  * `AGENT_LEARNINGS_AND_HANDBOOK.md` for new pitfalls, solutions, or best practices.
  * `AGENT_AGENT_TESTING_HANDBOOK.md` for new test patterns or debugging strategies.
  * `CHANGELOG_AGENT_NOTES.md` for a narrative of what/why/next.
* Leave clear TODOs, open questions, and context for the next agent or developer.

## 12. Maximize Observability
* All tools, endpoints, and tests should print/log their inputs, outputs, and errors.
* Prefer explicit, human-readable logs over silent failures or black-box steps.
* If a test or tool is not observable, refactor it.

## 13. Test With Real Data
* End-to-end and integration tests must use real product URLs, media, and prompts.
* A test that passes with only mocks is not considered robust.

## 14. Enforce API Contracts
* Always validate that API responses and tool outputs match the expected schema.
* If a contract changes, update all dependent code and documentation.

## 15. UI Robustness
* All UI changes must be tested for widget tree errors (e.g., ParentDataWidget issues).
* Document any UI pitfalls and solutions in the handbook.

## Optional (Advanced Autonomy)

### 🧠 "Agentify" Your Thinking
* Write code in a way that an agent could understand and continue.
* Be explicit in comments. Add `// Step 1`, `// Expect:`, `// Reason:` where helpful.

### 🕸️ Leverage Available Tools
* Use Cursor features like agent chat, diff view, context pinning, etc., **intentionally**.
* Combine human + agent workflows — don't try to be 100% autonomous when hybrid is faster. 