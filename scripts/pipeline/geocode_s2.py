# -*- coding: utf-8 -*-
"""S2 队列地理编码：用 Nominatim(OSM) 把行政区名转成质心坐标。

- 限速 1.1 s/req（Nominatim 使用政策）
- 重音字符回退：'Maranhao' → 'Maranhão'
- 国家级直接取该国 centroid
- 结果写回 site_geo_s2.tsv，并另存一份只含坐标的精简表
"""
import csv, os, io, time, json, urllib.request, urllib.parse, sys

T = r"C:\SF_data\tools"
SRC = os.path.join(T, "site_geo_s2.tsv")
DST = SRC
PROXY = "http://127.0.0.1:7897"
UA = "sfru-cohort-geocoder/1.0 (research; contact: hugo@nmu)"

ACCENT = {
    "Maranhao": "Maranhão", "Goias": "Goiás", "Sao Paulo": "São Paulo",
    "Chapeco": "Chapecó", "Rolandia": "Rolândia", "Uberlandia": "Uberlândia",
    "Ponta Pora": "Ponta Porã", "Querencia": "Querência",
    "Luis Eduardo Magalhaes": "Luís Eduardo Magalhães",
    "Juana Diaz": "Juana Díaz", "Campo Mourao": "Campo Mourão",
    "Pouso Alegre de Minas": "Pouso Alegre de Minas",
    "Sao Gabriel do Oeste": "São Gabriel do Oeste",
    "Santa Cruz das Palmeiras": "Santa Cruz das Palmeiras",
    "Chapadao do Sul": "Chapadão do Sul", "Frutal": "Frutal",
    "Ourinhos": "Ourinhos", "Itapetininga": "Itapetininga",
    "Pato Branco": "Pato Branco", "Guarapuava": "Guarapuava",
    "Palotina": "Palotina", "Carazinho": "Carazinho",
    "Santa Rosa": "Santa Rosa", "Dourados": "Dourados",
    "Balsas": "Balsas", "Jatai": "Jataí", "Sinop": "Sinop",
    "Sapezal": "Sapezal", "Conchal": "Conchal", "Formosa": "Formosa",
    "Rio Verde": "Rio Verde", "Ponta Grossa": "Ponta Grossa",
    "Lucas do Rio Verde": "Lucas do Rio Verde",
    "Campo Verde": "Campo Verde",
}

_op = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
_op.addheaders = [("User-Agent", UA)]


def q(query, limit=1):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": limit, "addressdetails": 0})
    for _ in range(3):
        try:
            with _op.open(url, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(2.5)
    print(f"    [warn] {query}: {type(last).__name__}", file=sys.stderr)
    return []


def accentify(qs):
    out = qs
    for a, b in ACCENT.items():
        out = out.replace(a, b)
    return out


rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"))
print(f"共 {len(rows)} 个空间点待编码\n")
hit = miss = 0
for i, r in enumerate(rows, 1):
    if r.get("lat"):
        continue
    base = r["geo_string"]
    cands = [r["source_note"]]
    acc = accentify(r["source_note"])
    if acc != r["source_note"]:
        cands.append(acc)
    got = None
    for cq in cands:
        res = q(cq)
        time.sleep(1.1)
        if res:
            got = (res[0], cq)
            break
    if got:
        res, used = got
        r["lat"], r["lon"] = f"{float(res['lat']):.4f}", f"{float(res['lon']):.4f}"
        r["source_note"] = f"OSM:{res.get('type','?')}|{used}"
        hit += 1
        flag = ""
    else:
        r["lat"], r["lon"] = "", ""
        r["source_note"] = "MISS"
        miss += 1
        flag = "  <<< MISS"
    print(f"{i:>3}/{len(rows)}  {'OK ' if got else '×× '} {base:<48} "
          f"{r['lat']:>10} {r['lon']:>10}{flag}")

with open(DST, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["geo_string", "country", "subnational", "n_samples",
                                      "module", "level", "lat", "lon", "source_note"],
                       delimiter="\t")
    w.writeheader()
    w.writerows(rows)
print(f"\n命中 {hit} / 缺失 {miss} → {DST}")
