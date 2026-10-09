"""Download public Simplified Chinese localizations, excluding subscriber content."""
import json,subprocess,concurrent.futures,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('n',ROOT/'scripts/normalize-catalog.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
def fetch(q):
 p=ROOT/'sources/catalog'/(q['id']+'-zh_hans.json')
 if not p.exists():
  result=subprocess.run(['curl','-fLsS','--max-time','20','--retry','1','https://murdoku.com/play_puzzles/zh_hans/'+q['id']+'-zh_hans.json','-o',str(p)],capture_output=True)
  if result.returncode:return q['id']+' unavailable'
 json.loads(p.read_text());return q['id']+' OK'
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for result in pool.map(fetch,json.loads((ROOT/'sources/catalog/available.json').read_text())):print(result,flush=True)
