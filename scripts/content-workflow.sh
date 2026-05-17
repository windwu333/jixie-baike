#!/usr/bin/env bash
# ==============================================================
# 机械师大百科 · 本地内容生成→审稿→发布工作流
# ==============================================================
# 用法:
#   ./content-workflow.sh generate  "文章标题"   → 生成草稿到 content/website/ 和 content/wechat/
#   ./content-workflow.sh list                   → 列出所有待审核内容
#   ./content-workflow.sh review  <文件名>        → 标记为已审
#   ./content-workflow.sh publish <文件名>        → 发布（push到GitHub / 标记为已发布）
#   ./content-workflow.sh status                 → 查看内容状态计数
# ==============================================================

set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONTENT_DIR="$BASE_DIR/content"
WEBSITE_DIR="$CONTENT_DIR/website"
WECHAT_DIR="$CONTENT_DIR/wechat"
PUBLISHED_DIR="$CONTENT_DIR/published"

mkdir -p "$WEBSITE_DIR" "$WECHAT_DIR" "$PUBLISHED_DIR"

cmd_generate() {
    local title="$1"
    if [ -z "$title" ]; then
        echo "❌ 用法: $0 generate \"文章标题\""
        exit 1
    fi

    local slug="$(echo "$title" | sed 's/[^a-zA-Z0-9一-龥]/-/g' | sed 's/-\+/-/g' | sed 's/^-//;s/-$//')"
    local date_str="$(date +%Y-%m-%d)"
    local ts="$(date +%Y%m%d_%H%M)"
    local wf="${WEBSITE_DIR}/${date_str}-${slug}_DRAFT.md"
    local wxf="${WECHAT_DIR}/${date_str}-${slug}_DRAFT.md"

    echo "📝 准备生成: $title"
    echo "  网站版: $(basename "$wf")"
    echo "  公众号: $(basename "$wxf")"
    echo ""
    echo "请在以下区域粘贴 AI 生成的网站版内容（Hugo Markdown 格式），"
    echo "输入完成后按 Ctrl+D 提交："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Read from stdin for website content
    cat > "$wf"
    echo "" >> "$wf"
    echo "---" >> "$wf"
    echo "_workflow:" >> "$wf"
    echo "  status: draft" >> "$wf"
    echo "  created: $ts" >> "$wf"
    echo "  platform: website" >> "$wf"
    echo "---" >> "$wf"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ 网站版草稿已保存: $(basename "$wf")"
    echo ""
    echo "现在粘贴公众号精简版内容（500-1500字，纯文本格式），"
    echo "输入完成后按 Ctrl+D 提交："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Read from stdin for WeChat content
    cat > "$wxf"
    echo "" >> "$wxf"
    echo "---" >> "$wxf"
    echo "_workflow:" >> "$wxf"
    echo "  status: draft" >> "$wxf"
    echo "  created: $ts" >> "$wxf"
    echo "  platform: wechat" >> "$wxf"
    echo "---" >> "$wxf"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 公众号版草稿已保存: $(basename "$wxf")"
    echo ""
    echo "📋 待审核文件:"
    echo "  📄 $(basename "$wf")"
    echo "  📱 $(basename "$wxf")"
    echo ""
    echo "👉 审核: $0 review <文件名>"
    echo "👉 发布: $0 publish <文件名>"
}

cmd_list() {
    echo "📋 内容状态总览"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local draft_w=0 draft_wx=0 reviewed_w=0 reviewed_wx=0 published=0

    for f in "$WEBSITE_DIR"/*_DRAFT.* "$WECHAT_DIR"/*_DRAFT.*; do
        [ -f "$f" ] && draft_w=$((draft_w+1))
    done

    for f in "$PUBLISHED_DIR"/*.md; do
        [ -f "$f" ] && published=$((published+1))
    done

    echo "  📄 网站待审: $(ls "$WEBSITE_DIR"/*_DRAFT.* 2>/dev/null | wc -l | tr -d ' ')"
    echo "  📱 公众号待审: $(ls "$WECHAT_DIR"/*_DRAFT.* 2>/dev/null | wc -l | tr -d ' ')"
    echo "  ✅ 已发布: $published"
    echo ""

    if ls "$WEBSITE_DIR"/*_DRAFT.* >/dev/null 2>&1; then
        echo "📄 网站待审核列表:"
        for f in "$WEBSITE_DIR"/*_DRAFT.*; do
            echo "  📄 $(basename "$f") ($(wc -c < "$f" | tr -d ' ') bytes)"
        done
    fi
    if ls "$WECHAT_DIR"/*_DRAFT.* >/dev/null 2>&1; then
        echo "📱 公众号待审核列表:"
        for f in "$WECHAT_DIR"/*_DRAFT.*; do
            echo "  📱 $(basename "$f") ($(wc -c < "$f" | tr -d ' ') bytes)"
        done
    fi
}

cmd_review() {
    local fname="$1"
    if [ -z "$fname" ]; then
        echo "❌ 用法: $0 review <文件名>"
        exit 1
    fi

    local found=0
    for dir in "$WEBSITE_DIR" "$WECHAT_DIR"; do
        local fpath="$dir/$fname"
        if [ -f "$fpath" ]; then
            # Remove _DRAFT suffix
            local newname="$(echo "$fname" | sed 's/_DRAFT//')"
            local newpath="$dir/$newname"
            mv "$fpath" "$newpath"
            echo "✅ 已审核: $(basename "$fname") → $(basename "$newname")"
            echo "   👉 接下来可以发布: $0 publish $(basename "$newname")"
            found=1
        fi
    done

    if [ "$found" -eq 0 ]; then
        echo "❌ 文件不存在: $fname"
        echo "   目录: $WEBSITE_DIR"
        echo "         $WECHAT_DIR"
        exit 1
    fi
}

cmd_publish() {
    local fname="$1"
    if [ -z "$fname" ]; then
        echo "❌ 用法: $0 publish <文件名>"
        exit 1
    fi

    local found=0
    for dir in "$WEBSITE_DIR" "$WECHAT_DIR"; do
        local fpath="$dir/$fname"
        if [ -f "$fpath" ] && ! echo "$fname" | grep -q "_DRAFT"; then
            cp "$fpath" "$PUBLISHED_DIR/"
            local platform="website"
            echo "$fname" | grep -q "wechat\|公众号\|wx\|WX" && platform="wechat"
            echo "✅ 已发布 [$platform]: $fname"
            echo "   📦 已归档到: $PUBLISHED_DIR/"
            found=1
        fi
    done

    if [ "$found" -eq 0 ]; then
        echo "❌ 文件未找到或尚未审核: $fname"
        echo "   请先审核: $0 review <文件名>"
        exit 1
    fi
}

cmd_status() {
    echo "📊 机械师大百科 · 内容管线状态"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  草稿:    $(find "$WEBSITE_DIR" "$WECHAT_DIR" -name '*_DRAFT*' 2>/dev/null | wc -l | tr -d ' ') 篇"
    echo "  已审:    $(find "$WEBSITE_DIR" "$WECHAT_DIR" -name '*.md' ! -name '*_DRAFT*' 2>/dev/null | wc -l | tr -d ' ') 篇"
    echo "  已发布:  $(find "$PUBLISHED_DIR" -name '*.md' 2>/dev/null | wc -l | tr -d ' ') 篇"
    echo ""

    # Also show kanban status
    echo "🔄 看板状态:"
    python3 ~/.claude/skills/claude-kanban/scripts/kanban-persist.py list --session jixiebaike 2>/dev/null | head -5
}

case "${1:-help}" in
    generate|gen)
        shift
        cmd_generate "$@"
        ;;
    list|ls)
        cmd_list
        ;;
    review|check)
        shift
        cmd_review "$@"
        ;;
    publish|deploy)
        shift
        cmd_publish "$@"
        ;;
    status|st)
        cmd_status
        ;;
    help|--help|-h)
        echo "机械师大百科 · 内容工作流"
        echo "用法:"
        echo "  generate \"标题\"   生成新内容草稿"
        echo "  list              列出待审核内容"
        echo "  review <文件>      标记为已审核"
        echo "  publish <文件>     发布已审核内容"
        echo "  status            查看内容管线状态"
        ;;
    *)
        echo "未知命令: $1"
        echo "使用: $0 help"
        exit 1
        ;;
esac
