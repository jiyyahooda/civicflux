import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {Crosshair,Layers,CloudRain,Wind,X} from 'lucide-react';
import type {Feed,Observations} from '../types/api';

const keyFor=(f:Feed)=>f.source+':'+(f.station_id??'model-grid');
export default function StationMap({observations,city}:{observations:Observations|null;city:string}){
  const container=useRef<HTMLDivElement>(null),map=useRef<L.Map|null>(null),markers=useRef<L.LayerGroup|null>(null);
  const [weather,setWeather]=useState(true),[air,setAir]=useState(true),[selectedKey,setSelectedKey]=useState<string|null>(null),[tileError,setTileError]=useState(false);
  const reference=observations?.map_reference;
  const imd=observations?.feeds.find(f=>f.source==='IMD');
  const cams=observations?.feeds.find(f=>f.source==='CAMS');
  const points=[...(imd?.stations??(imd?.readings?[imd]:[])),...(cams?.readings?[cams]:[])].filter(f=>f.coordinates);
  const selected=points.find(f=>keyFor(f)===selectedKey);
  useEffect(()=>{
    if(!container.current||!reference)return;
    const m=L.map(container.current,{zoomControl:false,scrollWheelZoom:false,attributionControl:true}).setView([reference.latitude,reference.longitude],11);
    const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>'}).addTo(m);
    tiles.on('tileerror',()=>setTileError(true));tiles.on('load',()=>setTileError(false));
    L.control.zoom({position:'bottomright'}).addTo(m);
    map.current=m;markers.current=L.layerGroup().addTo(m);
    const resize=new ResizeObserver(()=>m.invalidateSize());resize.observe(container.current);
    return()=>{resize.disconnect();m.remove();map.current=null;markers.current=null};
  },[observations?.city_id,reference?.latitude,reference?.longitude]);
  useEffect(()=>{
    const group=markers.current;if(!group)return;group.clearLayers();
    points.forEach(point=>{
      const estimate=point.kind==='model_estimate';if((estimate&&!air)||(!estimate&&!weather)||!point.coordinates)return;
      const metric=point.readings?.[estimate?'us_aqi':'temperature'];
      const badge=document.createElement('div');badge.className='station-pin '+(estimate?'pin-estimate':'pin-observed')+(point.status==='stale'?' pin-stale':'');
      const icon=document.createElement('span');icon.textContent=estimate?'A':'W';
      const value=document.createElement('b');value.textContent=metric?`${metric.value.toFixed(estimate?0:1)}${estimate?'':'°'}`:'—';
      badge.append(icon,value);
      const marker=L.marker([point.coordinates.latitude,point.coordinates.longitude],{
        icon:L.divIcon({html:badge,className:'station-marker',iconSize:[76,34],iconAnchor:[38,17]}),
        title:estimate?`CAMS model estimate · US AQI · ${point.status}`:`${point.station_name} · IMD temperature · ${point.status}`,keyboard:true});
      marker.on('click',()=>setSelectedKey(keyFor(point)));marker.addTo(group);
    });
  },[observations,weather,air,reference]);
  if(!reference)return <div className="station-map-empty panel" role="status">Loading the verified city reference and source locations…</div>;
  return <div className="station-map-frame">
    <div ref={container} className="station-map-canvas" aria-label={`${city} street map with weather stations and a separate CAMS model-grid estimate`}/>
    <div className="map-layer-controls"><span><Layers size={12}/>MAP LAYERS</span><button aria-pressed={weather} onClick={()=>setWeather(!weather)}><CloudRain size={13}/>IMD stations</button><button aria-pressed={air} onClick={()=>setAir(!air)}><Wind size={13}/>CAMS estimate</button><button aria-label="Recenter city map" onClick={()=>map.current?.setView([reference.latitude,reference.longitude],11)}><Crosshair size={15}/></button></div>
    <div className="map-location-label"><span className="eyebrow">GEOGRAPHIC VIEW</span><b>{city}</b><small>{points.filter(p=>p.kind!=='model_estimate').length} verified IMD station locations</small></div>
    {tileError&&<div className="map-tile-error">Map tiles are not loading. Check the network; source readings remain available.</div>}
    {selected&&<section className="station-inspector"><button className="close-button" aria-label="Close station details" onClick={()=>setSelectedKey(null)}><X size={14}/></button><span className={'badge '+(selected.kind==='model_estimate'?'estimate':'observed')}>{selected.kind==='model_estimate'?'Model estimate':'Measured station observation'} · {selected.status}</span><h3>{selected.station_name}</h3><div className="inspector-readings">{Object.entries(selected.readings??{}).map(([key,r])=><span key={key}>{r.label??key}<b>{r.value.toFixed(key.includes('aqi')?0:1)} <small>{r.unit}</small></b></span>)}</div><p>{selected.scope}</p><small>{selected.kind==='model_estimate'?'Valid':'Observed'} {selected.observed_at?new Date(selected.observed_at).toLocaleString('en-IN'):'time unavailable'}</small>{selected.index_standard&&<small>{selected.index_standard}</small>}<a href={selected.provider_url} target="_blank" rel="noreferrer">Provider ↗</a></section>}
    <div className="station-map-legend"><span><i className="observed-dot"/>Weather: IMD measurements</span><span><i className="estimate-dot"/>Air: CAMS estimates, US AQI</span><small>No synthetic asset or complaint coordinates are plotted.</small></div>
  </div>
}
