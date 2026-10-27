import {useState} from 'react';
import {Map,Network,ExternalLink} from 'lucide-react';
import CascadeGraph from './CascadeGraph';
import StationMap from './StationMap';
import type {Graph,Scenario,Observations} from '../types/api';

export default function InfrastructureMap({graph,city='Delhi',scenario,observations=null}:{graph:Graph;city?:string;scenario?:Scenario|null;observations?:Observations|null}) {
  const [view,setView]=useState<'network'|'map'|'google'>('map');
  return <section className="map-workspace">
    <div className="map-toolbar"><div><span className="eyebrow">CITY INTELLIGENCE</span><h3>{view==='network'?'Infrastructure dependency graph':`${city} · environmental monitoring`}</h3></div><div className="segmented" aria-label="Infrastructure view"><button className={view==='map'?'selected':''} onClick={()=>setView('map')}><Map size={13}/>Live map</button><button className={view==='network'?'selected':''} onClick={()=>setView('network')}><Network size={13}/>Dependencies</button><button className={view==='google'?'selected':''} onClick={()=>setView('google')}><ExternalLink size={12}/>Google</button></div></div>
    {view==='network'?<CascadeGraph graph={graph} initial={scenario?.inputs.initial} risks={Array.isArray(scenario?.cascade.prediction)?scenario.cascade.prediction:[]}/>:view==='map'?<StationMap observations={observations} city={city}/>:<div className="reference-map panel"><iframe key={city} title={`${city} city reference map`} src={`https://maps.google.com/maps?q=${encodeURIComponent(city+', India')}&z=11&output=embed`} loading="lazy" referrerPolicy="no-referrer-when-downgrade" allowFullScreen/><div className="map-disclaimer">GOOGLE GEOGRAPHIC REFERENCE · VERIFIED STATIONS ARE IN LIVE MAP</div></div>}
  </section>
}
