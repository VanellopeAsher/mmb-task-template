"""Compare recomputed coordinate/data result to independent private targets."""
import argparse,json,sys
from pathlib import Path
from generate_answer import generate
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from verify import verify
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('answer',type=Path,nargs='?',default=ROOT/'solution/answer.json');p.add_argument('--data-dir',type=Path,default=Path('/workspace/data'));a=p.parse_args()
 computed=generate(a.data_dir);verify(computed);verify(json.loads(a.answer.read_text(encoding='utf-8')));print('recomputed and saved Oracle match independent targets')
