# 判断记录（可核验）

服务器价值在于留下判断记录，不在于堆 JSON。采集程序只提供赛程/SP 输入；水位不得作为核心输入。

每场一场文件：`judgment/records/{编号}-{开赛日期}.json`

## 必填

| 字段 | 含义 |
|---|---|
| id | 北单/竞彩编号 |
| match | 主 vs 客 |
| kickoff | 开赛时间 Asia/Shanghai |
| locked_at | 赛前锁盘时刻 |
| strength | 实力模型：方向、净胜球、理由（对手强弱、主客、机会质量、打法、人员） |
| goals | 进球模型：总进球区间、理由 |
| disagreement | 两模型分歧，禁止用「多数同意」加信心 |
| uses_odds | 必须为 false。SP 只可放在 `odds_ref` 对照 |
| result | 赛后：比分、总进球、方向对错、进球数对错、净胜球对错、逐项评分 |

## 验收

1. 采集：`python3 collector/collect.py --out ./out` 写出 `beidan.json` / `jingcai.json`
2. 关纳米仍能跑通：`python3 collector/collect.py --skip-nami --out ./out` 写出 `fallback.json`，退出码 0
3. 判断：赛前写入 `strength`/`goals`/`disagreement`，赛后只追加 `result`，不改锁盘字段
