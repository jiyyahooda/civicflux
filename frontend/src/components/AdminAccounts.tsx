import {useState} from 'react';
import {api} from '../api/client';
import {useApi} from '../hooks/useApi';
type Area={id:string;username:string;pincode:string;area_name:string;is_active:number;last_login_at:string|null};
export default function AdminAccounts({onSaved}:{onSaved:()=>void}){
 const areas=useApi(()=>api<Area[]>('municipal/administrators'));const [message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 async function deactivate(area:Area){setBusy(true);try{await api('municipal/administrators',{pincode:area.pincode,is_active:false});setMessage('Area deactivated. This session is now closed.');onSaved();window.dispatchEvent(new Event('civicflux-session-expired'))}catch(e){setMessage((e as Error).message)}finally{setBusy(false)}}
 return <details className="panel"><summary>Administrator assignments</summary><p>One account per postal area. Username: admin. The area's six-digit postal PIN is its login password.</p>{areas.data?.map(area=><article key={area.id}><h3>{area.area_name.split(',')[0]}</h3><p>{area.pincode} · {area.is_active?'Active':'Inactive'}</p><button disabled={busy||!area.is_active} onClick={()=>deactivate(area)}>Deactivate this area and sign out</button></article>)}<p>Other areas are managed through the server's seed/area management script; this portal cannot change another area's access.</p><p role="status">{message||areas.error}</p></details>
}
