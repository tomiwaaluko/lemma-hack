from __future__ import annotations
import json, sqlite3
from pathlib import Path
from recall_desk.domain import OpState

class Journal:
    def __init__(self,path='recall.db',crash_hook=None):
        self.path=Path(path); self.db=sqlite3.connect(self.path); self.db.row_factory=sqlite3.Row
        self.crash_hook=crash_hook
        self.db.executescript('''create table if not exists runs(run_id text primary key,request_id text,phase integer default 0,state text,scope text,flags text default '{}');
        create table if not exists ops(op_id text primary key,run_id text,occurrence_key text,action text,target_id text,params text,step integer,state text default 'PLANNED');
        create table if not exists events(seq integer primary key autoincrement,run_id text,kind text,payload text);'''); self.db.commit()
    def _after(self,label):
        if self.crash_hook: self.crash_hook(label)
    def start(self,run_id,request_id): self.db.execute('insert or ignore into runs(run_id,request_id,state) values(?,?,?)',(run_id,request_id,'RUNNING'));self.db.commit()
    def finish(self,run_id): self.db.execute('update runs set state=? where run_id=?',('FINISHED',run_id));self.db.commit()
    def transition(self,op_id,state):
        state=state.value if hasattr(state,'value') else state
        row=self.db.execute('select action from ops where op_id=?',(op_id,)).fetchone()
        self.db.execute('update ops set state=? where op_id=?',(state,op_id));self.db.commit()
        self._after(f'transition:{op_id}:{state}:{row["action"] if row else ""}')
    def add_ops(self,ops):
        self.db.executemany('insert or ignore into ops values(?,?,?,?,?,?,?,?)',[(o.op_id,o.run_id,o.occurrence_key,o.action.value,o.target_id,json.dumps(o.params),o.step,'PLANNED') for o in ops]);self.db.commit()
    def set_phase(self,run_id,phase):self.db.execute('update runs set phase=? where run_id=?',(phase,run_id));self.db.commit()
    def set_flags(self,run_id,**flags):
        row=self.db.execute('select flags from runs where run_id=?',(run_id,)).fetchone();current=json.loads(row['flags']);current.update({k:current.get(k,False) or v for k,v in flags.items()});self.db.execute('update runs set flags=? where run_id=?',(json.dumps(current),run_id));self.db.commit()
    def close(self):self.db.close()
    def states_for_action(self,action): return [row['state'] for row in self.db.execute('select state from ops where action=? order by step',(action,))]
    def verified_archives_for_request(self,request_id):
        return {row['target_id'] for row in self.db.execute('select ops.target_id from ops join runs using(run_id) where runs.request_id=? and ops.action=? and ops.state=?',(request_id,'ARCHIVE_BLOCK','VERIFIED'))}
    def reconcilable_archives_for_request(self,request_id):
        return {row['target_id'] for row in self.db.execute('select ops.target_id from ops join runs using(run_id) where runs.request_id=? and ops.action=?',(request_id,'ARCHIVE_BLOCK'))}
