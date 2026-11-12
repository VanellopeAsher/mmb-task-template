import hashlib, pathlib, requests

OWNER="meiirbek-islamov"
REPO="defective-UiO-66"
BRANCH="main"
BASE=f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/"
OUT=pathlib.Path("/workspace/data/structures")
OUT.mkdir(parents=True,exist_ok=True)

FILES=[
("sample_01.cif","CIFs/randomly-distributed-defects/missing-linker-defects/uio66-3x3x3-defective_linkers_1%.cif","1bdcdd83b08ae69c0cbdad414915e6fb2b6390ec"),
("sample_02.cif","CIFs/randomly-distributed-defects/missing-linker-defects/uio66-3x3x3-defective_linkers_10%.cif","2c5050a0715beac02489582104505fb2275a0277"),
("sample_03.cif","CIFs/randomly-distributed-defects/missing-linker-defects/uio66-3x3x3-defective_linkers_20%.cif","2fbc901fc459bd78be162d4a16a5a8fca4c8731c"),
("sample_04.cif","CIFs/randomly-distributed-defects/missing-cluster-defects/uio66-3x3x3-defective-cluster_1%.cif","90e08035f8328ea2014f4a3e0a9ac09d7e6c0150"),
("sample_05.cif","CIFs/randomly-distributed-defects/missing-cluster-defects/uio66-3x3x3-defective-cluster_10%.cif","5d588c060e58b34b06cb7c83b7dceeb73500f8bd"),
("sample_06.cif","CIFs/randomly-distributed-defects/missing-cluster-defects/uio66-3x3x3-defective-cluster_20%.cif","c909402dc6e0e3e9cde43acd2c2961c2b67e4b5d"),
("sample_07.cif","CIFs/correlated-nanoregions-UiO-66/uio66-1x1x1-defective-cluster_reo.cif","dd61e6712d4e36735847a633d7ad4f195bd8ebff"),
("sample_08.cif","CIFs/correlated-nanoregions-UiO-66/uio66-1x1x1-defective_cluster_scu.cif","3aa9713da9662d99ef85a8358294b492de4f4753"),
("sample_09.cif","CIFs/correlated-nanoregions-UiO-66/uio66-1x1x1-defective_linker_bcu.cif","d190de5199b8009c1dd591cf417ef5e4a36f5d96"),
]
for name, rel, expected in FILES:
    r=requests.get(BASE+rel,timeout=120)
    r.raise_for_status()
    data=r.content
    blob=b"blob "+str(len(data)).encode()+b"\0"+data
    actual=hashlib.sha1(blob).hexdigest()
    if actual != expected:
        raise RuntimeError(f"{name}: Git blob SHA mismatch {actual} != {expected}")
    (OUT/name).write_bytes(data)
    print(f"verified {name} ({len(data)} bytes)")
