#!/usr/bin/env python3
"""OP.GG MCP経由で全チャンピオンのMIDデータを収集してchampions.jsonに保存"""

import requests
import json
import time
import os
import re

MCP_URL = "https://mcp-api.op.gg/mcp"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "champions.json")
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), ".fetch_progress.json")

def mcp_call(method, params=None, id=1):
    payload = {"jsonrpc": "2.0", "id": id, "method": method}
    if params:
        payload["params"] = params
    for attempt in range(3):
        try:
            resp = requests.post(MCP_URL, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  リトライ {attempt+1}/3: {e}")
            time.sleep(2 ** attempt)
    return None

def tool_call(tool_name, arguments):
    return mcp_call("tools/call", {"name": tool_name, "arguments": arguments})

def get_text(result):
    """MCPレスポンスからテキスト取得"""
    if not result or "result" not in result:
        return None
    content = result["result"].get("content", [])
    if not content:
        return None
    return content[0].get("text", "")

def parse_list(s):
    """[a,b,c] or ["a","b"] 形式のリストをパース"""
    s = s.strip()
    if not s.startswith("[") or not s.endswith("]"):
        return []
    inner = s[1:-1].strip()
    if not inner:
        return []
    items = []
    depth = 0
    cur = ""
    in_str = False
    for ch in inner:
        if ch == '"' and not in_str:
            in_str = True
            cur += ch
        elif ch == '"' and in_str:
            in_str = False
            cur += ch
        elif ch == '[' and not in_str:
            depth += 1
            cur += ch
        elif ch == ']' and not in_str:
            depth -= 1
            cur += ch
        elif ch == ',' and depth == 0 and not in_str:
            items.append(cur.strip().strip('"'))
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur.strip().strip('"'))
    return items

def parse_analysis_text(text):
    """カスタムフォーマットのレスポンスを解析"""
    result = {}

    # AverageStats(win_rate,pick_rate,ban_rate,tier)
    m = re.search(r'AverageStats\(([\d.]+),([\d.]+),([\d.]+),(\d+)\)', text)
    if m:
        result["win_rate"] = float(m.group(1))
        result["pick_rate"] = float(m.group(2))
        result["ban_rate"] = float(m.group(3))
        result["tier"] = int(m.group(4))

    # CoreItems([ids],[names],pick_rate,win)
    m = re.search(r'CoreItems\((\[[^\]]*\]),(\[[^\]]*\]),([\d.]+),(\d+)\)', text)
    if m:
        ids = parse_list(m.group(1))
        names = parse_list(m.group(2))
        result["core_item_ids"] = [int(x) for x in ids if x.isdigit()]
        result["core_item_names"] = names
        result["core_item_pick_rate"] = float(m.group(3))

    # Boots([ids],[names],pick_rate,win) - 存在する場合
    m = re.search(r'Boots\((\[[^\]]*\]),(\[[^\]]*\]),([\d.]+),(\d+)\)', text)
    if m:
        ids = parse_list(m.group(1))
        names = parse_list(m.group(2))
        result["boots_ids"] = [int(x) for x in ids if x.isdigit()]
        result["boots_names"] = names

    # Runes(primary_page,[primary_runes],secondary_page,[secondary_runes],[stat_mods],pick_rate,win)
    m = re.search(
        r'Runes\("([^"]+)",(\[[^\]]*\]),"([^"]+)",(\[[^\]]*\]),(\[[^\]]*\]),([\d.]+),(\d+)\)',
        text
    )
    if m:
        result["rune_primary_page"] = m.group(1)
        result["rune_primary_runes"] = parse_list(m.group(2))
        result["rune_secondary_page"] = m.group(3)
        result["rune_secondary_runes"] = parse_list(m.group(4))
        result["rune_stat_mods"] = parse_list(m.group(5))
        result["rune_pick_rate"] = float(m.group(6))

    # Skills([order],pick_rate,win)
    m = re.search(r'Skills\((\[[^\]]*\]),([\d.]+),(\d+)\)', text)
    if m:
        result["skill_order"] = parse_list(m.group(1))
        result["skill_pick_rate"] = float(m.group(2))

    # SkillMasteries([ids],pick_rate,win)
    m = re.search(r'SkillMasteries\((\[[^\]]*\]),([\d.]+),(\d+)\)', text)
    if m:
        result["skill_max_order"] = parse_list(m.group(1))

    # StrongCounter("name",win_rate,play) - 上位5体
    counters = []
    for m in re.finditer(r'StrongCounter\("([^"]+)",([\d.]+),(\d+)\)', text):
        counters.append({
            "name": m.group(1),
            "win_rate_vs": float(m.group(2)),
            "games": int(m.group(3))
        })
    # 試合数でソートして上位5体
    counters.sort(key=lambda x: x["games"], reverse=True)
    result["counters"] = counters[:5]

    return result

def get_all_champions():
    """全チャンピオン一覧を取得"""
    result = tool_call("lol_list_champions", {
        "desired_output_fields": ["data.champions[].{champion_id,key,name}"]
    })
    text = get_text(result)
    if not text:
        return []
    pattern = r'Champion\((\d+),"([^"]+)","([^"]+)"\)'
    champions = []
    for m in re.finditer(pattern, text):
        champions.append({"id": int(m.group(1)), "key": m.group(2), "name": m.group(3)})
    return champions

def get_champion_mid_data(key):
    """チャンピオンのMIDデータを取得・パース"""
    result = tool_call("lol_get_champion_analysis", {
        "game_mode": "ranked",
        "champion": key,
        "position": "mid",
        "desired_output_fields": [
            "data.summary.average_stats.{win_rate,pick_rate,ban_rate,tier}",
            "data.core_items.{ids[],ids_names[],pick_rate,win}",
            "data.boots.{ids[],ids_names[],pick_rate,win}",
            "data.runes.{primary_page_name,primary_rune_names[],secondary_page_name,secondary_rune_names[],stat_mod_names[],pick_rate,win}",
            "data.skills.{order[],pick_rate,win}",
            "data.skill_masteries.{ids[],pick_rate,win}",
            "data.strong_counters[].{champion_name,win_rate,play}"
        ]
    })
    text = get_text(result)
    if not text:
        return None
    return parse_analysis_text(text)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"results": {}}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False)

def build_champion_entry(champ, data):
    """最終JSONフォーマットに整形"""
    return {
        "name": champ["name"],
        "key": champ["key"],
        "id": champ["id"],
        "stats": {
            "win_rate": data.get("win_rate"),
            "pick_rate": data.get("pick_rate"),
            "ban_rate": data.get("ban_rate"),
            "tier": data.get("tier")
        },
        "counters": data.get("counters", []),
        "build": {
            "core_items": {
                "names": data.get("core_item_names", []),
                "ids": data.get("core_item_ids", []),
                "pick_rate": data.get("core_item_pick_rate")
            },
            "boots": {
                "names": data.get("boots_names", []),
                "ids": data.get("boots_ids", [])
            },
            "runes": {
                "primary_page": data.get("rune_primary_page"),
                "primary_runes": data.get("rune_primary_runes", []),
                "secondary_page": data.get("rune_secondary_page"),
                "secondary_runes": data.get("rune_secondary_runes", []),
                "stat_mods": data.get("rune_stat_mods", []),
                "pick_rate": data.get("rune_pick_rate")
            },
            "skills": {
                "level_order": data.get("skill_order", []),
                "max_order": data.get("skill_max_order", []),
                "pick_rate": data.get("skill_pick_rate")
            }
        }
    }

def main():
    print("=== OP.GG MCP チャンピオンデータ収集 (MIDレーン/ランク) ===")
    print("全チャンピオン一覧を取得中...")

    champions = get_all_champions()
    if not champions:
        print("チャンピオン一覧の取得に失敗しました")
        return

    print(f"チャンピオン数: {len(champions)}")

    progress = load_progress()
    results = progress.get("results", {})

    total = len(champions)
    success_count = sum(1 for v in results.values() if not v.get("error"))

    for i, champ in enumerate(champions):
        key = champ["key"]

        if key in results and not results[key].get("error"):
            print(f"[{i+1}/{total}] {champ['name']} - スキップ")
            continue

        print(f"[{i+1}/{total}] {champ['name']} ({key}) ...", end=" ", flush=True)

        data = get_champion_mid_data(key)

        if data and data.get("win_rate") is not None:
            results[key] = build_champion_entry(champ, data)
            success_count += 1
            wr = data.get("win_rate", 0)
            pr = data.get("pick_rate", 0)
            print(f"✓ 勝率:{wr:.1%} ピック:{pr:.1%} カウンター:{len(data.get('counters',[]))}体")
        else:
            results[key] = {"name": champ["name"], "key": key, "id": champ["id"], "error": "MIDデータなし"}
            print("✗ データなし（MIDレーン未対応?）")

        progress["results"] = results
        save_progress(progress)
        time.sleep(0.4)

    # 最終JSON保存
    output = {
        "version": "1.0",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "OP.GG MCP API",
        "position": "mid",
        "game_mode": "ranked",
        "total_champions": total,
        "successful": success_count,
        "champions": results
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了 ===")
    print(f"成功: {success_count}/{total} チャンピオン")
    print(f"保存: {OUTPUT_FILE}")

    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    main()
