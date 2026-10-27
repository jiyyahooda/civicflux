import {useState} from 'react';
import {CloudRain,Droplets,Car,Layers,Sun,Waves,Play,ArrowRight} from 'lucide-react';
import type {Scenario,ScenarioInput,Graph} from '../types/api';
import ResourceAllocation from '../components/ResourceAllocation';
import {runScenario} from '../api/operations';

const presets=[
  {id:'light',title:'Light stress',note:'Low rain · single pump outage',icon:Sun,rain:5,load:.75,blockage:.1,initial:['pump_0']},
  {id:'rain',title:'Heavy rainfall',note:'High forcing · drainage outage',icon:CloudRain,rain:100,load:1.3,blockage:.7,initial:['drainage_0']},
  {id:'water',title:'Water disruption',note:'Water asset · network exposure',icon:Droplets,rain:30,load:1.1,blockage:.4,initial:['water_0']},
  {id:'road',title:'Road disruption',note:'Road outage · service dependencies',icon:Car,rain:40,load:1.15,blockage:.3,initial:['road_0']},
  {id:'pump',title:'Pump outage',note:'Monsoon load · pump failure seed',icon:Waves,rain:60,load:1.1,blockage:.5,initial:['pump_0']},
  {id:'compound',title:'Compound stress',note:'Three outages · peak scenario load',icon:Layers,rain:150,load:1.5,blockage:.85,initial:['pump_0','drainage_0','road_0']},
];
const defaultWeights={urgency:.25,cascade:.2,service:.2,equity_proxy:.15,environmental_benefit:.15,carbon_penalty:.05};

export default function Planning({defaults,scenario,admin,city,graph,onRun}:{defaults:ScenarioInput|null;scenario:Scenario|null;admin:boolean;city:string;graph:Graph|null;onRun:(s:Scenario)=>void}) {
  const [input,setInput]=useState<ScenarioInput|null>(null),[preset,setPreset]=useState('pump'),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const value=input??defaults;
  function change(v:Partial<ScenarioInput>){if(value){setInput({...value,...v});setPreset('custom')}}
  function choose(id:string){const p=presets.find(p=>p.id===id);if(!p||!value)return;setInput({...value,name:p.title+' research scenario',initial:p.initial,load:p.load,flood:{...value.flood,rain_mm:p.rain,blockage:p.blockage}});setPreset(id)}
  async function run(){if(!value)return;setBusy(true);setError('');try{onRun(await runScenario({...value,city_id:city}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
  const flood=Array.isArray(scenario?.flood.prediction)?scenario.flood.prediction[0]:undefined;
  return <><section className="panel scenario-lab"><div className="section-head"><div><span className="eyebrow">THE SCENARIO LAB</span><h3>What happens <em>next?</em></h3></div><span className="badge simulation">Synthetic research</span></div><p>Choose a scenario, adjust conditions and compare resource plans across the connected infrastructure graph.</p>
    {value?<fieldset disabled={!admin||busy}><div className="scenario-templates">{presets.map(p=><button key={p.id} className="scenario-template" aria-pressed={preset===p.id} onClick={()=>choose(p.id)}><p.icon size={20}/><strong>{p.title}</strong><small>{p.note}</small></button>)}</div><div className="form-grid">
      <label>Scenario name<input maxLength={100} minLength={3} value={value.name} onChange={e=>change({name:e.target.value})}/></label>
      <label>Flood engine<select value={value.flood_engine} onChange={e=>change({flood_engine:e.target.value as ScenarioInput['flood_engine']})}><option value="mass_balance">Mass-balance simulator · depth in metres</option><option value="trained_surrogate">Trained XGBoost · calibrated scenario score</option></select></label>
      <label>Declared outage{value.initial.length>1?'s':''}<select aria-label="Initial outage" value={value.initial.length>1?'compound':value.initial[0]} onChange={e=>change({initial:[e.target.value]})}>{value.initial.length>1&&<option value="compound">{value.initial.join(' + ')}</option>}{graph?.nodes.map(n=><option key={n.id}>{n.id}</option>)}</select></label>
      <label>Rainfall forcing <b>{value.flood.rain_mm} mm / event</b><input type="range" min="0" max="200" value={value.flood.rain_mm} onChange={e=>change({flood:{...value.flood,rain_mm:+e.target.value}})}/></label>
      <label>Cascade load <b>{value.load.toFixed(2)}×</b><input type="range" min="0.5" max="1.5" step="0.05" value={value.load} onChange={e=>change({load:+e.target.value})}/></label>
      <label>Hypothetical budget · INR<input type="number" min="0" max="10000000" step="1000" value={value.resources.budget} onChange={e=>change({resources:{...value.resources,budget:+e.target.value}})}/></label>
      <label>Available mobile pumps<input type="number" min="0" max="1000" step="1" value={value.resources.pumps} onChange={e=>change({resources:{...value.resources,pumps:+e.target.value}})}/></label>
      {Object.entries(value.resources.crew_hours).map(([kind,hours])=><label key={kind}>{kind} crew · hours<input type="number" min="0" max="10000" value={hours} onChange={e=>change({resources:{...value.resources,crew_hours:{...value.resources.crew_hours,[kind]:+e.target.value}}})}/></label>)}
    </div><details><summary>Adjust flood assumptions & policy weights</summary><p>Preset values are editable hypothetical inputs. They are not current weather, asset readings or causal effect estimates. Weights must satisfy the existing optimizer contract.</p><div className="form-grid">{Object.entries(value.flood).filter(([k])=>k!=='rain_mm').map(([k,v])=><label key={k}>{k.replaceAll('_',' ')}<input type="number" step="any" value={v} onChange={e=>change({flood:{...value.flood,[k]:+e.target.value}})}/></label>)}{Object.entries(value.weights??defaultWeights).map(([k,v])=><label key={k}>{k.replaceAll('_',' ')} weight<input type="number" min="0" max="1" step=".05" value={v} onChange={e=>change({weights:{...(value.weights??defaultWeights),[k]:+e.target.value}})}/></label>)}</div></details><button className="primary" disabled={busy||value.name.trim().length<3} onClick={run}>{busy?<span className="spinner"/>:<Play size={14}/>} {busy?'Running models & resource solver…':'Run synthetic scenario'} {!busy&&<ArrowRight size={15}/>}</button></fieldset>:<p role="status">Loading scenario defaults…</p>}
    {!admin&&<div className="notice">Civilian access · Explore saved results below. Admin login is required to change or run a scenario.</div>}{error&&<div className="error" role="alert">{error}</div>}
  </section>
  {scenario&&<><section className="panel"><div className="section-head"><div><span className="eyebrow">SCENARIO RESULTS</span><h3>{scenario.name}</h3></div><span className="badge simulation">{scenario.review_status.replaceAll('_',' ')}</span></div><small>{new Date(scenario.created).toLocaleString('en-IN')} · {scenario.city_id} workspace · hypothetical assets</small><div className="scenario-result-grid"><div><span>{scenario.inputs.flood_engine==='mass_balance'?'Simulated peak depth':'Calibrated flood research score'}</span><b>{flood?(typeof flood.depth_m==='number'?`${flood.depth_m.toFixed(3)} m`:typeof flood.simulated_flood_probability==='number'?Number(flood.simulated_flood_probability).toFixed(3):'Unavailable'):'Unavailable'}</b><small>{scenario.inputs.flood_engine==='mass_balance'?'Uncalibrated mass-balance physics':'Synthetic surrogate · not a real flood probability'}</small></div><div><span>Declared outages</span><b>{scenario.inputs.initial.length}</b><small>{scenario.inputs.initial.join(' · ')}</small></div><div><span>CP-SAT selected</span><b>{scenario.allocation.comparisons['CP-SAT'].selected.length}</b><small>{scenario.allocation.comparisons['CP-SAT'].status} · Human review required</small></div></div></section><ResourceAllocation scenario={scenario}/></>}
  </>
}
