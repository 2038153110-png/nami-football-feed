# 纳米体彩采集项目（脱敏）

这是**采集程序 + 部署脚本**，不是比赛数据仓库。

密钥不要发进聊天、不要写进仓库。放到服务器 `/etc/nami-collector.env`。

## 仓库里有什么

| 路径 | 作用 |
|---|---|
| [collector/collect.py](collector/collect.py) | 采集北单/竞彩（让球、总进球、比分 SP） |
| [collector/.env.example](collector/.env.example) | 环境变量模板 |
| [deploy/install.sh](deploy/install.sh) | 装到 `/opt/nami-collector`，systemd 每 15 分钟跑 |
| [judgment/SCHEMA.md](judgment/SCHEMA.md) | 可核验判断记录，核心输入不用水位 |
| `*.json` 根目录 | 旧快照，可忽略 |

没有 `/opt/nami` 这个路径。正确安装位置是 **`/opt/nami-collector`**。

## 在原服务器上安装

```bash
git clone https://github.com/2038153110-png/nami-football-feed.git
cd nami-football-feed
sudo sh deploy/install.sh
sudo editor /etc/nami-collector.env   # 只在服务器上填 NAMI_USER / NAMI_SECRET
sudo systemctl start nami-collector.service
```

纳米控制台把**这台服务器出口 IP**加进白名单。采集进程不把密钥打到日志。

## 关纳米仍能跑通一次（验收）

```bash
python3 collector/collect.py --skip-nami --out /tmp/nami-out
# 退出码 0，写出 fallback.json（FotMob 赛程比分，无体彩 SP）
```

有纳米时：

```bash
# 环境变量已在 shell 或 EnvironmentFile 里，不要贴到聊天
python3 collector/collect.py --out ./out
# out/beidan.json  当前北单 + 已开奖（让球/总进球/比分）
# out/jingcai.json 当前竞彩 + 已开奖
# out/status.json
```

## 给判断服务用的输出

- 北单当前：`out/beidan-open.json`
- 北单已开奖：`out/beidan-settled.json`
- 判断记录格式：`judgment/record.example.json`

判断规则（采集不管，由判断服务写记录）：

1. 核对对手强弱、主客、机会质量、打法、人员；**核心输入不使用水位**
2. 实力模型 vs 进球模型，保留分歧，不靠「多数同意」加信心
3. 赛前锁概率和理由，赛后逐项评分：方向 / 进球数 / 净胜球

暂停的扫盘任务不会被本仓库的 timer 擅自恢复。

## 最新北单快照（给 GPT 读）

当前 142 + 已开奖 352（含让球/总进球/比分 SP）：
https://raw.githubusercontent.com/2038153110-png/nami-football-feed/main/bd-1734.json
