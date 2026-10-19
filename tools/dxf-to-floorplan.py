"""
把 AutoCAD DXF 平面圖轉成看板用的平面圖資料檔。

用法：
    pip install ezdxf
    python tools/dxf-to-floorplan.py <平面圖.dxf> <廠區代碼> > floorplans/<廠區代碼>.js
例：
    python tools/dxf-to-floorplan.py 2M2F.dxf 2F_2 > floorplans/2F_2.js

圖面需求：
- 每台機台旁要有含編號的文字（例如 "Brother / S500 X1 / M296"），會用 M+數字 辨識。
- 機台本體最好是圖塊（INSERT），程式會找「包住編號文字的最小圖塊」當作機台外框；
  找不到圖塊的機台，會參考最近的同型號機台估算，並在 stderr 列出。
- 其他文字（例如「IPQC 檢驗室」）會當作區域名稱顯示。
- 圖層分類：建築結構 → 牆；預定通道 → 通道；消防設施 → 消防；電控箱 → 電控；其他 → 設施細節。
"""
import json
import re
import sys
from collections import defaultdict

import ezdxf
from ezdxf import bbox, path

MACHINE_RE = re.compile(r"\b(M\d{2,3})\b")
FLATTEN = 2          # 曲線轉折線的精度（圖面單位）
MARGIN = 40


def layer_class(layer):
    if layer == "建築結構":
        return "wall"
    if layer == "預定通道":
        return "aisle"
    if layer == "消防設施":
        return "fire"
    if layer == "電控箱":
        return "ctrl"
    return "misc"


def text_of(e):
    return e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text


def main(dxf_path, floor_key):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    log = lambda *a: print(*a, file=sys.stderr)

    # ---- 機台編號文字
    labels = []
    for e in msp.query("MTEXT TEXT"):
        t = text_of(e)
        m = MACHINE_RE.search(t)
        if m:
            parts = [s.strip() for s in t.split("\n") if s.strip()]
            model = " ".join(p for p in parts if p != m.group(1) and p != "Brother")
            labels.append(dict(id=m.group(1), x=e.dxf.insert.x, y=e.dxf.insert.y, model=model, layer=e.dxf.layer))
    ids = [l["id"] for l in labels]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        log("警告：機台編號重複：", dups)

    # ---- 找出包住編號的圖塊（機台外框）
    inserts = []
    for e in msp.query("INSERT"):
        try:
            bb = bbox.extents([e], fast=True)
        except Exception:
            continue
        if not bb.has_data:
            continue
        w, h = bb.extmax.x - bb.extmin.x, bb.extmax.y - bb.extmin.y
        if 80 <= w <= 600 and 80 <= h <= 600:
            inserts.append(dict(handle=e.dxf.handle, name=e.dxf.name,
                                bb=[bb.extmin.x, bb.extmin.y, bb.extmax.x, bb.extmax.y]))
    used = set()
    machines = []
    for L in labels:
        inside = [c for c in inserts if c["handle"] not in used
                  and c["bb"][0] - 5 <= L["x"] <= c["bb"][2] + 5 and c["bb"][1] - 5 <= L["y"] <= c["bb"][3] + 5]
        if inside:
            c = min(inside, key=lambda c: (c["bb"][2] - c["bb"][0]) * (c["bb"][3] - c["bb"][1]))
            used.add(c["handle"])
            machines.append(dict(L, bb=c["bb"], est=False))
        else:
            machines.append(dict(L, bb=None, est=True))
    for m in machines:
        if not m["est"]:
            continue
        ref = [r for r in machines if not r["est"] and r["model"] == m["model"]] or [r for r in machines if not r["est"]]
        r = min(ref, key=lambda r: (r["x"] - m["x"]) ** 2 + (r["y"] - m["y"]) ** 2)
        dx, dy = m["x"] - r["x"], m["y"] - r["y"]
        m["bb"] = [r["bb"][0] + dx, r["bb"][1] + dy, r["bb"][2] + dx, r["bb"][3] + dy]
        log(f"注意：{m['id']} 沒有機台圖塊，參考 {r['id']} 估算外框")

    # 機台細節圖層（編號文字所在圖層、brother_*、TR-60A）不畫，改用狀態色塊表示
    machine_layers = {l["layer"] for l in labels} | {"TR-60A"}
    skip_layer = lambda ly: ly in machine_layers or ly.lower().startswith("brother")

    # ---- 區域名稱
    areas = []
    for e in msp.query("MTEXT TEXT"):
        t = text_of(e).strip()
        if not t or MACHINE_RE.search(t):
            continue
        h = getattr(e.dxf, "char_height", None) or getattr(e.dxf, "height", 20)
        areas.append(dict(text=re.sub(r"\s+", " ", t), x=e.dxf.insert.x, y=e.dxf.insert.y, h=h))

    # ---- 背景幾何
    lines, fills = defaultdict(list), defaultdict(list)

    def emit(e, layer):
        t = e.dxftype()
        if t in ("MTEXT", "TEXT", "MULTILEADER", "ATTRIB", "ATTDEF", "DIMENSION"):
            return
        if skip_layer(layer):
            return
        c = layer_class(layer)
        try:
            if t == "HATCH":
                for p in path.from_hatch(e):
                    pts = list(p.flattening(FLATTEN))
                    if len(pts) > 2:
                        fills[c].append(pts)
                return
            if t == "INSERT":
                for v in e.virtual_entities():
                    emit(v, v.dxf.layer if v.dxf.layer != "0" else layer)
                return
            pts = list(path.make_path(e).flattening(FLATTEN))
            if len(pts) > 1:
                lines[c].append(pts)
        except Exception:
            pass

    for e in msp:
        if e.dxftype() == "INSERT" and e.dxf.handle in used:
            continue
        emit(e, e.dxf.layer)

    pts = [p for g in lines.values() for pl in g for p in pl]
    minx, maxx = min(p.x for p in pts), max(p.x for p in pts)
    miny, maxy = min(p.y for p in pts), max(p.y for p in pts)
    X = lambda x: round(x - minx + MARGIN)
    Y = lambda y: round(maxy - y + MARGIN)

    def d(pl, close=False):
        out, last = [], None
        for p in pl:
            q = (X(p.x), Y(p.y))
            if q != last:
                out.append(f"{q[0]} {q[1]}")
                last = q
        if len(out) < 2:
            return ""
        return "M" + "L".join(out) + ("Z" if close else "")

    plan = dict(
        source=dxf_path.split("/")[-1],
        W=round(maxx - minx + 2 * MARGIN), H=round(maxy - miny + 2 * MARGIN),
        lines={c: "".join(d(pl) for pl in g) for c, g in lines.items()},
        fills={c: "".join(d(pl, True) for pl in g) for c, g in fills.items()},
        machines=[dict(id=m["id"], model=m["model"], x=X(m["bb"][0]), y=Y(m["bb"][3]),
                       w=round(m["bb"][2] - m["bb"][0]), h=round(m["bb"][3] - m["bb"][1]))
                  for m in sorted(machines, key=lambda m: int(m["id"][1:]))],
        areas=[dict(text=a["text"], x=X(a["x"]), y=Y(a["y"]), h=round(a["h"])) for a in areas],
    )
    log(f"完成：{len(plan['machines'])} 台機台、{len(plan['areas'])} 個區域名稱，畫布 {plan['W']}×{plan['H']}")
    print("// 由 tools/dxf-to-floorplan.py 自動產生，請勿手動修改。來源：" + plan["source"])
    print("window.FLOORPLANS = window.FLOORPLANS || {};")
    print(f"window.FLOORPLANS[{json.dumps(floor_key)}] = " + json.dumps(plan, ensure_ascii=False, separators=(",", ":")) + ";")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
