import {type CSSProperties} from 'react';
import {ArrowUpRight,CloudRain,Wind,Network,MessageSquare,ShieldCheck,MapPin,Droplets,Thermometer,Clock3,ChevronRight} from 'lucide-react';
import CityHero from '../components/CityHero';
import InfrastructureMap from '../components/InfrastructureMap';

import SourceStatus from '../components/SourceStatus';
import EnvironmentalChart from '../components/EnvironmentalChart';
import type {Model,Observations,Scenario,City,Graph,Complaint} from '../types/api';

export default function Dashboard({models,observations,scenarios,city,graph,complaints,navigate}:{models:Model[];observations:Observations|null;scenarios:Scenario[];city:City|undefined;graph:Graph|null;complaints:Complaint[];navigate:(page:string)=>void}) {
  const intro=true;
  const latest=scenarios[0],allocation=latest?.allocation.comparisons['CP-SAT'];
  const supported=models.filter(m=>m.readiness!=='Not ready').length;
  const localComplaints=complaints.filter(c=>c.city_id===city?.id);
  const weather=observations?.feeds.find(f=>f.source==='IMD'),air=observations?.feeds.find(f=>f.source==='CAMS');
  const stationCount=weather?.stations?.length??(weather?.readings?1:0);
  const freshStations=weather?.stations?.filter(s=>s.status==='fresh').length??(weather?.status==='fresh'?1:0);
  const value=(metric:string,feed=weather,digits=1)=>{const v=feed?.readings?.[metric]?.value;return typeof v==='number'?v.toFixed(digits):'—'};
  const budget=latest?.inputs.resources.budget??0,used=allocation?.used?.budget??0;
  const remaining=allocation&&budget?Math.round((budget-used)/budget*100):null;
  const recommendations=[...(allocation?.selected??[])].sort((a,b)=>b.utility-a.utility).slice(0,3);
  const events=[...(weather?.observed_at?[{time:weather.observed_at,title:'IMD station report',detail:weather.station_name??'Weather station',kind:'observed'}]:[]),
    ...(air?.observed_at?[{time:air.observed_at,title:'CAMS model valid time',detail:'Air-quality grid estimate · US AQI',kind:'estimate'}]:[]),
    ...(latest?[{time:latest.created,title:'Research scenario executed',detail:latest.name,kind:'simulation'}]:[]),
    ...localComplaints.slice(0,2).map(c=>({time:c.created,title:'Community report',detail:c.category.replaceAll('_',' ')+' · '+c.status.replaceAll('_',' '),kind:'community'}))].sort((a,b)=>Date.parse(b.time)-Date.parse(a.time)).slice(0,4);
  const Title=intro?'h2':'h1';
  return <div className="live-control-room">
    {intro&&<CityHero ready={supported} total={models.length} onExplore={()=>navigate('Model validation')}/>}
    <div id="city-dashboard" className="dashboard-content">
      <div className="dashboard-title"><div><span className="eyebrow"><i className="status-dot"/> CIVIC INTELLIGENCE / {city?.name.toUpperCase()}</span><Title>Your city, connected<span>.</span></Title><p>Live signals. Clear priorities. People in control.</p></div><div className="control-room-actions"><button className="glass-button" onClick={()=>navigate('Operations')}><MessageSquare size={13}/>Report a problem</button></div></div>
      <div className="room-status-strip">
        <div><span className="status-label"><MapPin size={13}/>IMD weather stations</span><strong>{stationCount.toString().padStart(2,'0')}<small>{weather?`${freshStations} fresh / ${stationCount-freshStations} stale`:'connecting'}</small></strong><small>Official locations & observation times</small></div>
        <div><span className="status-label"><Wind size={13}/>Air-quality context</span><strong>{value('us_aqi',air,0)}<small>US AQI · CAMS estimate</small></strong><small>Not a CPCB / Indian AQI reading</small></div>
        <div><span className="status-label"><Network size={13}/>Research components</span><strong>{supported}<small>/ {models.length} verified</small></strong><small>Trained artifacts · research only</small></div>
        <div><span className="status-label"><MessageSquare size={13}/>Open community reports</span><strong>{localComplaints.filter(c=>c.status!=='closed').length.toString().padStart(2,'0')}<small>{city?.name}</small></strong><small>{scenarios.length} saved research scenarios</small></div>
      </div>
      <div className="room-main-grid"><div className="room-map-column">{graph?<InfrastructureMap graph={graph} city={city?.name} scenario={latest} observations={observations}/>:<section className="panel loading-panel" role="status">Loading research topology…</section>}
        <div className="map-domain-strip"><span><i className="observed-dot"/>Measured station weather</span><span><i className="estimate-dot"/>Gridded air estimates</span><button onClick={()=>navigate('Cascade analysis')}>Explore synthetic cascades <ChevronRight size={12}/></button></div>
      </div><aside className="room-side-column">
        <section className="panel city-metrics"><div className="section-head"><h3>City environment</h3><span className="badge observed">IMD + CAMS</span></div><div className="city-metric-grid">
          {[{name:'Temperature',metric:'temperature',unit:'°C',icon:Thermometer,feed:weather,kind:'IMD observation'},
            {name:'Humidity',metric:'humidity',unit:'%',icon:Droplets,feed:weather,kind:'IMD observation'},
            {name:'Rainfall · 24h',metric:'rainfall',unit:'mm',icon:CloudRain,feed:weather,kind:'IMD 24h accumulation'},
            {name:'PM2.5',metric:'pm25',unit:'µg/m³',icon:Wind,feed:air,kind:'CAMS model estimate'}].map(m=><div key={m.metric}><m.icon size={17}/><span>{m.name}</span><strong>{value(m.metric,m.feed)}<small>{m.unit}</small></strong><small>{m.kind}</small></div>)}
        </div><small>{weather?.observed_at?`Observed ${new Date(weather.observed_at).toLocaleString('en-IN',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})} · ${weather.station_name}`:'Connecting to official weather source…'}</small></section>
        <section className="panel compact-readiness"><div className="mini-ring" style={{'--coverage':`${remaining!==null?remaining:models.length?supported/models.length*100:0}%`} as CSSProperties}><b>{remaining!==null?remaining+'%':`${supported}/${models.length}`}</b></div><div><span className="eyebrow">{remaining!==null?'RESOURCE HEADROOM':'MODEL READINESS'}</span><h3>{remaining!==null?'Budget remaining':'Verified research'}</h3><small>{remaining!==null?'Latest hypothetical allocation':'Not a city sustainability score'}</small><button className="text-button" onClick={()=>navigate(remaining!==null?'Planning':'Model validation')}>Inspect evidence <ArrowUpRight size={12}/></button></div></section>
        <section className="panel recommendations"><div className="section-head"><h3>Research action plan</h3><span className="badge simulation">Review required</span></div>{recommendations.length?recommendations.map((r,i)=><div className="recommendation" key={r.case_id}><span className="recommendation-rank">{i+1}</span><div><strong>{r.node_id.replaceAll('_',' ')} · {r.crew_type} crew</strong><small>Utility {r.utility.toFixed(3)} · ₹{r.cost.toLocaleString('en-IN')} · {r.duration_hours}h</small></div><button onClick={()=>navigate('Operations')}>Review</button></div>):<div className="compact-empty"><ShieldCheck size={20}/><p>Run a supported scenario to generate explainable resource choices.</p><button onClick={()=>navigate('Planning')}>Open scenario lab <ArrowUpRight size={13}/></button></div>}<small>Synthetic plans only. Nothing is automatically approved or dispatched.</small></section>
      </aside></div>
      <div className="room-secondary-grid"><section className="panel scenario-snapshot"><div className="section-head"><div><span className="eyebrow">RESEARCH SCENARIO</span><h3>{latest?latest.name:'Explore the pressure points'}</h3></div><button className="text-button" onClick={()=>navigate('Planning')}>Scenario lab <ArrowUpRight size={13}/></button></div>{latest?<><span className="badge simulation">{latest.review_status.replaceAll('_',' ')}</span><div className="scenario-mini-metrics"><span><b>{latest.inputs.flood.rain_mm}</b>mm / event</span><span><b>{latest.inputs.load.toFixed(2)}×</b>cascade load</span><span><b>{latest.inputs.initial.length}</b>declared outages</span><span><b>{allocation?.selected.length??0}</b>selected actions</span></div><small>{latest.inputs.initial.join(' · ')} · {allocation?.status} · Explicit synthetic assumptions</small></>:<div className="scenario-entry-grid">{['Light stress','Heavy rainfall','Water disruption','Road disruption','Pump outage','Compound stress'].map(name=><button key={name} onClick={()=>navigate('Planning')}><CloudRain size={13}/>{name}<ArrowUpRight size={12}/></button>)}</div>}</section><section className="panel event-timeline"><div className="section-head"><div><span className="eyebrow">SOURCE & WORKSPACE EVENTS</span><h3>Event timeline</h3></div><Clock3 size={16}/></div>{events.map((e,i)=><div className="timeline-event" key={i}><time>{new Date(e.time).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:false})}</time><i className={e.kind==='estimate'?'estimate-dot':'observed-dot'}/><div><strong>{e.title}</strong><small>{e.detail}</small></div></div>)}{!events.length&&<p>Waiting for validated source responses.</p>}</section></div>
      <EnvironmentalChart feed={air}/>
      <SourceStatus observations={observations}/>
    </div>
  </div>
}
