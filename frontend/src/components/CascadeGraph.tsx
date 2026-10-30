import {assetLabel} from '../utils/assetLabel';
import {useId,useRef,useState} from 'react';
import {Plus,Minus,RotateCcw,ArrowUpRight,Search} from 'lucide-react';
import type {Graph} from '../types/api';

export default function CascadeGraph({graph,initial=[],risks=[],planned=[],city}:{city?:string;graph:Graph;initial?:string[];risks?:Record<string,unknown>[];planned?:string[]}) {
  const [selected,setSelected]=useState(graph.nodes[0]?.id??''),[zoom,setZoom]=useState(1),[filter,setFilter]=useState('all'),[search,setSearch]=useState('');
  const [pan,setPan]=useState({x:0,y:0});
  const drag=useRef<{id:number;x:number;y:number;originX:number;originY:number}|null>(null);
  const marker=useId().replaceAll(':','');
  const kinds=['pump','drainage','road','water','facility'];
  const riskMap=new Map(risks.map(r=>[String(r.node_id),Number(r.risk)]));
  const pos=(id:string)=>{const n=graph.nodes.find(n=>n.id===id)!;return {x:88+kinds.indexOf(n.node_type)*190,y:72+Number(id.split('_').at(-1))*66}};
  const node=graph.nodes.find(n=>n.id===selected);
  const edges=graph.edges.filter(e=>e.source===selected||e.target===selected);
  const visible=(id:string)=>{const n=graph.nodes.find(n=>n.id===id)!;return (filter==='all'||n.node_type===filter)&&(id+' '+assetLabel(id,city)).toLowerCase().includes(search.toLowerCase())};
  const changeZoom=(amount:number)=>{const next=Math.min(1.7,Math.max(.7,zoom+amount)),p=pos(selected);setZoom(next);setPan({x:p.x-500/next,y:p.y-310/next})};
  return <div data-tour="graph" className="panel graph-panel">
    <div className="network-stats"><span><b>{graph.nodes.length}</b> assets</span><span><b>{graph.edges.length}</b> dependencies</span><span className="badge simulation">Planning network</span><div className="graph-tools"><button aria-label="Zoom out" onClick={()=>changeZoom(-.15)}><Minus size={14}/></button><span>{Math.round(zoom*100)}%</span><button aria-label="Zoom in" onClick={()=>changeZoom(.15)}><Plus size={14}/></button><button aria-label="Reset graph zoom" onClick={()=>{setZoom(1);setPan({x:0,y:0});setFilter('all');setSearch('')}}><RotateCcw size={14}/></button></div></div>
    <div className="graph-filters"><label className="graph-search"><Search size={13}/><input aria-label="Find infrastructure asset" placeholder="Find an asset…" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="filter-chips">{['all',...kinds].map(k=><button key={k} aria-pressed={filter===k} onClick={()=>setFilter(k)}>{k}</button>)}</div></div>
    <div className="graph-scroll"><svg role="group" tabIndex={0} aria-label="Interactive schematic infrastructure graph" viewBox={`${pan.x} ${pan.y} ${1000/zoom} ${620/zoom}`}
      onKeyDown={e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();setPan(p=>({x:p.x+(e.key==='ArrowRight'?50:e.key==='ArrowLeft'?-50:0),y:p.y+(e.key==='ArrowDown'?50:e.key==='ArrowUp'?-50:0)}))}}}
      onPointerDown={e=>{if((e.target as Element).closest('.graph-node'))return;drag.current={id:e.pointerId,x:e.clientX,y:e.clientY,originX:pan.x,originY:pan.y};e.currentTarget.setPointerCapture(e.pointerId)}}
      onPointerMove={e=>{const d=drag.current;if(!d)return;const r=e.currentTarget.getBoundingClientRect();setPan({x:d.originX-(e.clientX-d.x)*1000/(zoom*r.width),y:d.originY-(e.clientY-d.y)*620/(zoom*r.height)})}}
      onPointerUp={e=>{drag.current=null;if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId)}}
      onPointerCancel={()=>{drag.current=null}}>
      <defs><marker id={marker} markerWidth="6" markerHeight="6" refX="25" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3z" fill="var(--accent)"/></marker><pattern id={marker+'grid'} width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".75" fill="var(--line)"/></pattern></defs>
      <rect x="-3000" y="-3000" width="6000" height="6000" fill={`url(#${marker}grid)`}/>
      {kinds.map((k,i)=><text className="graph-label" key={k} x={88+i*190} y="27" textAnchor="middle">{k.toUpperCase()}</text>)}
      {graph.edges.map((e,i)=>{const a=pos(e.source),b=pos(e.target),active=e.source===selected||e.target===selected;return <path key={i} d={`M ${a.x} ${a.y} C ${a.x+75} ${a.y},${b.x-75} ${b.y},${b.x} ${b.y}`} className={active?'edge active':'edge'} style={{opacity:visible(e.source)||visible(e.target)?undefined:.025}} markerEnd={active?`url(#${marker})`:undefined}/>})}
      {graph.nodes.map(n=>{const p=pos(n.id),risk=riskMap.get(n.id),failed=initial.includes(n.id);return <g key={n.id} role="button" tabIndex={0} aria-label={`Inspect ${assetLabel(n.id,city)}`} aria-pressed={selected===n.id} onClick={()=>setSelected(n.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(n.id)}}} style={{opacity:visible(n.id)?1:.12}} className={(planned.includes(n.id)?'planned-asset ':'')+'graph-node '+(selected===n.id?'selected ':'')+(failed?'failed':'')}><title>{assetLabel(n.id,city)} · criticality {n.criticality.toFixed(2)}{risk!==undefined?` · planning score ${risk.toFixed(3)}`:''}</title><circle className="node-halo" cx={p.x} cy={p.y} r="25"/><circle cx={p.x} cy={p.y} r="17"/><text className="node-index" x={p.x} y={p.y+4} textAnchor="middle">{failed?'!':n.id.split('_').at(-1)}</text><text x={p.x} y={p.y+34} textAnchor="middle">{assetLabel(n.id,city).split(' · ')[0].slice(0,23)}</text>{risk!==undefined&&<rect x={p.x-18} y={p.y+40} width={36*risk} height="2" rx="1" fill="var(--accent)"/>}</g>})}
    </svg></div>
    {node&&<div className="graph-inspector"><div><span className="eyebrow">SELECTED ASSET</span><strong>{assetLabel(node.id,city)} <ArrowUpRight size={14}/></strong></div><span>Criticality <b>{node.criticality.toFixed(2)}</b></span><span>Resilience <b>{node.resilience.toFixed(2)}</b></span>{riskMap.has(node.id)&&<span>Planning score <b>{riskMap.get(node.id)?.toFixed(3)}</b></span>}<small>{edges.length} connections · {edges.slice(0,3).map(e=>`${assetLabel(e.source,city)} → ${assetLabel(e.target,city)} (${e.delay_minutes} min)`).join(' · ')||'No direct dependencies'}</small></div>}
    <small className="graph-footnote">{graph.attributes.graph_id} · Drag or use arrow keys to pan · Provider → dependent · {initial.length?'Filled nodes are declared outages.':'Select an asset to trace its connections.'} Planning scores are not real-world failure probabilities. Named geographic associations are illustrative scenario locations.</small>
  </div>
}

