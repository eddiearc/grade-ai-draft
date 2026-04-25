---
name: grade-ai-draft
description: Use when the user wants to grade or revise an AI-written article, post, script, memo, plan, or other prose draft by marking exact passages and giving targeted rewrite comments. Triggers include "批改作业", "批改 AI 稿", "批改 AI 写的稿子", "帮我改稿", "批注改稿", "精准改稿", and "grade AI draft".
---

# 批改作业 / Grade AI Draft

## Overview

This skill treats an AI-written draft like homework. The human acts as the teacher: mark exact spans, write grading comments, click 完成, and let the agent revise the source file according to those comments.

Use it for AI-generated prose drafts, not general file review. The promise is: **人类负责批改判断，Agent 负责按位置改稿**.

## When to Use

Use this skill when the user wants to grade and revise AI-written:

- 小红书 / X / 公众号 / 视频口播稿
- article drafts, newsletters, essays, memos
- product copy, plans, proposals, README prose

Do not use this skill for git diff review, code review, or broad-purpose annotation workflows. If the user asks for code/diff review, use a review workflow instead.

## Core Flow

```
用户: 用批改作业帮我批改这篇 AI 稿 <draft-file>
  ↓
Agent resolves the absolute draft path
  ↓
Agent tells the user how to operate the UI
  ↓
Agent starts the local revision UI in the foreground and synchronously waits
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

**Important:** run the server in the foreground and synchronously wait for it to exit. Do not launch it with `&`, `nohup`, `disown`, or a detached terminal. The UI is served by this process; if the command returns before the user clicks 完成, the browser page may stop working.

Because the foreground command blocks until completion, give the user instructions **before** starting the server, not after.

```bash
python3 ~/.agents/skills/grade-ai-draft/server.py --source "<ABSOLUTE_DRAFT_PATH>" --timeout 600
```

If `~/.agents` is not available in the current agent, use the local skill path that contains this `SKILL.md`.

## User Instructions

Before starting the server, tell the user:

```
我现在会打开批改作业界面，并同步等待你完成。

操作：
1. 划选需要修改的句子或段落
2. 写下具体意见，比如「这句太像 AI」「删掉」「展开这个例子」「改得更口语」
3. 全部标完点右上角「完成」
4. 我会按你的批注直接修改原文
```

Then start the foreground server command and wait. When it exits with code `0`, read the sidecar JSON and revise the draft.

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
- For AI-generated drafts, remove generic AI phrasing and keep the user's voice, examples, and judgment visible.
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

## After Grading Revisions

After applying the grading comments, suggest the next concrete step:

- generate platform titles
- turn the draft into a video outline
- prepare a Xiaohongshu post package
- archive after publishing
