import {useEffect,useState} from 'react';
import type {ReactNode} from 'react';
import {Activity} from 'lucide-react';
export default function AdminWelcome({children}:{children:ReactNode}){
 const [welcoming,setWelcoming]=useState(true);
 useEffect(()=>{const timer=window.setTimeout(()=>setWelcoming(false),5000);return()=>window.clearTimeout(timer)},[]);
 if(!welcoming)return <>{children}</>;
 return <div className="admin-shell admin-welcome-shell"><section className="admin-welcome" role="status" aria-live="polite" aria-busy="true"><span className="welcome-brand"><Activity size={30} aria-hidden="true"/></span><span className="admin-eyebrow">CivicFlux · Municipal workspace</span><h1>Welcome, admin</h1><p>Loading your workspace…</p><div className="welcome-progress" aria-hidden="true"><span/></div></section></div>
}
