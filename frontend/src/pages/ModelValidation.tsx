import {useState} from 'react';
import {Search,FlaskConical,ShieldCheck} from 'lucide-react';
import ModelStatus from '../components/ModelStatus';
import type {Model} from '../types/api';
export default function ModelValidation({models}:{models:Model[]}){
  const [search,setSearch]=useState('');
  const visible=models.filter(m=>`${m.component} ${m.selected_model} ${m.geographic_scope}`.toLowerCase().includes(search.toLowerCase()));
  return <><section className="panel"><div className="model-summary"><ShieldCheck size={25}/><strong>{models.filter(m=>m.readiness!=='Not ready').length} / {models.length}</strong><p>Components verified for supported research inference.<br/>Readiness does not grant operational approval.</p></div><div className="section-head"><div><span className="eyebrow">EVIDENCE YOU CAN INSPECT</span><h3>Models that power CivicFlux.</h3></div><FlaskConical size={22}/></div><p>Notebooks 01–11, all original model versions and research datasets are preserved. Traffic and flood use verified native exports attached to their original preprocessing and calibration. No retraining was performed.</p><label className="graph-search"><Search size={13}/><input aria-label="Search models" value={search} placeholder="Search model, method or scope…" onChange={e=>setSearch(e.target.value)}/></label></section>
  {visible.map(m=><section className="panel" key={m.component}><ModelStatus model={m}/><div className="two-columns"><div><p><strong>Scope & horizon</strong><br/>{m.geographic_scope} · {m.horizon}</p></div><div><p><strong>Verification</strong><br/>{m.readiness_reason}</p><p><strong>Artifact</strong><br/><code>{m.artifact??'Python CP-SAT component; no fitted model required'}</code></p><p><strong>Schema</strong><br/><code>{m.feature_schema}</code></p></div></div></section>)}{!visible.length&&<p>No models match this search.</p>}</>
}
