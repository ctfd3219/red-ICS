#!/usr/bin/env python3
"""Build mandatory IPSearch-MCP call plans.

This script does not query ip.db and does not replace MCP calls. It only validates
IPv4 input or generates keyword_lookup query strings for an AI/MCP runner.
"""

import argparse
import ipaddress
import json
import re
from pathlib import Path

REGIONS = {
    "北京": ("beijing", "bj"), "上海": ("shanghai", "sh"), "天津": ("tianjin", "tj"), "重庆": ("chongqing", "cq"),
    "浙江": ("zhejiang", "zj"), "杭州": ("hangzhou", "hz"), "西湖": ("xihu", "xh"), "宁波": ("ningbo", "nb"),
    "江苏": ("jiangsu", "js"), "南京": ("nanjing", "nj"), "苏州": ("suzhou", "sz"),
    "广东": ("guangdong", "gd"), "广州": ("guangzhou", "gz"), "深圳": ("shenzhen", "sz"),
    "山东": ("shandong", "sd"), "济南": ("jinan", "jn"), "青岛": ("qingdao", "qd"),
    "吉林": ("jilin", "jl"), "辽宁": ("liaoning", "ln"), "河北": ("hebei", "hb"), "河南": ("henan", "hn"),
    "湖北": ("hubei", "hb"), "湖南": ("hunan", "hn"), "四川": ("sichuan", "sc"), "福建": ("fujian", "fj"),
    "安徽": ("anhui", "ah"), "江西": ("jiangxi", "jx"), "陕西": ("shaanxi", "sn"), "山西": ("shanxi", "sx"),
    "云南": ("yunnan", "yn"), "贵州": ("guizhou", "gz"), "甘肃": ("gansu", "gs"), "海南": ("hainan", "hi"),
    "新疆": ("xinjiang", "xj"), "广西": ("guangxi", "gx"), "内蒙古": ("neimenggu", "nmg"), "宁夏": ("ningxia", "nx"),
    "西藏": ("xizang", "xz"), "香港": ("hongkong", "hk"), "澳门": ("macau", "mo"), "台湾": ("taiwan", "tw"),
}

TERMS = {
    "人民": ("renmin", "rm", "people"), "政府": ("zhengfu", "zf", "gov"), "医院": ("yiyuan", "yy", "hospital"),
    "大学": ("daxue", "dx", "university"), "学院": ("xueyuan", "xy", "college"), "学校": ("xuexiao", "xx", "school"),
    "公安": ("gongan", "ga", "police"), "法院": ("fayuan", "fy", "court"), "税务": ("shuiwu", "sw", "tax"),
    "教育": ("jiaoyu", "jy", "education"), "卫生": ("weisheng", "ws", "health"), "政务": ("zhengwu", "zw", "government"),
    "数据": ("shuju", "sj", "data"), "大数据": ("dashuju", "dsj", "bigdata"), "信息": ("xinxi", "xx", "info"),
    "科技": ("keji", "kj", "technology"), "网络": ("wangluo", "wl", "network"), "软件": ("ruanjian", "rj", "software"),
    "混论": ("kunlun", "kl", "kunlun"), "昆仑": ("kunlun", "kl", "kunlun"), "机械": ("jixie", "jx", "machinery"), "股份": ("gufen", "gf", "stock"), "有限": ("youxian", "yx", "ltd"),
    "公司": ("gongsi", "gs", "company"), "集团": ("jituan", "jt", "group"), "酒": ("jiu", "j", "wine"),
    "第一": ("diyi", "dy", "first"), "第二": ("dier", "de", "second"), "第三": ("disan", "ds", "third"),
    "中心": ("zhongxin", "zx", "center"), "管理": ("guanli", "gl", "management"), "服务": ("fuwu", "fw", "service"),
    "委员会": ("weiyuanhui", "wyh", "committee"), "管理局": ("guanliju", "glj", "bureau"), "人民政府": ("renminzhengfu", "rmzf", "people gov"),
}

CHAR_PINYIN = {
    "浙": ("zhe", "z"), "江": ("jiang", "j"), "第": ("di", "d"), "一": ("yi", "y"), "二": ("er", "e"), "三": ("san", "s"),
    "人": ("ren", "r"), "民": ("min", "m"), "医": ("yi", "y"), "院": ("yuan", "y"), "杭": ("hang", "h"), "州": ("zhou", "z"),
    "西": ("xi", "x"), "湖": ("hu", "h"), "区": ("qu", "q"), "政": ("zheng", "z"), "府": ("fu", "f"),
    "吉": ("ji", "j"), "林": ("lin", "l"), "混": ("kun", "k"), "论": ("lun", "l"), "昆": ("kun", "k"), "仑": ("lun", "l"),
    "机": ("ji", "j"), "械": ("xie", "x"), "股": ("gu", "g"), "份": ("fen", "f"), "有": ("you", "y"), "限": ("xian", "x"),
    "公": ("gong", "g"), "司": ("si", "s"), "酒": ("jiu", "j"), "科": ("ke", "k"), "技": ("ji", "j"),
    "网": ("wang", "w"), "络": ("luo", "l"), "软": ("ruan", "r"), "件": ("jian", "j"), "数": ("shu", "s"), "据": ("ju", "j"),
    "信": ("xin", "x"), "息": ("xi", "x"), "中": ("zhong", "z"), "心": ("xin", "x"), "大": ("da", "d"), "学": ("xue", "x"),
}

STOP_WORDS = ["股份有限公司", "有限责任公司", "有限公司", "集团", "公司", "市", "省", "区", "县"]

TYPE_PRIORITY = [
    "人民政府", "政府", "医院", "大学", "学院", "学校", "公安", "法院", "税务",
    "委员会", "管理局", "中心", "集团", "公司",
]

BROAD_SINGLE_KEYWORDS = {
    "beijing", "shanghai", "tianjin", "chongqing", "zhejiang", "jiangsu", "guangdong",
    "hospital", "gov", "government", "company", "ltd", "group", "school", "university",
}


def validate_ipv4(value: str) -> str:
    try:
        ip = ipaddress.IPv4Address(value.strip())
    except ValueError as exc:
        raise SystemExit(f"invalid IPv4: {value}; 请重新输入合法 IPv4 地址") from exc
    return str(ip)


def detect_regions(name: str):
    matches = []
    for cn, (en, initial) in sorted(REGIONS.items(), key=lambda item: len(item[0]), reverse=True):
        if cn in name:
            matches.append({"cn": cn, "en": en, "initial": initial})
    return matches


def detect_terms(name: str):
    matches = []
    for cn, (pinyin, initial, english) in sorted(TERMS.items(), key=lambda item: len(item[0]), reverse=True):
        if cn in name:
            matches.append({"cn": cn, "pinyin": pinyin, "initial": initial, "english": english})
    return matches


def initials(name: str) -> str:
    result = []
    i = 0
    while i < len(name):
        matched = False
        for cn, (_, initial, _) in sorted(TERMS.items(), key=lambda item: len(item[0]), reverse=True):
            if name.startswith(cn, i):
                result.append(initial.replace(" ", ""))
                i += len(cn)
                matched = True
                break
        if matched:
            continue
        ch = name[i]
        if ch in CHAR_PINYIN:
            result.append(CHAR_PINYIN[ch][1])
        elif ch.isascii() and ch.isalnum():
            result.append(ch.lower())
        i += 1
    return re.sub(r"[^a-z0-9]", "", "".join(result))


def compact_main_name(name: str) -> str:
    value = name
    for word in STOP_WORDS:
        value = value.replace(word, "")
    for region in REGIONS:
        value = value.replace(region, "")
    return value or name


def scan_tokens(text: str, field: str):
    tokens = []
    i = 0
    term_items = sorted(TERMS.items(), key=lambda item: len(item[0]), reverse=True)
    while i < len(text):
        matched = False
        for cn, (pinyin, _, english) in term_items:
            if text.startswith(cn, i):
                tokens.append(pinyin if field == "pinyin" else english)
                i += len(cn)
                matched = True
                break
        if matched:
            continue
        ch = text[i]
        if field == "pinyin" and ch in CHAR_PINYIN:
            tokens.append(CHAR_PINYIN[ch][0])
        elif ch.isascii() and ch.isalnum():
            tokens.append(ch.lower())
        i += 1
    return dedupe(tokens)


def pinyin_tokens(text: str):
    return scan_tokens(text, "pinyin")


def english_tokens(text: str):
    return scan_tokens(text, "english")


def primary_type_term(terms):
    for wanted in TYPE_PRIORITY:
        for item in terms:
            if item["cn"] == wanted:
                return item
    return terms[0] if terms else None


def dedupe(values):
    seen = set()
    result = []
    for value in values:
        for part in re.split(r"[,\s]+", str(value).strip().lower()):
            cleaned = re.sub(r"[^a-z0-9-]", "", part)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
    return result


def safe_keyword(tokens):
    tokens = dedupe(tokens)
    # Avoid broad region-only or institution-only keywords, but allow specific initials.
    if len(tokens) == 1:
        only = tokens[0]
        if len(only) >= 5 and only not in BROAD_SINGLE_KEYWORDS:
            return only
        return None
    return ",".join(tokens)


def build_keyword_plan(unit_name: str):
    name = unit_name.strip()
    regions = detect_regions(name)
    terms = detect_terms(name)
    region = regions[0] if regions else None
    main = compact_main_name(name)
    name_initials = initials(name)
    region_en = region["en"] if region else None
    region_tokens = [item["en"] for item in regions]
    primary_term = primary_type_term(terms)

    name_english_tokens = english_tokens(name)
    main_pinyin_tokens = pinyin_tokens(main)
    main_english_tokens = english_tokens(main)
    if "ltd" in name_english_tokens and main_english_tokens:
        main_english_tokens = main_english_tokens[:1] + ["ltd"]

    calls = []

    def add(rule, tokens):
        keyword = safe_keyword(tokens)
        if keyword:
            calls.append({"rule": rule, "tool": "keyword_lookup", "keyword": keyword})

    if name_initials:
        add("1. 单位中文名称拼音首字母", [name_initials])

    add("2. 单位英文分词组合", [region_en] + english_tokens(name))
    add("3. 单位中文拼音分词组合", [region_en] + main_pinyin_tokens)
    add("4. 地区英文 + 公司/机构主要拼音", [region_en] + (main_pinyin_tokens[:1] if primary_term and primary_term["cn"] == "公司" else main_pinyin_tokens[:2]))
    add("5. 地区英文 + 公司/机构主要英文", [region_en] + main_english_tokens[:2])

    if region_en and name_initials and terms:
        add("6. 组合补充：地区 + 类型 + 首字母", [region_en, primary_term["english"] if primary_term else None, name_initials])

    if len(region_tokens) >= 2:
        add("7. 多级地区 + 类型英文", region_tokens + english_tokens(name)[-2:])
        add("8. 多级地区 + 类型拼音", region_tokens + pinyin_tokens(name)[-2:])

    if regions and terms:
        for region_item in regions:
            add(f"9. 单地区补充：{region_item['cn']} + 主要类型", [region_item["en"], primary_term["english"] if primary_term else None])

    return {
        "input_type": "unit_name",
        "unit_name": name,
        "detected_regions": regions,
        "detected_terms": terms,
        "mcp_policy": "必须依次通过 AI MCP 调用 keyword_lookup；即使前一次已有结果也要执行全部关键词；禁止 Python 直接读取 ip.db。",
        "calls": calls,
        "result_requirements": [
            "将返回 IP 段统一转换为 CIDR 格式",
            "保留 IP 段描述/名称原文",
            "给出中文翻译或归属解释",
            "说明每个 CIDR 归属该单位的原因",
            "无法确认归属时标记 suspected，不得标记 confirmed",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build IPSearch-MCP call plan")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ipv4", help="IPv4 address for ip_lookup")
    group.add_argument("--unit-name", help="Company, institution, or government unit name for keyword_lookup")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    if args.ipv4:
        ip = validate_ipv4(args.ipv4)
        result = {
            "input_type": "ipv4",
            "ip": ip,
            "mcp_policy": "调用前已完成 IPv4 基础校验；必须通过 AI MCP 调用 ip_lookup，不得 Python 直接读取 ip.db。",
            "calls": [{"rule": "IPv4 Whois 查询", "tool": "ip_lookup", "ip": ip}],
            "result_requirements": ["返回 IP 段、名称、描述、国家、状态、最后修改等字段"],
        }
    else:
        result = build_keyword_plan(args.unit_name)

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




