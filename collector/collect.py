#!/usr/bin/env python3
"""Nami lottery collector. Stdlib only. Credentials from env, never from this file.

Usage:
  NAMI_USER=... NAMI_SECRET=... python3 collect.py --out ./out

Exit 0 even on Nami failure if ALLOW_FOTMOB_FALLBACK=1 (scores only, SP empty).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

TZ = timezone(timedelta(hours=8))
NAMI_HOST = os.environ.get("NAMI_HOST", "https://open.sportnanoapi.com").rstrip("/")
FOTMOB = "https://www.fotmob.com/api/data"

JQ_KEYS = ["0", "1", "2", "3", "4", "5", "6", "7+"]
BF_JC = [
    "1:0", "2:0", "2:1", "3:0", "3:1", "3:2", "4:0", "4:1", "4:2", "5:0", "5:1", "5:2", "胜其他",
    "0:0", "1:1", "2:2", "3:3", "平其他",
    "0:1", "0:2", "1:2", "0:3", "1:3", "2:3", "0:4", "1:4", "2:4", "0:5", "1:5", "2:5", "负其他",
]
BF_BD = {
    "s10": "1:0", "s20": "2:0", "s21": "2:1", "s30": "3:0", "s31": "3:1", "s32": "3:2",
    "s40": "4:0", "s41": "4:1", "s42": "4:2", "sw": "胜其他",
    "s00": "0:0", "s11": "1:1", "s22": "2:2", "s33": "3:3", "sp": "平其他",
    "s01": "0:1", "s02": "0:2", "s12": "1:2", "s03": "0:3", "s13": "1:3", "s23": "2:3",
    "s04": "0:4", "s14": "1:4", "s24": "2:4", "sl": "负其他",
}
SELL = {"0": "未开售", "1": "在售", "2": "停售", "3": "开奖中", "4": "已开奖"}
SPF_MAP = {"3": "胜", "1": "平", "0": "负"}


def now_stamp() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


def clock(ts: Any) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), TZ).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return None


def num(v: Any) -> int | float | None:
    if v is None or v == "" or v == "—":
        return None
    try:
        n = float(str(v).lstrip("+"))
        return int(n) if n == int(n) else n
    except (TypeError, ValueError):
        return None


def csv(s: Any) -> list[str]:
    return [x.strip() for x in str(s or "").split(",")]


def overall(s: Any) -> str:
    p = str(s or "").split(",")
    if p and all(x == "4" for x in p):
        return "已开奖"
    if "1" in p:
        return "在售"
    if "3" in p:
        return "开奖中"
    if p and all(x == "0" for x in p):
        return "未开售"
    return "停售"


def sold(code: str) -> bool:
    return code in {"1", "2", "3", "4"}


def http_json(url: str, timeout: int = 25) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "nami-collector/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def nami_get(path: str, user: str, secret: str) -> dict[str, Any]:
    q = urllib.parse.urlencode({"user": user, "secret": secret})
    join = "&" if "?" in path else "?"
    return http_json(f"{NAMI_HOST}{path}{join}{q}")


def map_list(s: Any, keys: list[str]) -> dict[str, int | float] | None:
    parts = csv(s)
    if not any(num(x) is not None for x in parts):
        return None
    out: dict[str, int | float] = {}
    for i, k in enumerate(keys):
        v = num(parts[i]) if i < len(parts) else None
        if v is not None:
            out[k] = v
    return out or None


def trio_spf(spf: dict[str, Any] | None) -> dict[str, int | float | None] | None:
    if not isinstance(spf, dict):
        return None
    a, b, c = num(spf.get("sf3")), num(spf.get("sf1")), num(spf.get("sf0"))
    if a is None and b is None and c is None:
        return None
    return {"胜": a, "平": b, "负": c}


def trio_csv(parts: list[str], start: int = 0) -> dict[str, int | float | None] | None:
    a, b, c = num(parts[start] if len(parts) > start else None), num(parts[start + 1] if len(parts) > start + 1 else None), num(parts[start + 2] if len(parts) > start + 2 else None)
    if a is None and b is None and c is None:
        return None
    return {"胜": a, "平": b, "负": c}


def bd_jq(odds: dict[str, Any] | None) -> dict[str, int | float] | None:
    jq = (odds or {}).get("jq") or {}
    out: dict[str, int | float] = {}
    for i, k in enumerate(JQ_KEYS):
        v = num(jq.get(f"j{i}"))
        if v is not None:
            out[k] = v
    return out or None


def bd_bf(odds: dict[str, Any] | None) -> dict[str, int | float] | None:
    bf = (odds or {}).get("bf") or {}
    out: dict[str, int | float] = {}
    for k, label in BF_BD.items():
        v = num(bf.get(k))
        if v is not None:
            out[label] = v
    return out or None


def collect_beidan(user: str, secret: str) -> dict[str, Any]:
    odds = nami_get("/api/v2/sports/bd/odds", user, secret).get("data") or []
    result = nami_get("/api/v2/sports/bd/result", user, secret).get("data") or []
    rows = []
    for r in odds:
        sell = str(r.get("sell_status") or "").split(",")
        o = r.get("odds") or {}
        spf = o.get("spf") or {}
        rows.append(
            {
                "编号": str(r.get("issue_num") or ""),
                "期号": r.get("issue"),
                "比赛": f"{r.get('home')} vs {r.get('away')}",
                "联赛": r.get("comp"),
                "开赛时间": clock(r.get("match_time")),
                "让球": num(spf.get("goal")),
                "让球SP": trio_spf(spf) if sold((sell + ["0"] * 5)[0]) else None,
                "总进球SP": bd_jq(o) if sold((sell + ["0"] * 5)[1]) else None,
                "比分SP": bd_bf(o) if sold((sell + ["0"] * 5)[4]) else None,
                "状态": overall(r.get("sell_status")),
            }
        )
    rows.sort(key=lambda x: (x.get("开赛时间") or "", x.get("编号") or ""))
    settled = []
    for r in result:
        o = r.get("odds") or {}
        spf, jq, bf = o.get("spf") or {}, o.get("jq") or {}, o.get("bf") or {}
        settled.append(
            {
                "编号": str(r.get("issue_num") or ""),
                "期号": r.get("issue"),
                "比赛": f"{r.get('home')} vs {r.get('away')}",
                "联赛": r.get("comp"),
                "开赛时间": clock(r.get("match_time")),
                "比分": None if r.get("home_score") is None else f"{r.get('home_score')}-{r.get('away_score')}",
                "让球胜平负开奖": {"让球": spf.get("rb1"), "结果": spf.get("rb2"), "SP": num(spf.get("sp"))},
                "总进球开奖": {"结果": jq.get("rb1"), "SP": num(jq.get("sp"))},
                "比分开奖": {"结果": bf.get("rb1"), "SP": num(bf.get("sp"))},
                "状态": "已开奖",
            }
        )
    settled.sort(key=lambda x: (x.get("开赛时间") or "", x.get("编号") or ""))
    return {
        "说明": "纳米北单。当前含让球SP、总进球SP、比分SP；已开奖含比分和开奖SP。水位只作对照，不是判断核心输入。",
        "来源": "nami",
        "时区": "Asia/Shanghai",
        "更新时间": now_stamp(),
        "场次": {"北单": len(rows), "北单已开奖": len(settled), "状态": dict(Counter(x["状态"] for x in rows))},
        "北单": rows,
        "北单已开奖": settled,
    }


def collect_jingcai(user: str, secret: str) -> dict[str, Any]:
    payload = nami_get("/api/v2/sports/jc/odds", user, secret).get("data") or {}
    result = nami_get("/api/v2/sports/jc/result", user, secret).get("data") or {}
    jczq = payload.get("jczq") or [] if isinstance(payload, dict) else []
    rzq = result.get("jczq") or [] if isinstance(result, dict) else []
    open_rows = []
    for r in jczq:
        sell = str(r.get("sell_status") or "").split(",")
        spf, rq = csv(r.get("spf")), csv(r.get("rq"))
        open_rows.append(
            {
                "编号": str(r.get("issue_num") or ""),
                "期号": r.get("issue"),
                "比赛": f"{r.get('short_home') or r.get('home')} vs {r.get('short_away') or r.get('away')}",
                "联赛": r.get("comp") or r.get("short_comp"),
                "开赛时间": clock(r.get("match_time")),
                "让球": num(rq[0]) if rq else None,
                "胜平负SP": trio_csv(spf) if sold((sell + ["0"] * 5)[0]) else None,
                "让球SP": trio_csv(rq, 1) if sold((sell + ["0"] * 5)[1]) else None,
                "总进球SP": map_list(r.get("jq"), JQ_KEYS) if sold((sell + ["0"] * 5)[3]) else None,
                "比分SP": map_list(r.get("bf"), BF_JC) if sold((sell + ["0"] * 5)[2]) else None,
                "状态": overall(r.get("sell_status")),
            }
        )
    open_rows.sort(key=lambda x: (x.get("开赛时间") or "", x.get("编号") or ""))
    settled = []
    for r in rzq:
        bf, jq, spf, rq = csv(r.get("bf")), csv(r.get("jq")), csv(r.get("spf")), csv(r.get("rq"))
        settled.append(
            {
                "编号": str(r.get("issue_num") or ""),
                "期号": r.get("issue"),
                "比赛": f"{r.get('short_home') or r.get('home')} vs {r.get('short_away') or r.get('away')}",
                "联赛": r.get("comp") or r.get("short_comp"),
                "开赛时间": clock(r.get("match_time")),
                "比分": None if r.get("home_score") is None else f"{r.get('home_score')}-{r.get('away_score')}",
                "胜平负开奖": {"结果": SPF_MAP.get(spf[0], spf[0] or None), "SP": num(spf[1] if len(spf) > 1 else None)},
                "让球开奖": {"让球": num(rq[0] if rq else None), "结果": SPF_MAP.get(rq[1], rq[1] if len(rq) > 1 else None), "SP": num(rq[2] if len(rq) > 2 else None)},
                "总进球开奖": {"结果": jq[0] or None, "SP": num(jq[1] if len(jq) > 1 else None)},
                "比分开奖": {"结果": bf[0] or None, "SP": num(bf[1] if len(bf) > 1 else None)},
                "状态": "已开奖",
            }
        )
    settled.sort(key=lambda x: (x.get("开赛时间") or "", x.get("编号") or ""))
    return {
        "说明": "纳米竞彩足球。当前含胜平负/让球/总进球/比分 SP。水位只作对照。",
        "来源": "nami",
        "时区": "Asia/Shanghai",
        "更新时间": now_stamp(),
        "场次": {"竞彩足球": len(open_rows), "竞彩足球已开奖": len(settled), "状态": dict(Counter(x["状态"] for x in open_rows))},
        "竞彩足球": open_rows,
        "竞彩足球已开奖": settled,
    }


def fotmob_fallback() -> dict[str, Any]:
    data = http_json(f"{FOTMOB}/matches?date={datetime.now(TZ).strftime('%Y%m%d')}")
    leagues = data.get("leagues") or []
    rows = []
    for lg in leagues:
        for m in lg.get("matches") or []:
            st = m.get("status") or {}
            home, away = m.get("home") or {}, m.get("away") or {}
            phase = "完场" if st.get("finished") else ("直播" if st.get("started") or st.get("ongoing") else "未开")
            rows.append(
                {
                    "编号": str(m.get("id") or ""),
                    "比赛": f"{home.get('name') or home.get('longName')} vs {away.get('name') or away.get('longName')}",
                    "联赛": lg.get("name"),
                    "开赛时间": st.get("utcTime"),
                    "比分": None if home.get("score") is None else f"{home.get('score')}-{away.get('score')}",
                    "状态": phase,
                    "让球SP": None,
                    "总进球SP": None,
                    "比分SP": None,
                }
            )
    return {
        "说明": "Nami 不可用，已用 FotMob 赛程比分跑通。无体彩 SP。判断核心输入仍不使用水位。",
        "来源": "fotmob",
        "时区": "Asia/Shanghai",
        "更新时间": now_stamp(),
        "场次": {"赛程": len(rows)},
        "赛程": rows,
    }


def dump(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Collect Nami beidan/jingcai lottery SP")
    p.add_argument("--out", default=os.environ.get("OUT_DIR", "./out"))
    p.add_argument("--skip-nami", action="store_true")
    args = p.parse_args()
    out = Path(args.out)
    user = os.environ.get("NAMI_USER", "").strip()
    secret = os.environ.get("NAMI_SECRET", "").strip()
    allow_fb = os.environ.get("ALLOW_FOTMOB_FALLBACK", "1") not in {"0", "false", "no"}
    status: dict[str, Any] = {"更新时间": now_stamp(), "nami": None, "fallback": None}

    if args.skip_nami or not user or not secret:
        status["nami"] = {"ok": False, "message": "未配置 NAMI_USER/NAMI_SECRET，或指定 --skip-nami"}
        if not allow_fb:
            dump(out / "status.json", status)
            print(status["nami"]["message"], file=sys.stderr)
            return 2
        fb = fotmob_fallback()
        dump(out / "fallback.json", fb)
        status["fallback"] = {"ok": True, "matches": fb["场次"]}
        dump(out / "status.json", status)
        print("fotmob fallback", fb["场次"])
        return 0

    try:
        bd = collect_beidan(user, secret)
        jc = collect_jingcai(user, secret)
        dump(out / "beidan.json", bd)
        dump(out / "jingcai.json", jc)
        dump(out / "beidan-open.json", {"更新时间": bd["更新时间"], "场次" : bd["场次"]["北单"], "北单": bd["北单"]})
        dump(out / "beidan-settled.json", {"更新时间": bd["更新时间"], "场次": bd["场次"]["北单已开奖"], "北单已开奖": bd["北单已开奖"]})
        status["nami"] = {"ok": True, "beidan": bd["场次"], "jingcai": jc["场次"]}
        dump(out / "status.json", status)
        print("nami", status["nami"])
        return 0
    except Exception as err:
        status["nami"] = {"ok": False, "message": str(err)}
        if not allow_fb:
            dump(out / "status.json", status)
            print("nami failed", err, file=sys.stderr)
            return 1
        fb = fotmob_fallback()
        dump(out / "fallback.json", fb)
        status["fallback"] = {"ok": True, "matches": fb["场次"]}
        dump(out / "status.json", status)
        print("nami failed, fotmob fallback", err)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
