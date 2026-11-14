"""Fetch unmodified author-review PDFs; verify both published MD5 and SHA256."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    m=json.loads(Path(__file__).with_name('source_manifest.json').read_text())
    for name,row,urlkey in [('paper.pdf',m['paper'],'published_pdf_url'),('si.pdf',m['supplement'],'url')]:
        data=urllib.request.urlopen(row[urlkey],timeout=120).read()
        for alg in ['md5','sha256']:
            if hashlib.new(alg,data).hexdigest()!=row[alg]:raise ValueError(f'{name} {alg} mismatch')
        (a.output/name).write_bytes(data);print(name,len(data),'verified')
