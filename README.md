# ai-redraft

一个专注于 **AI 改稿** 的本地 skill。

它解决的问题很窄：不要再在聊天框里反复解释“这句不对”“那段删掉”。打开稿子，直接划选原文写批注，完成后 Agent 读取批注并按位置修改原文。

Repository: <https://github.com/eddiearc/ai-redraft>

## 使用场景

- 小红书 / X / 公众号草稿改写
- 视频口播稿精修
- 文章、备忘录、方案、产品文案修改
- content-studio 文稿批注改稿

不做 git diff review，不做通用标注。

## 安装

```bash
git clone https://github.com/eddiearc/ai-redraft.git ~/.agents/skills/ai-redraft
mkdir -p ~/.codex/skills ~/.claude/skills
ln -sfn ~/.agents/skills/ai-redraft ~/.codex/skills/ai-redraft
ln -sfn ~/.agents/skills/ai-redraft ~/.claude/skills/ai-redraft
```

## 使用方式

```bash
python3 ~/.agents/skills/ai-redraft/server.py --source "/abs/path/to/draft.md" --timeout 600
```

浏览器打开后：

1. 划选需要修改的句子或段落
2. 写批注，比如“这句太像 AI”“删掉”“展开这个例子”
3. 点右上角「完成」
4. Agent 读取 `<draft>.annotations.json` 并修改原文

如果只是关闭浏览器窗口，服务会自动退出，但不会触发 Agent 改稿。

## 文件

```text
ai-redraft/
├── SKILL.md
├── README.md
├── server.py
├── template.html
├── favicon.svg
├── tests/
└── LICENSE
```
