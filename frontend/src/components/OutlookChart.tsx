import {useState} from 'react';
import {ResponsiveContainer,ComposedChart,Line,Bar,XAxis,YAxis,Tooltip,CartesianGrid} from 'recharts';
import {api} from '../api/client';
import {useApi} from '../hooks/useApi';
type Row={date:string;temperature_2m_max:number;temperature_2m_min:number;precipitation_sum:number;wind_speed_10m_max:number};
type Outlook={city_id:string;status:string;rows:Row[];available_days:number;complete:boolean;attribution:string;fetched_at?:string;reason?:string;warning?:string};
const day=(v:string)=>new Date(v+'T12:00:00').toLocaleDateString('en-IN',{day:'numeric',month:'short'});
export default function OutlookChart({cityId,cityName}:{cityId:string;cityName?:string}){
 const [days,setDays]=useState(14);
 const request=useApi(()=>api<Outlook>('predictions/outlook/'+cityId),[cityId]);
 const data=request.data?.city_id===cityId?request.data:null,rows=data?.rows.slice(0,days)??[];
 return <section className="panel outlook-panel"><div className="section-head"><div><span className="eyebrow">The days ahead · {cityName}</span><h2>Your city’s next <em>{days} days.</em></h2></div><div className="segmented">{[2,14].map(n=><button key={n} className={days===n?'selected':''} onClick={()=>setDays(n)}>{n===14?'2 weeks':'2 days'}</button>)}</div></div><div className="outlook-subtitle"><span className="badge estimate">Weather forecast · Open-Meteo</span><span>Temperature °C · Daily precipitation mm</span></div>
 {request.loading&&<p role="status">Loading the upcoming weather outlook…</p>}
 {(request.error||data?.status==='unavailable')&&<div className="error" role="alert">{request.error??data?.reason}<button onClick={request.reload}>Try again</button></div>}
 {data?.warning&&<p className="warning">Cached forecast · {data.warning}</p>}
 {!!rows.length&&<><div className="outlook-chart"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={rows} margin={{top:20,right:8,bottom:10,left:0}}><CartesianGrid stroke="var(--line)" vertical={false}/><XAxis dataKey="date" tickFormatter={day} tick={{fill:'var(--muted)',fontSize:11}} minTickGap={20}/><YAxis yAxisId="temperature" unit="°" width={38} tick={{fill:'var(--muted)',fontSize:11}}/><YAxis yAxisId="rain" orientation="right" unit="mm" width={43} tick={{fill:'var(--muted)',fontSize:11}}/><Tooltip labelFormatter={v=>day(String(v))} contentStyle={{background:'var(--surface)',border:'1px solid var(--line)',borderRadius:14,color:'var(--text)'}}/><Bar yAxisId="rain" dataKey="precipitation_sum" name="Precipitation (mm)" fill="#57a7ea" opacity={.4} radius={[5,5,0,0]}/><Line yAxisId="temperature" dataKey="temperature_2m_max" name="High (°C)" stroke="var(--accent)" strokeWidth={3} dot={{r:3}}/><Line yAxisId="temperature" dataKey="temperature_2m_min" name="Low (°C)" stroke="#9b8af0" strokeWidth={2} dot={false}/></ComposedChart></ResponsiveContainer></div><div className="forecast-day-strip">{rows.map(r=><article key={r.date}><time>{day(r.date)}</time><strong>{Math.round(r.temperature_2m_max)}° <small>{Math.round(r.temperature_2m_min)}°</small></strong><span>{r.precipitation_sum} mm rain</span><span>{r.wind_speed_10m_max} km/h wind</span></article>)}</div><small>{data?.attribution} · {rows[0].date} – {rows[rows.length-1]?.date}{data?.fetched_at?' · Updated '+new Date(data.fetched_at).toLocaleString('en-IN'):''}</small>{!data?.complete&&<p>Showing {data?.available_days} available forecast days.</p>}</>}
 </section>
}

