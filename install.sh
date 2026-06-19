#!/bin/bash
set -e

echo "📦 安裝 youtube-sub CLI 工具..."
uv tool install git+https://github.com/enid/youtube-sub

echo "🤖 安裝 Claude Code Skill..."
mkdir -p ~/.claude/skills/youtube-sub
cp skill/SKILL.md ~/.claude/skills/youtube-sub/

echo "✅ 安裝完成！"
echo "   CLI 工具：youtube-sub --help"
echo "   Claude Code：直接輸入 YouTube URL 即可"
