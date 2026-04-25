# 批改作业 / Grade AI Draft

一个专注于 **批改 AI 稿件** 的本地 skill。

把 AI 写出来的稿子当成作业。人类像老师一样划出问题、写下批改意见，Agent 再按这些批注回到原文里修改。

Repository: <https://github.com/eddiearc/grade-ai-draft>

## 使用场景

- AI 生成了一篇稿子，但你想像老师批改作业一样逐句指出问题
- 想保留原文结构，只改某几句、某几段，而不是让 AI 整篇重写
- 想把“这里不像我”“这句太 AI”“这个例子不对”变成明确的修改意见
- 适合文章、帖子、视频口播稿、产品文案、方案、备忘录等 AI 初稿

不做 git diff review，不做通用标注。

## 安装

推荐用 Skills CLI 安装：

```bash
npx skills add eddiearc/grade-ai-draft
```

如果你不想自己处理命令行，也可以直接把这句话发给 Agent：

```text
请从 https://github.com/eddiearc/grade-ai-draft 安装 grade-ai-draft skill，并确保 Claude 和 Codex 都能识别。
```

## 使用方式

对 Agent 说：

```text
用批改作业帮我批改这篇 AI 稿 <稿件路径>
```

Agent 会启动本地批注界面。你只需要：

1. 划选需要修改的句子或段落
2. 写批注，比如“这句太像 AI”“删掉”“展开这个例子”
3. 点右上角「完成」
4. Agent 读取 `<draft>.annotations.json` 并修改原文

Agent 也可以直接用下面的命令启动界面：

```bash
python3 ~/.agents/skills/grade-ai-draft/server.py --source "/abs/path/to/draft.md" --timeout 600
```

如果只是关闭浏览器窗口，服务会自动退出，但不会触发 Agent 改稿。

## 文件

```text
grade-ai-draft/
├── SKILL.md
├── README.md
├── server.py
├── template.html
├── favicon.svg
├── tests/
└── LICENSE
```
