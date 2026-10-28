import {useState} from 'react';
import {MapPin,X} from 'lucide-react';
import {api} from '../api/client';
import {useApi} from '../hooks/useApi';
import type {AdminProfile,Pin} from '../types/municipal';
import type {CivicNotice} from '../types/civic';
export default function LocalContext({city,pin,onPin,revision}:{city:string;pin:string;onPin:(pin:string)=>void;profile?:AdminProfile|null;revision:number}){
 const local=useApi(()=>api<{notices:CivicNotice[]}>('municipal/local/'+city+(pin?'?pincode='+pin:'')),[city,pin,revision]);
 const registry=useApi(()=>api<{records:Pin[]}>('municipal/pincodes/'+city),[city]);
 const [dismissed,setDismissed]=useState('');
 const notice=[...(local.data?.notices??[])].sort((a,b)=>new Date(b.created??b.valid_from).getTime()-new Date(a.created??a.valid_from).getTime())[0];
 if(!notice||dismissed===notice.id)return null;
 const name=registry.data?.records.find(p=>p.pincode===(notice.pincode??pin))?.locality_name??notice.area;
 return <aside className="local-notification" aria-label="Local PIN notification"><MapPin aria-hidden="true"/><div className="notification-content"><span className="locality-chip">{name.split(',')[0]}{(notice.pincode??pin)&&' · '+(notice.pincode??pin)}</span><h2>{notice.headline}</h2><p title={notice.description}>{notice.description}</p><time dateTime={notice.created??notice.valid_from}>{new Date(notice.created??notice.valid_from).toLocaleString('en-IN')}</time><label className="notice-pin">Locality<select aria-label="Notification locality" value={pin} onChange={e=>onPin(e.target.value)}><option value="">Citywide</option>{registry.data?.records.map(p=><option key={p.pincode} value={p.pincode}>{p.pincode} · {p.locality_name.split(',')[0]}</option>)}</select></label></div><button className="dismiss-notice" aria-label="Dismiss local notification" onClick={()=>setDismissed(notice.id)}><X/></button></aside>
}
