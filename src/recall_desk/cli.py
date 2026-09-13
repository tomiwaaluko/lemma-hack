from __future__ import annotations
import argparse,runpy,sys
from pathlib import Path
from recall_desk.journal import Journal
from recall_desk.orchestrator import run_req001
from recall_desk.report import render_markdown
from recall_desk.snapshot import check_fixtures,load_snapshot,reset_to_snapshot
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
def _ports():
    return runpy.run_path('scripts/m0_slice.py')['live_ports']()
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('command',choices=['reset','check-fixtures','run']);p.add_argument('request',nargs='?');p.add_argument('--approve',action='store_true');a=p.parse_args(argv);settings,notion,trello,airtable,reset=_ports();snap=load_snapshot()
    if a.command=='reset': reset_to_snapshot(reset,notion,trello,snap,'REQ-001','AST-001');print('reset PASS');return 0
    if a.command=='check-fixtures':
        bad=check_fixtures(notion,trello,airtable,snap);print('check-fixtures ✓ PASS' if not bad else bad);return int(bool(bad))
    if not a.approve: print('Use --approve');return 1
    summary=run_req001(settings,notion,trello,airtable,Journal(settings.db_path));Path('runs').mkdir(exist_ok=True);Path(f'runs/{summary.run_id}.md').write_text(render_markdown(summary,[]));print(f'Final result: {summary.final_result.value}\n{summary.run_id}\n{summary.counts}');return 0
if __name__=='__main__':raise SystemExit(main())
