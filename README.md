# 纳米足球公开数据

给 ChatGPT 直接 GET。无密钥、无登录。

- 直播 **81** 场
- 竞彩足球 **74** 场
- 北单 **398** 场
- 每场都有独立字段：`编号` `比赛` `开赛时间` `让球` `胜平负SP` `让球SP` `状态`
- `开赛时间` 是东八区字符串，例如 `2026-09-19 02:30`
- `胜平负SP` / `让球SP` 为 `{"胜":1.58,"平":5.4,"负":3.21}`；该玩法未开售时为 `null`

## 发给 GPT 的链接

完整（直播 + 竞彩 74 + 北单 398）

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/now.json

只要竞彩 74 场

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/jingcai.json

只要北单 398 场

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/beidan.json

纯文本

https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/feed.txt
