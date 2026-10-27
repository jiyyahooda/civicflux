import {useEffect,useState,useRef} from 'react';
import {Activity,Sun,Moon,LogIn,LogOut,ArrowUpRight,RefreshCw,X,Menu,ShieldCheck} from 'lucide-react';
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
import CityMap from './pages/CityMap';
import ReportProblem from './pages/ReportProblem';
import OpenReports from './pages/OpenReports';
import ReviewReports from './pages/ReviewReports';
import type {Weather,CivicContext,CivicReport} from './types/civic';
import ModelValidation from './pages/ModelValidation';
import type {City,Graph,ScenarioInput,Scenario,Audit} from './types/api';


export default function App(){
  const [page,setPage]=useState('Overview'),[city,setCity]=useState('delhi');
  const [dark,setDark]=useState(localStorage.getItem('civicflux-theme')==='dark');
  const [admin,setAdmin]=useState(false),[login,setLogin]=useState(false),[mobileNav,setMobileNav]=useState(false);
  const navigation=['Overview','City map','Infrastructure','Predictions','Report a problem',...(admin?['Review reports','Planning']:[])];
  const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[loginError,setLoginError]=useState(''),[logging,setLogging]=useState(false);
  const [revision,setRevision]=useState(0),[chosen,setChosen]=useState<Scenario|null>(null),[scrolled,setScrolled]=useState(false),[sessionError,setSessionError]=useState('');
  const modal=useRef<HTMLElement>(null);
  const cities=useApi(()=>api<City[]>('cities'));
  const models=useApi(getModels,[revision],{keepPreviousData:true});
  const observations=useApi(()=>getObservations(city),[city,revision],{keepPreviousData:true});
  const scenarios=useApi(()=>admin?getScenarios():Promise.resolve([]),[admin,revision],{keepPreviousData:true});
  const graph=useApi(()=>admin?api<Graph>('scenarios/graph'):Promise.resolve(null),[admin]);
  const defaults=useApi(()=>admin?api<ScenarioInput>('scenarios/defaults'):Promise.resolve(null),[admin]);
  const complaints=useApi(()=>api<CivicReport[]>('civic/reports?city_id='+city),[city,revision]);
  const weather=useApi(()=>api<Weather>('civic/weather/'+city),[city,revision]);
  const civic=useApi(()=>api<CivicContext>('civic/context/'+city),[city,revision]);
  const feedback=useApi(()=>admin?getFeedback():Promise.resolve({reviews:[],verifications:[]}),[admin,revision],{keepPreviousData:true});
  const audit=useApi(()=>admin?api<Audit[]>('audit'):Promise.resolve([]),[admin,revision]);
  const activeCity=cities.data?.find(c=>c.id===city);
  const currentObservations=observations.data?.city_id===city?observations.data:null;
  const currentWeather=weather.data?.city_id===city?weather.data:null;
  const currentCivic=civic.data?.city_id===city?civic.data:null;
  const localReports=(complaints.data??[]).filter(r=>r.city_id===city);
  const localScenarios=scenarios.data?.filter(s=>s.city_id===city)??[];
  const scenario=(chosen?.city_id===city?localScenarios.find(s=>s.id===chosen.id)??chosen:null)??localScenarios[0]??null;
  const refresh=()=>setRevision(n=>n+1);
  const navigate=(value:string)=>{setPage(value);setMobileNav(false)};
  useEffect(()=>{window.scrollTo(0,0)},[page]);
  useEffect(()=>{if(!admin&&['Planning','Review reports'].includes(page))setPage('Overview')},[admin,page]);
  useEffect(()=>{const expired=()=>{setAdmin(false);setSessionError('Your admin session expired. Sign in again to continue.');setLogin(true)};window.addEventListener('civicflux-session-expired',expired);return()=>window.removeEventListener('civicflux-session-expired',expired)},[]);
  useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light';localStorage.setItem('civicflux-theme',dark?'dark':'light')},[dark]);
  useEffect(()=>{api('auth/me').then(()=>setAdmin(true)).catch(()=>setAdmin(false));const timer=setInterval(refresh,60000);return()=>clearInterval(timer)},[]);
  useEffect(()=>{const update=()=>setScrolled(window.scrollY>45);window.addEventListener('scroll',update,{passive:true});return()=>window.removeEventListener('scroll',update)},[]);
  useEffect(()=>{if(!login)return;const before=document.activeElement as HTMLElement;const handle=(e:KeyboardEvent)=>{if(e.key==='Escape')setLogin(false);if(e.key==='Tab'){const items=modal.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input');if(!items?.length)return;const first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};document.addEventListener('keydown',handle);return()=>{document.removeEventListener('keydown',handle);before?.focus()}},[login]);
  useEffect(()=>{const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');observer.unobserve(e.target)}}),{threshold:.06});document.querySelectorAll('.panel').forEach(el=>{el.classList.add('reveal');observer.observe(el)});return()=>observer.disconnect()},[page,models.data,scenarios.data,graph.data,complaints.data]);
  async function authenticate(e:React.FormEvent){e.preventDefault();setLogging(true);setLoginError('');try{await api('auth/login',{username,password});setAdmin(true);setLogin(false);setSessionError('');setPassword('');refresh()}catch(e){setLoginError((e as Error).message)}finally{setLogging(false)}}
  async function portal(){if(!admin){setLoginError('');setLogin(true);return}try{await api('auth/logout',{});setAdmin(false);refresh()}catch(e){setSessionError((e as Error).message)}}
  const errors=[cities.error,models.error,observations.error,scenarios.error,graph.error,defaults.error,complaints.error,weather.error,civic.error,feedback.error,audit.error,sessionError].filter(Boolean);
  return <div className={'app-shell '+(mobileNav?'mobile-nav-open':'')}>
    <div className="main-shell"><header className={'topbar '+(scrolled?'is-scrolled':'')}><div className="top-brand-row"><a className="navigation-brand" href="#overview" onClick={e=>{e.preventDefault();navigate('Overview')}}><span className="brand-mark"><Activity size={23}/></span><span className="brand-civic">Civic</span><span className="brand-flux">Flux</span></a></div><div className="topbar-actions"><span className="mode-indicator"><i className="status-dot"/>{admin?'Admin workspace':'Public access'}</span><CitySelector cities={cities.data??[]} value={city} onChange={v=>{setCity(v);setChosen(null)}}/><button className="icon-button" aria-label={dark?'Switch to light theme':'Switch to dark theme'} onClick={()=>setDark(!dark)}>{dark?<Sun size={17}/>:<Moon size={17}/>}</button><button className="portal-button" aria-label={admin?'Sign out':'Admin login'} onClick={portal}>{admin?<LogOut size={15}/>:<LogIn size={15}/>}<span>{admin?'Sign out':'Admin login'}</span></button></div><nav className="horizontal-navigation" aria-label="Main navigation">{navigation.map((title,i)=><button key={title} aria-current={page===title?'page':undefined} className={page===title?'nav-item active':'nav-item'} onClick={()=>navigate(title)}><span>{title}</span><small>{String(i+1).padStart(2,'0')}</small></button>)}</nav></header>
      <main>
        {page!=='Overview'&&<div className="page-heading"><div><span className="eyebrow">{activeCity?.name.toUpperCase()} / CIVICFLUX</span><h1>{page}<span>.</span></h1></div><button className="refresh-button" onClick={refresh}><RefreshCw size={15}/>Refresh</button></div>}

        {errors.length>0&&<div className="error" role="alert">{admin?[...new Set(errors)].join(' · '):'Some information is unavailable. Try refreshing or check the source panels.'} <button onClick={()=>{setSessionError('');refresh()}}>Retry</button></div>}
        {models.loading&&!models.data&&page!=='Overview'&&<p className="loading" role="status">Loading research inventory…</p>}
        {page==='Overview'&&<Dashboard models={models.data??[]} observations={currentObservations} city={activeCity} reports={localReports} weather={currentWeather} context={currentCivic} navigate={navigate} admin={admin}/>}
        {page==='Predictions'&&<Predictions city={activeCity} models={models.data??[]} admin={admin}/>}
        {page==='Infrastructure'&&<Infrastructure city={activeCity} context={currentCivic} reports={localReports} observations={currentObservations} weather={currentWeather}/>}
        {page==='City map'&&<CityMap key={city} city={activeCity} observations={currentObservations} weather={currentWeather} context={currentCivic} reports={localReports}/>}
        {page==='Report a problem'&&<ReportProblem key={city} city={activeCity} onSaved={refresh}/>}
        {page==='Open reports'&&<OpenReports key={city} reports={localReports}/>}
        {page==='Review reports'&&admin&&<ReviewReports key={city} city={city} revision={revision} onSaved={refresh}/>}
        {page==='Cascade analysis'&&<Cascade graph={graph.data} scenario={scenario}/>}

        {page==='Planning'&&admin&&<Planning key={city} defaults={defaults.data} scenario={scenario} city={activeCity} graph={graph.data} onRun={s=>{setChosen(s);refresh()}} context={currentCivic} weather={currentWeather} feedback={feedback.data??{reviews:[],verifications:[]}} onSaved={refresh} revision={revision} scenarios={localScenarios} onSelect={setChosen}/>}

        {page==='Model validation'&&<ModelValidation models={models.data??[]}/>}
        <footer><span className="footer-brand">CIVICFLUX</span><span><ShieldCheck size={13}/> Human review · No automatic dispatch</span></footer>
      </main>
    </div>
    {login&&<div className="modal-backdrop" onClick={e=>{if(e.target===e.currentTarget)setLogin(false)}}><section ref={modal} role="dialog" aria-modal="true" aria-labelledby="login-title" className="login-modal"><button className="close-button" aria-label="Close login" onClick={()=>setLogin(false)}><X size={20}/></button><span className="brand-mark"><ShieldCheck size={26}/></span><span className="eyebrow">THE HUMAN IN THE LOOP</span><h2 id="login-title">Your city.<br/><em>Your judgement.</em></h2><p>Sign in to adjust scenario assumptions, review proposals and respond to community reports.</p><form onSubmit={authenticate}><label>Admin ID<input autoFocus autoComplete="username" placeholder="Enter admin ID" required value={username} onChange={e=>setUsername(e.target.value)}/></label><label>Password<input type="password" autoComplete="current-password" placeholder="Enter password" required value={password} onChange={e=>setPassword(e.target.value)}/></label><button className="primary" disabled={logging}>{logging?'Signing in…':'Enter the admin portal'}<ArrowUpRight size={18}/></button>{loginError&&<div className="error" role="alert">{loginError}</div>}</form><small>Public analysis stays available without an account.</small></section></div>}
  </div>
}


