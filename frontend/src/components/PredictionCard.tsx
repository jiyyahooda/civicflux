import type {Example} from '../types/api';
export default function PredictionCard({example}:{example:Example}){
  const p=example.response;
  const rows=Array.isArray(p.prediction)?p.prediction:[];
  const object=(!Array.isArray(p.prediction)&&p.prediction?p.prediction:rows[0])??{};
  let value=p.status.replaceAll('_',' '),label='Serving status';
  if(p.status.startsWith('supported')){
    if(typeof object.prediction==='number'){value=object.prediction.toFixed(2);label='Research forecast'}
    else if(typeof object.simulated_flood_probability==='number'){value=object.simulated_flood_probability.toFixed(3);label='Calibrated synthetic flood score'}
    else if(typeof object.benchmark_onset_score==='number'){value=object.benchmark_onset_score.toFixed(3);label='L-TOWN benchmark onset score'}
    else if(typeof object.anomaly_score==='number'){value=object.anomaly_score.toFixed(3);label='Anomaly score · not proof of equipment failure'}
    else if(typeof object.research_resolution_hours==='number'){value=object.research_resolution_hours.toFixed(2)+' h';label='Synthetic research resolution estimate'}
    else if(p.component==='cascade_risk'){value=rows.length+' assets';label='Synthetic assets scored for the next 60 minutes'}
    else if(Array.isArray(object.selected)){value=object.selected.length+' selected';label='Hypothetical resource allocation'}
  }
  return <article className="panel prediction-card"><span className={'badge '+(example.input_kind.includes('synthetic')?'simulation':'research')}>{example.input_kind}</span><h3>{p.component.replaceAll('_',' ')}</h3><strong className="metric-value">{value}</strong><small>{label}</small><p>{typeof p.units==='string'?p.units:Object.entries(p.units as Record<string,string>??{}).map(([k,v])=>`${k}: ${v}`).join(' · ')} · {p.horizon}</p><small>Fixture/request clock: {example.request_clock}<br/>Input age at that clock: {p.freshness?.age_hours??'unavailable'} hours</small>{p.uncertainty?<p className="interval">90% residual interval: {p.uncertainty.intervals.map(i=>`${i.lower_90.toFixed(2)}–${i.upper_90.toFixed(2)}`).join(', ')}<small>{p.uncertainty.method}</small></p>:<p className="interval">Uncertainty interval unavailable for this component.</p>}<small>{p.geographic_scope}</small></article>
}
