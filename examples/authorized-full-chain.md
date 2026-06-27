# 示例：完整授权全链路执行

用户输入示例：

```text
已经获得 XX 科技有限公司授权，范围为 example.com、*.example.com 和 192.0.2.0/24。请使用 red-ics 做完整全链路资产侦察，允许低速主动探测，输出到 output/xx-tech。
```

预期执行模式：`authorized`

执行要点：

- 阶段 0 初始化 `output/xx-tech`。
- 阶段 1 到阶段 3 先完成组织、被动 OSINT 和扩展资产。
- 阶段 4 只在授权域名、IP、CIDR 内做主动探测。
- 阶段 5 生成 `Report.md`、`assets_summary.xlsx` 和证据索引。