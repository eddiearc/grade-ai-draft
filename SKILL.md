---
name: ai-redraft
description: Use when the user wants to revise an article, post, script, memo, plan, or other prose draft by marking exact passages and giving targeted rewrite comments. Triggers include "帮我改稿", "批注改稿", "精准改稿", "这篇帮我批注后修改", "让 AI 按批注改稿", "review my draft", and content-studio draft revision.
---

# AI Redraft

## Overview

This skill turns vague "帮我改一下" editing into precise human-feedback revision. The user marks exact spans in a local draft, writes rewrite comments, clicks 完成, and the agent revises the source file according to those comments.

Use it for prose drafts, not general file review. The promise is: **人负责判断，AI 负责按位置改稿**.

## When to Use

Use this skill when the user wants to polish or rewrite:

- 小红书 / X / 公众号 / 视频口播稿
- article drafts, newsletters, essays, memos
- product copy, plans, proposals, README prose
- content-studio files under `content-studio/01-内容生产/待深化的选题/`

Do not use this skill for git diff review, code review, or broad-purpose annotation workflows. If the user asks for code/diff review, use a review workflow instead.

## Core Flow

```
用户: 帮我批注改稿 <draft-file>
  ↓
Agent resolves the absolute draft path
  ↓
Agent starts the local revision UI and waits
  ↓
User highlights draft passages and writes rewrite comments
  ↓
User clicks 完成
  ↓
Agent reads <draft-file>.annotations.json
  ↓
Agent edits the draft in place and reports what changed
```

## Start the Revision UI

Always use `--source`. Do not use diff mode.

```bash
python3 ~/.agents/skills/ai-redraft/server.py --source "<ABSOLUTE_DRAFT_PATH>" --timeout 600
```

If `~/.agents` is not available in the current agent, use the local skill path that contains this `SKILL.md`.

## User Instructions

After starting the server, tell the user:

```
改稿批注界面已经打开，我会等你完成。

操作：
1. 划选需要修改的句子或段落
2. 写下具体意见，比如「这句太像 AI」「删掉」「展开这个例子」「改得更口语」
3. 全部标完点右上角「完成」
4. 我会按你的批注直接修改原文
```

## Annotation JSON

The server writes `<draft-file>.annotations.json`:

```json
{
  "source_file": "/abs/path/draft.md",
  "source_name": "draft.md",
  "annotations": [
    {
      "id": "ann-1",
      "seq": 1,
      "selected_text": "被选中的原文",
      "context_before": "前面最多 30 字",
      "context_after": "后面最多 30 字",
      "note": "用户写的改稿意见",
      "created_at": "2026-04-25T..."
    }
  ]
}
```

Use `context_before + selected_text + context_after` to locate the exact passage before editing.

## Rewrite Rules

- Treat user comments as editorial intent, not optional suggestions.
- Preserve the user's original meaning unless the comment asks for a stronger rewrite.
- Prefer concrete, natural wording over polished AI-sounding summaries.
- For content-studio drafts, follow the local anti-AI style rules: keep first-person texture, avoid fake drama, and avoid generic "不是……而是……" framing.
- If a comment says "删掉", remove the selected passage unless doing so breaks necessary logic.
- If a comment says "展开", add only details supported by the draft or known context; do not invent cases.
- If a comment is ambiguous, make the smallest defensible edit and mention the assumption.

## Completion Report

After editing, report:

- how many annotations were applied
- the main types of changes, not every tiny wording tweak
- any annotations you could not apply precisely

For 5 or fewer annotations, mention each one briefly. For more than 5, group them by rewrite type.

## Exit Codes

- `0`: completed after the user clicks 完成; read sidecar and revise the draft
- `1`: timeout; ask whether to reopen the revision UI
- `2`: browser closed before 完成; the UI service has shut down and the draft should not be edited
- `3`: user cancelled; do not edit
- `4`: port conflict; retry with `--port 7891`, then `7892`

## After Content-Studio Revisions

If the file is a content-studio draft, suggest the next concrete step:

- generate platform titles
- turn the draft into a video outline
- prepare a Xiaohongshu post package
- archive after publishing
