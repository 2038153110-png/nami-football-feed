# 纳米足球公开数据

给 ChatGPT 直接 GET。无密钥、无登录。

- 竞彩足球 **75** 场
- 北单 **258** 场
- 每场都有独立字段：`编号` `比赛` `开赛时间` `让球` `胜平负SP` `让球SP` `状态`
- `开赛时间` 是东八区字符串，例如 `2026-09-18 18:30`
- `胜平负SP` / `让球SP` 为 `{"胜":1.77,"平":5.25,"负":2.68}`；该玩法未开售时为 `null`

## 发给 GPT 的链接

完整（直播 + 竞彩 75 + 北单 258）

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/feed.json

只要竞彩 75 场

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/jingcai.json

只要北单 258 场

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/beidan.json

## 示例

竞彩 5001（胜平负和让球都开售）

```json
{
  "编号": "5001",
  "比赛": "沙特亚 vs 卡塔尔亚",
  "开赛时间": "2026-09-18 18:30",
  "让球": -1,
  "胜平负SP": { "胜": 1.42, "平": 3.95, "负": 5.8 },
  "让球SP": { "胜": 2.37, "平": 3.4, "负": 2.42 },
  "状态": "在售"
}
```

竞彩 5008 拜仁（胜平负未开售，让球 -3 有三项 SP）

```json
{
  "编号": "5008",
  "比赛": "拜仁 vs 柏林联合",
  "开赛时间": "2026-09-19 02:30",
  "让球": -3,
  "胜平负SP": null,
  "让球SP": { "胜": 1.77, "平": 5.25, "负": 2.68 },
  "状态": "在售"
}
```

## 给 GPT 的话

打开这个链接，读取全部「竞彩足球」和「北单」数组，不要只看前几条。每场用「编号」「比赛」「开赛时间」「让球」「胜平负SP」「让球SP」「状态」。SP 为 null 表示该玩法未开售。
https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/feed.json
