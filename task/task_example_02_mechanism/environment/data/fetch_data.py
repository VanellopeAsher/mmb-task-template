import hashlib, json, pathlib, requests, zipfile, io

BASE = "https://entrepot.recherche.data.gouv.fr"
PID = "doi:10.57745/EQL6HT"
EXPECTED = {
    "DataXAS.zip": "085ecb1b86089a542f909c5d867d50b0",
    "MassSpectrometer.zip": "6ea7054361b23d8bb6022dd3d0761b86",
}
out = pathlib.Path("/workspace/data/raw")
out.mkdir(parents=True, exist_ok=True)
meta = requests.get(f"{BASE}/api/datasets/:persistentId/", params={"persistentId": PID}, timeout=60)
meta.raise_for_status()
files = meta.json()["data"]["latestVersion"]["files"]
for name, md5 in EXPECTED.items():
    match = next((f for f in files if f["dataFile"]["filename"] == name), None)
    if match is None:
        raise RuntimeError(f"Dataverse record does not contain {name}")
    file_id = match["dataFile"]["id"]
    response = requests.get(f"{BASE}/api/access/datafile/{file_id}", timeout=300)
    response.raise_for_status()
    payload = response.content
    actual = hashlib.md5(payload).hexdigest()
    if actual != md5:
        raise RuntimeError(f"{name}: MD5 mismatch {actual} != {md5}")
    target = out / name
    target.write_bytes(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        zf.extractall(out / name.removesuffix(".zip"))
    print(f"verified and extracted {name} ({len(payload)} bytes)")
