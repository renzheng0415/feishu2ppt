# Feishu2PPT 演示文件

这个目录提供不需要登录飞书的本地演示素材：

- \`sample-feishu.xml\`：最小飞书结构样例，包含标题、章节、正文和一组数据。
- \`sample-manifest.json\`：媒体与结构映射样例。
- \`showcase-plan.json\`：已经审查过的深圳项目月度营销复盘页面计划。
- \`showcase.pptx\`：可直接打开查看的可编辑示例。

## 本地跑通示例

在 Skill 根目录执行：

\`\`\`bash
WORKDIR="/tmp/feishu2ppt-demo-files"
python3 scripts/run.py plan \\
  --source-xml examples/sample-feishu.xml \\
  --workdir "$WORKDIR"
python3 scripts/run.py render \\
  --plan "$WORKDIR/deck.json" \\
  --output /tmp/feishu2ppt-demo.pptx \\
  --approve-plan
\`\`\`

如果本机已安装 OfficeCLI，再执行：

\`\`\`bash
officecli validate /tmp/feishu2ppt-demo.pptx
officecli view /tmp/feishu2ppt-demo.pptx issues --json
officecli view /tmp/feishu2ppt-demo.pptx screenshot --page 1-6 --grid 4 --out /tmp/feishu2ppt-demo-grid.png
\`\`\`

这个示例只验证本地 XML 到可编辑 PPTX 的链路，不代表飞书在线授权已经配置，也不代表真实项目数据已经接入。

