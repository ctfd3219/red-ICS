#!/usr/bin/env python3
"""Initialize red-ics output artifacts without overwriting existing findings."""

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

TEXT_FILES = {
    "domains_seed.txt": "# seed domains\n",
    "domains_all.txt": "# domain\n",
    "subdomains_passive.txt": "# subdomain\n",
    "subdomains_active.txt": "# subdomain\n",
    "subdomains_all.txt": "# subdomain\n",
    "ips_passive.txt": "# ip\n",
    "ips_active.txt": "# ip\n",
    "ips_all.txt": "# ip\n",
    "cidrs_all.txt": "# cidr\n",
    "urls_web.txt": "# url\n",
    "sensitive_files.txt": "# url\tsource\tevidence\n",
    "internal_hosts.txt": "# host_or_ip\tsource\tconfidence\n",
}

CSV_FILES = {
    "related_orgs.csv": "name,relationship,source,confidence,notes\n",
    "ports_open.csv": "ip,port,protocol,service,version,source,confidence\n",
    "host_collision.csv": "ip,host,status,title,evidence,confidence\n",
    "buckets_public.csv": "provider,bucket,url,permission,evidence,confidence\n",
    "vendors_partners.csv": "name,type,source,asset_clue,confidence,notes\n",
    "cloud_services.csv": "service,provider,asset,signal,source,confidence\n",
    "evidence_index.csv": "artifact,item,source,evidence,confidence,phase\n",
}

JSON_FILES = {
    "company_info.json": {},
    "credentials_found.json": [],
}

LOG_FILES = [
    "scope.log",
    "phase0_prepare.log",
    "phase1_org_recon.log",
    "phase2_passive_osint.log",
    "phase3_extended_assets.log",
    "phase4_active_recon.log",
    "phase5_report.log",
]

DEFAULT_CONFIG = {
    "default_output": "output",
    "execution_modes": ["authorized", "passive-first", "supplement", "unknown"],
    "default_mode": "unknown",
    "xlsx_template": {
        "filename": "assets_summary.xlsx",
        "sheet_name": "资产汇总",
        "columns": [
            "组织",
            "域名",
            "子域名",
            "IP",
            "CIDR",
            "Web",
            "端口",
            "供应商",
            "云服务",
            "APP",
            "小程序",
            "公众号",
            "泄露线索",
            "主动探测",
        ],
    },
}


def load_config(path: Path) -> dict:
    config = json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))
    if not path.exists():
        return config

    loaded = json.loads(path.read_text(encoding="utf-8"))
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


def write_if_missing(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def col_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def sheet_xml(columns) -> str:
    cells = []
    for idx, value in enumerate(columns, start=1):
        ref = f"{col_name(idx)}1"
        cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
    cols = "".join(
        f'<col min="{i}" max="{i}" width="18" customWidth="1"/>'
        for i in range(1, len(columns) + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{cols}</cols>
  <sheetData><row r="1">{''.join(cells)}</row></sheetData>
</worksheet>
"""


def create_xlsx_template(path: Path, force: bool, sheet_name: str, columns) -> bool:
    if path.exists() and not force:
        return False

    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>
""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
""",
        "xl/workbook.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="{escape(sheet_name)}" sheetId="1" r:id="rId1"/></sheets>
</workbook>
""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
""",
        "xl/styles.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>
""",
        "xl/worksheets/sheet1.xml": sheet_xml(columns),
    }

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize red-ics output structure")
    parser.add_argument("--config", default="config.json", help="Config file path")
    parser.add_argument("--output", default=None, help="Output directory, default from config")
    parser.add_argument("--target", default="", help="Target name/domain for scope.json")
    parser.add_argument("--mode", default=None, help="Execution mode")
    parser.add_argument("--force", action="store_true", help="Overwrite existing empty artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Print planned artifacts without writing files")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    modes = config.get("execution_modes", DEFAULT_CONFIG["execution_modes"])
    mode = args.mode or config.get("default_mode", "unknown")
    if mode not in modes:
        raise SystemExit(f"invalid mode: {mode}; expected one of {', '.join(modes)}")

    xlsx_config = config.get("xlsx_template", DEFAULT_CONFIG["xlsx_template"])
    xlsx_filename = xlsx_config.get("filename", "assets_summary.xlsx")
    xlsx_columns = xlsx_config.get("columns", DEFAULT_CONFIG["xlsx_template"]["columns"])
    sheet_name = xlsx_config.get("sheet_name", "资产汇总")

    out_dir = Path(args.output or config.get("default_output", "output"))
    logs_dir = out_dir / "logs"

    if args.dry_run:
        planned = list(TEXT_FILES) + list(CSV_FILES) + list(JSON_FILES) + ["scope.json", "Report.md", xlsx_filename]
        planned += [f"logs/{name}" for name in LOG_FILES]
        print(f"output: {out_dir}")
        print(f"mode: {mode}")
        print(f"planned_artifacts: {len(planned)}")
        for item in planned:
            print(item)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for name, content in TEXT_FILES.items():
        if write_if_missing(out_dir / name, content, args.force):
            created.append(name)

    for name, content in CSV_FILES.items():
        if write_if_missing(out_dir / name, content, args.force):
            created.append(name)

    for name, value in JSON_FILES.items():
        content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        if write_if_missing(out_dir / name, content, args.force):
            created.append(name)

    scope = {
        "target": args.target,
        "mode": mode,
        "authorized_scope": [],
        "assumptions": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if write_if_missing(out_dir / "scope.json", json.dumps(scope, ensure_ascii=False, indent=2) + "\n", args.force):
        created.append("scope.json")

    report_stub = "# 资产侦察报告\n\n> 状态：初始化完成，等待阶段数据填充。\n"
    if write_if_missing(out_dir / "Report.md", report_stub, args.force):
        created.append("Report.md")

    if create_xlsx_template(out_dir / xlsx_filename, args.force, sheet_name, xlsx_columns):
        created.append(xlsx_filename)

    for name in LOG_FILES:
        if write_if_missing(logs_dir / name, "", args.force):
            created.append(f"logs/{name}")

    print(f"initialized: {out_dir}")
    print(f"created_or_overwritten: {len(created)}")
    for item in created:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())