import {useState} from 'react';
import {ComposedChart,Area,Line,XAxis,YAxis,Tooltip,ResponsiveContainer,CartesianGrid,Brush} from 'recharts';
import {api} from '../api/client';
import {useApi} from '../hooks/useApi';
type Row={target_time:string;entity:string|number;target:number;prediction:number;lower:number;upper:number};

export default function ForecastChart({component}:{component:string}){
  const supported=['rainfall','aqi','traffic'].includes(component);
  const [entity,setEntity]=useState(''),[count,setCount]=useState(72);
  const source=useApi(()=>supported?api<{kind:string;rows:Row[]}>('predictions/'+component+'/series'):Promise.resolve({kind:'unavailable',rows:[]}),[component]);
  if(!supported)return null;
  const unit=component==='rainfall'?'mm/day':component==='aqi'?'PM2.5 µg/m³':'vehicles/hour';
  const entities=[...new Set(source.data?.rows.map(r=>String(r.entity))??[])];
  const current=entities.includes(entity)?entity:entities[0];
  const rows=source.data?.rows.filter(r=>String(r.entity)===current).slice(0,count).map(r=>({...r,interval:[r.lower,r.upper]}))??[];
  return <section className="panel forecast-chart"><div className="section-head"><div><h3>{component==='rainfall'?'Rainfall':component==='aqi'?'Air quality · PM2.5':'Traffic'} <span className="muted-text">/ {unit}</span></h3></div><div className="forecast-controls">{entities.length>1&&<label><select aria-label="Forecast benchmark entity" value={current} onChange={e=>setEntity(e.target.value)}>{entities.map(e=><option value={e} key={e}>Junction {e}</option>)}</select></label>}<div className="segmented">{[24,72].map(n=><button key={n} className={count===n?'selected':''} aria-label={`Show up to ${n} saved rows`} onClick={()=>setCount(n)}>{n} rows</button>)}</div></div></div>
    <p>Saved holdout observations and rolling predictions. Shaded band: 90% residual interval; no guaranteed coverage for a particular case.</p>
    <span className="badge research">Archived evaluation · {rows.length} records{current?` · ${component==='traffic'?'junction ':''}${current}`:''}</span>
    {source.error?<div className="error" role="alert">{source.error}<button onClick={source.reload}>Retry chart</button></div>:source.loading?<p role="status">Loading saved research evaluation…</p>:<div className="chart"><ResponsiveContainer><ComposedChart data={rows} margin={{left:-8,right:5,top:5,bottom:0}}><defs><linearGradient id={`forecast-${component}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--accent)" stopOpacity={.2}/><stop offset="100%" stopColor="var(--accent)" stopOpacity={.03}/></linearGradient></defs><CartesianGrid vertical={false} stroke="var(--line)" strokeDasharray="3 4"/><XAxis dataKey="target_time" tickFormatter={v=>String(v).slice(5,16)} stroke="var(--muted)" minTickGap={45} tickLine={false} axisLine={false}/><YAxis stroke="var(--muted)" width={45} tickLine={false} axisLine={false}/><Tooltip labelFormatter={v=>`Forecast target: ${v}`} contentStyle={{background:'var(--surface)',borderColor:'var(--line)',color:'var(--text)'}}/><Area type="linear" dataKey="interval" name="90% saved interval" fill={`url(#forecast-${component})`} stroke="none"/><Line type="linear" dataKey="target" name="Observed" stroke="var(--muted)" strokeWidth={1.5} dot={false}/><Line type="linear" dataKey="prediction" name="Research prediction" stroke="var(--accent)" strokeWidth={2} dot={false} activeDot={{r:4}}/><Brush dataKey="target_time" height={15} stroke="var(--line)" fill="var(--bg)" tickFormatter={()=>''} travellerWidth={5}/></ComposedChart></ResponsiveContainer></div>}
    <small>{rows.length?`${rows[0].target_time} → ${rows[rows.length-1].target_time}`:'No saved series loaded.'} · Archived research, not current conditions.</small>
  </section>
}
