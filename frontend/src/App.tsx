import {useEffect,useState,useRef} from 'react';
import {Activity,LayoutDashboard,CloudRain,Network,GitBranch,SlidersHorizontal,ClipboardList,FlaskConical,Sun,Moon,LogIn,LogOut,ArrowUpRight,RefreshCw,X,Menu,ShieldCheck} from 'lucide-react';
import {api} from './api/client';
import {getModels} from './api/models';
import {getObservations} from './api/observations';
import {getScenarios,getComplaints,getFeedback} from './api/operations';
import {useApi} from './hooks/useApi';
import CitySelector from './components/CitySelector';
import Dashboard from './pages/Dashboard';
import Predictions from './pages/Predictions';
import Infrastructure from './pages/Infrastructure';
import Cascade from './pages/Cascade';
import Planning from './pages/Planning';
import Operations from './pages/Operations';
import ModelValidation from './pages/ModelValidation';
import type {City,Graph,ScenarioInput,Scenario,Audit} from './types/api';
const navigation=[['Overview',LayoutDashboard],['Predictions',CloudRain],['Infrastructure',Network],['Cascade analysis',GitBranch],['Planning',SlidersHorizontal],['Operations',ClipboardList],['Model validation',FlaskConical]] as const;

export default function App(){
  const [page,setPage]=useState('Overview'),[city,setCity]=useState('delhi');
  const [dark,setDark]=useState(localStorage.getItem('civicflux-theme')==='dark');
  const [admin,setAdmin]=useState(false),[login,setLogin]=useState(false),[mobileNav,setMobileNav]=useState(false);
  const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[loginError,setLoginError]=useState(''),[logging,setLogging]=useState(false);
  const [revision,setRevision]=useState(0),[chosen,setChosen]=useState<Scenario|null>(null),[scrolled,setScrolled]=useState(false),[sessionError,setSessionError]=useState('');
  const modal=useRef<HTMLElement>(null);
  const cities=useApi(()=>api<City[]>('cities'));
  const models=useApi(getModels,[revision],{keepPreviousData:true});
  const observations=useApi(()=>getObservations(city),[city,revision],{keepPreviousData:true});
  const scenarios=useApi(getScenarios,[revision],{keepPreviousData:true});
  const graph=useApi(()=>api<Graph>('scenarios/graph'));
  const defaults=useApi(()=>api<ScenarioInput>('scenarios/defaults'));
  const complaints=useApi(getComplaints,[revision],{keepPreviousData:true});
  const feedback=useApi(getFeedback,[revision],{keepPreviousData:true});
  const audit=useApi(()=>admin?api<Audit[]>('audit'):Promise.resolve([]),[admin,revision]);
  const activeCity=cities.data?.find(c=>c.id===city);
  const currentObservations=observations.data?.city_id===city?observations.data:null;
  const localScenarios=scenarios.data?.filter(s=>s.city_id===city)??[];
  const scenario=(chosen?.city_id===city?localScenarios.find(s=>s.id===chosen.id)??chosen:null)??localScenarios[0]??null;
  const refresh=()=>setRevision(n=>n+1);
  const navigate=(value:string)=>{setPage(value);setMobileNav(false)};
  useEffect(()=>{window.scrollTo(0,0)},[page]);
  useEffect(()=>{const expired=()=>{setAdmin(false);setSessionError('Your admin session expired. Sign in again to continue.');setLogin(true)};window.addEventListener('civicflux-session-expired',expired);return()=>window.removeEventListener('civicflux-session-expired',expired)},[]);
  useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light';localStorage.setItem('civicflux-theme',dark?'dark':'light')},[dark]);
  useEffect(()=>{api('auth/me').then(()=>setAdmin(true)).catch(()=>setAdmin(false));const timer=setInterval(refresh,60000);return()=>clearInterval(timer)},[]);
  useEffect(()=>{const update=()=>setScrolled(window.scrollY>45);window.addEventListener('scroll',update,{passive:true});return()=>window.removeEventListener('scroll',update)},[]);
  useEffect(()=>{if(!login)return;const before=document.activeElement as HTMLElement;const handle=(e:KeyboardEvent)=>{if(e.key==='Escape')setLogin(false);if(e.key==='Tab'){const items=modal.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input');if(!items?.length)return;const first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};document.addEventListener('keydown',handle);return()=>{document.removeEventListener('keydown',handle);before?.focus()}},[login]);
  useEffect(()=>{const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');observer.unobserve(e.target)}}),{threshold:.06});document.querySelectorAll('.panel').forEach(el=>{el.classList.add('reveal');observer.observe(el)});return()=>observer.disconnect()},[page,models.data,scenarios.data,graph.data,complaints.data]);
  async function authenticate(e:React.FormEvent){e.preventDefault();setLogging(true);setLoginError('');try{await api('auth/login',{username,password});setAdmin(true);setLogin(false);setSessionError('');setPassword('');refresh()}catch(e){setLoginError((e as Error).message)}finally{setLogging(false)}}
  async function portal(){if(!admin){setLoginError('');setLogin(true);return}try{await api('auth/logout',{});setAdmin(false);refresh()}catch(e){setSessionError((e as Error).message)}}
  const errors=[cities.error,models.error,observations.error,scenarios.error,graph.error,defaults.error,complaints.error,feedback.error,audit.error,sessionError].filter(Boolean);
  return <div className={'app-shell '+(mobileNav?'mobile-nav-open':'')}>
    <div className="main-shell"><header className={'topbar '+(scrolled?'is-scrolled':'')}><div className="top-brand-row"><a className="navigation-brand" href="#overview" onClick={e=>{e.preventDefault();navigate('Overview')}}><span className="brand-mark"><Activity size={23}/></span>Civic<span>Flux</span></a><span className="nav-product">Urban intelligence</span></div><div className="topbar-actions"><span className="mode-indicator"><i className="status-dot"/>{admin?'Admin workspace':'Public access'}</span><CitySelector cities={cities.data??[]} value={city} onChange={v=>{setCity(v);setChosen(null)}}/><button className="icon-button" aria-label={dark?'Switch to light theme':'Switch to dark theme'} onClick={()=>setDark(!dark)}>{dark?<Sun size={17}/>:<Moon size={17}/>}</button><button className="portal-button" aria-label={admin?'Sign out':'Admin login'} onClick={portal}>{admin?<LogOut size={15}/>:<LogIn size={15}/>}<span>{admin?'Sign out':'Admin login'}</span></button></div><nav className="horizontal-navigation" aria-label="Main navigation">{navigation.map(([title,Icon],i)=><button key={title} aria-current={page===title?'page':undefined} className={page===title?'nav-item active':'nav-item'} onClick={()=>navigate(title)}><Icon size={16}/><span>{title}</span><small>{String(i+1).padStart(2,'0')}</small></button>)}</nav></header>
      <main>
        {page!=='Overview'&&<div className="page-heading"><div><span className="eyebrow">{activeCity?.name.toUpperCase()} / CIVICFLUX</span><h1>{page}<span>.</span></h1><p>{page==='Planning'?'Test the pressure. Understand the trade-offs. Keep people in control.':page==='Operations'?'Community voices, human decisions and a transparent record.':'Follow the evidence. Understand the connections.'}</p></div><button className="refresh-button" onClick={refresh}><RefreshCw size={15}/>Refresh</button></div>}
        {page!=='Overview'&&<div className="evidence-key"><span><i className="live-dot"/>Observations</span><span><i className="research-dot"/>Research forecasts</span><span><i className="sim-dot"/>Synthetic simulations</span></div>}
        {errors.length>0&&<div className="error" role="alert">{[...new Set(errors)].join(' · ')} <button onClick={()=>{setSessionError('');refresh()}}>Retry</button></div>}
        {models.loading&&!models.data&&page!=='Overview'&&<p className="loading" role="status">Loading research inventory…</p>}
        {page==='Overview'&&<Dashboard models={models.data??[]} observations={currentObservations} scenarios={localScenarios} city={activeCity} graph={graph.data} complaints={complaints.data??[]} navigate={navigate}/>}
        {page==='Predictions'&&<Predictions city={activeCity} models={models.data??[]} admin={admin}/>}
        {page==='Infrastructure'&&<Infrastructure graph={graph.data} city={activeCity?.name} scenario={scenario} observations={currentObservations}/>}
        {page==='Cascade analysis'&&<Cascade graph={graph.data} scenario={scenario}/>}
        {(page==='Planning'||page==='Operations'||page==='Cascade analysis')&&localScenarios.length>0&&<label className="scenario-picker">Saved scenario<select value={scenario?.id??''} onChange={e=>setChosen(localScenarios.find(s=>s.id===e.target.value)??null)}>{localScenarios.map(s=><option value={s.id} key={s.id}>{s.name} · {new Date(s.created).toLocaleString('en-IN')}</option>)}</select></label>}
        {page==='Planning'&&<Planning defaults={defaults.data} scenario={scenario} admin={admin} city={city} graph={graph.data} onRun={s=>{setChosen(s);refresh()}}/>}
        {page==='Operations'&&<Operations scenario={scenario} feedback={feedback.data??{reviews:[],verifications:[]}} complaints={complaints.data??[]} admin={admin} city={city} audit={audit.data??[]} onSaved={refresh}/>}
        {page==='Model validation'&&<ModelValidation models={models.data??[]}/>}
        <footer><span className="footer-brand">CIVICFLUX</span><span>Urban resilience · Sustainability · Governance</span><span><ShieldCheck size={13}/> Research only · No automatic dispatch</span></footer>
      </main>
    </div>
    {login&&<div className="modal-backdrop" onClick={e=>{if(e.target===e.currentTarget)setLogin(false)}}><section ref={modal} role="dialog" aria-modal="true" aria-labelledby="login-title" className="login-modal"><button className="close-button" aria-label="Close login" onClick={()=>setLogin(false)}><X size={20}/></button><span className="brand-mark"><ShieldCheck size={26}/></span><span className="eyebrow">THE HUMAN IN THE LOOP</span><h2 id="login-title">Your city.<br/><em>Your judgement.</em></h2><p>Sign in to adjust scenario assumptions, review proposals and respond to community reports.</p><form onSubmit={authenticate}><label>Admin ID<input autoFocus autoComplete="username" placeholder="Enter admin ID" required value={username} onChange={e=>setUsername(e.target.value)}/></label><label>Password<input type="password" autoComplete="current-password" placeholder="Enter password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button className="primary" disabled={logging}>{logging?'Signing in…':'Enter the admin portal'}<ArrowUpRight size={18}/></button>{loginError&&<div className="error" role="alert">{loginError}</div>}</form><small>Public analysis stays available without an account.</small></section></div>}
  </div>
}


