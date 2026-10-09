"""Fetch only the public, currently released catalog selected from the official index."""
import json,subprocess,concurrent.futures
from pathlib import Path
root=Path(__file__).resolve().parents[1]
entries=json.loads((root/'sources/catalog/available.json').read_text())
def fetch(q):
 path=root/'sources/catalog'/q['file']
 if path.exists():return q['id']+' cached'
 subprocess.run(['curl','-fLsS','--retry','2','--max-time','30','https://murdoku.com/play_puzzles/en/'+q['id']+'.json','-o',str(path)],check=True)
 json.loads(path.read_text());return q['id']+' OK'
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(fetch,entries):print(result,flush=True)
