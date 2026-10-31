import AccountMenu from './components/AccountMenu';
import GuestProfile from './components/GuestProfile';
import CivilianProfile from './pages/CivilianProfile';
import {useCivilian,CivilianLogin} from './components/CivilianSession';
import {useEffect,useState,useRef} from 'react';
import {Activity,Sun,Moon,ArrowUpRight,RefreshCw,X,ShieldCheck} from 'lucide-react';
import {api} from './api/client';
import {getModels} from './api/models';
import {getObservations} from './api/observations';
import {getScenarios,getComplaints,getFeedback} from './api/operations';
import {useApi} from './hooks/useApi';
import CitySelector from './components/CitySelector';
import Dashboard from './pages/Dashboard';
import MonetaryHistory from './pages/MonetaryHistory';
import LocalArea,{cancelLocationRequest} from './components/LocalArea';
import {OpenDataOverview,DataSources} from './components/OpenData';
import './open-data.css';
import Predictions from './pages/Predictions';
import Infrastructure from './pages/Infrastructure';
import NotificationBell from './components/NotificationBell';
import Planning from './pages/Planning';
import Decisions from './pages/Decisions';
import AdminWelcome from './components/AdminWelcome';
import AdminShell from './components/AdminShell';
import AdminOverview from './pages/AdminOverview';
import LocalContext from './components/LocalContext';
import ProductTour from './tour/ProductTour';
import type {AdminProfile} from './types/municipal';
import CityMap from './pages/CityMap';
import ReportProblem from './pages/ReportProblem';
import OpenReports from './pages/OpenReports';
import ReviewReports from './pages/ReviewReports';
import type {Weather,CivicContext,CivicReport} from './types/civic';
import ModelValidation from './pages/ModelValidation';
import type {City,Graph,ScenarioInput,Scenario,Audit} from './types/api';


export default function App(){
  const keyboardReveal=useRef(false);
  const hoverTimer=useRef<ReturnType<typeof setTimeout>|null>(null);
  const revealHeader=()=>{if(hoverTimer.current)clearTimeout(hoverTimer.current);setHeaderHover(true)};
  const hideHeader=()=>{if(hoverTimer.current)clearTimeout(hoverTimer.current);hoverTimer.current=setTimeout(()=>{if(!publicHeader.current?.contains(document.activeElement))setHeaderHover(false)},220)};
  useEffect(()=>()=>{if(hoverTimer.current)clearTimeout(hoverTimer.current)},[]);
  const [headerHover,setHeaderHover]=useState(false),[compact,setCompact]=useState(matchMedia('(max-width:760px)').matches);
  useEffect(()=>{const media=matchMedia('(max-width:760px)');const update=()=>setCompact(media.matches);media.addEventListener('change',update);return()=>media.removeEventListener('change',update)},[]);
  const [page,setPage]=useState(location.pathname==='/data-sources'?'Data and sources':/^\/(?:admin\/)?(?:infrastructure|city-infra)\/?$/.test(location.pathname)?'City infra':'Overview'),[city,setCity]=useState('delhi');
  const [dark,setDark]=useState(localStorage.getItem('civicflux-theme')==='dark');
  const [admin,setAdmin]=useState(false),[login,setLogin]=useState(location.pathname==='/admin/login'),[mobileNav,setMobileNav]=useState(false);
  useEffect(()=>{const key=(e:KeyboardEvent)=>{if(e.key==='Escape')setMobileNav(false)};const outside=(e:PointerEvent)=>{if(!publicHeader.current?.contains(e.target as Node))setMobileNav(false)};window.addEventListener('keydown',key);window.addEventListener('pointerdown',outside);return()=>{window.removeEventListener('keydown',key);window.removeEventListener('pointerdown',outside)}},[]);
  const [preparedResources,setPreparedResources]=useState<ScenarioInput['resources']|null>(null);
  const [sessionReady,setSessionReady]=useState(false);
  const civilian=useCivilian(sessionReady&&!admin&&!login&&!location.pathname.startsWith('/admin'));
  const [profile,setProfile]=useState<AdminProfile|null>(null),[pin,setPin]=useState('');
  const navigation=admin?['Overview','Planning','Decisions','City map','City infra','Predictions','Review reports','Monetary history']:['Overview','City map','Predictions','Report a problem','Monetary history'];
  const [username,setUsername]=useState('admin'),[password,setPassword]=useState(''),[loginError,setLoginError]=useState(''),[logging,setLogging]=useState(false);
  const [revision,setRevision]=useState(0),[chosen,setChosen]=useState<Scenario|null>(null),[scrolled,setScrolled]=useState(false),[sessionError,setSessionError]=useState('');
  const modal=useRef<HTMLElement>(null);
  const publicHeader=useRef<HTMLElement>(null),[headerHeight,setHeaderHeight]=useState(160);
  useEffect(()=>{if(headerHover&&keyboardReveal.current){keyboardReveal.current=false;publicHeader.current?.querySelector<HTMLElement>('a')?.focus({preventScroll:true})}},[headerHover]);
  useEffect(()=>{if(admin||!sessionReady||!publicHeader.current)return;const node=publicHeader.current;const measure=()=>setHeaderHeight(node.getBoundingClientRect().height);const observer=new ResizeObserver(measure);observer.observe(node);measure();return()=>observer.disconnect()},[admin,sessionReady]);
  const cities=useApi(()=>api<City[]>('cities'),[admin,revision],{keepPreviousData:true});
  const models=useApi(getModels,[revision],{keepPreviousData:true});
  const observations=useApi(()=>getObservations(city),[city,revision,admin,pin]);
  const scenarios=useApi(()=>admin?getScenarios():Promise.resolve([]),[admin,revision],{keepPreviousData:true});
  const graph=useApi(()=>admin?api<Graph>('scenarios/graph'):Promise.resolve(null),[admin]);
  const defaults=useApi(()=>admin?api<ScenarioInput>('scenarios/defaults'):Promise.resolve(null),[admin]);
  const complaints=useApi(()=>api<CivicReport[]>('civic/reports?city_id='+city),[city,revision,admin,pin]);
  const weather=useApi(()=>api<Weather>('civic/weather/'+city),[city,revision,admin,pin]);
  const civic=useApi(()=>api<CivicContext>('civic/context/'+city),[city,revision,admin,pin]);
  const feedback=useApi(()=>admin?getFeedback():Promise.resolve({reviews:[],verifications:[]}),[admin,revision],{keepPreviousData:true});
  const audit=useApi(()=>admin&&profile?.role==='system_supervisor'?api<Audit[]>('audit'):Promise.resolve([]),[admin,profile?.role,revision]);
  const activeCity=cities.data?.find(c=>c.id===city);
  const currentObservations=observations.data?.city_id===city?observations.data:null;
  const currentWeather=weather.data?.city_id===city?weather.data:null;
  const currentCivic=civic.data?.city_id===city?{...civic.data,notices:civic.data.notices.filter(n=>!n.pincode||n.pincode===pin),operational_pools:civic.data.operational_pools?.filter(p=>!pin||!p.pincode||p.pincode===pin)}:null;
  const localReports=(complaints.data??[]).filter(r=>r.city_id===city&&(!pin||r.postal_code===pin));
  const localScenarios=scenarios.data?.filter(s=>s.city_id===city&&(!pin||s.inputs.pincode===pin))??[];
  const scenario=localScenarios.find(s=>s.id===chosen?.id)??localScenarios[0]??null;
  const refresh=()=>setRevision(n=>n+1);
  const navigate=(value:string)=>{setPage(value);setMobileNav(false)};
  useEffect(()=>{window.scrollTo(0,0)},[page]);
  useEffect(()=>{if(!sessionReady)return;if(!admin&&page==='City infra'){setPage('Overview');setLogin(true);history.replaceState({},'', '/admin/login')}if(!admin&&['Planning','Decisions','Review reports'].includes(page))setPage('Overview');if(admin&&page==='Report a problem')setPage('Review reports')},[admin,page,sessionReady]);
  useEffect(()=>{const expired=()=>{if(!admin){setRevision(n=>n+1);return}setAdmin(false);setProfile(null);setChosen(null);setPreparedResources(null);setSessionError('Your admin session expired. Sign in again to continue.');setLogin(true)};window.addEventListener('civicflux-session-expired',expired);return()=>window.removeEventListener('civicflux-session-expired',expired)},[admin]);
  useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light';localStorage.setItem('civicflux-theme',dark?'dark':'light')},[dark]);
  useEffect(()=>{api<{profile:AdminProfile}>('auth/me').then(session=>{setProfile(session.profile);const first=session.profile.assignments[0];if(first){setCity(first.city_id);setPin(first.pincode)}else if(session.profile.role!=='system_supervisor'&&session.profile.cities.length){setCity(session.profile.cities[0]);setPin('')}setAdmin(true)}).catch(()=>setAdmin(false)).finally(()=>setSessionReady(true));const timer=setInterval(refresh,60000);return()=>clearInterval(timer)},[]);
  useEffect(()=>{const update=()=>setScrolled(window.scrollY>80);window.addEventListener('scroll',update,{passive:true});update();return()=>window.removeEventListener('scroll',update)},[]);
  useEffect(()=>{if(!login)return;const before=document.activeElement as HTMLElement;const handle=(e:KeyboardEvent)=>{if(e.key==='Escape')closeAdminLogin();if(e.key==='Tab'){const items=modal.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input');if(!items?.length)return;const first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};document.addEventListener('keydown',handle);return()=>{document.removeEventListener('keydown',handle);before?.focus()}},[login]);
  useEffect(()=>{const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible');observer.unobserve(e.target)}}),{threshold:.06});document.querySelectorAll('.panel').forEach(el=>{el.classList.add('reveal');observer.observe(el)});return()=>observer.disconnect()},[page,models.data,scenarios.data,graph.data,complaints.data]);
  async function authenticate(e:React.FormEvent){e.preventDefault();setLogging(true);setLoginError('');try{const session=await api<{profile:AdminProfile}>('auth/login',{username,password});cancelLocationRequest();setProfile(session.profile);const first=session.profile.assignments[0];if(first){setCity(first.city_id);setPin(first.pincode)}else if(session.profile.role!=='system_supervisor'&&session.profile.cities.length){setCity(session.profile.cities[0]);setPin('')}setAdmin(true);setPage('Overview');history.replaceState({},'', '/admin');setLogin(false);setSessionError('');setPassword('');refresh()}catch(e){setLoginError((e as Error).message)}finally{setLogging(false)}}
  function closeAdminLogin(){setLogin(false);if(!admin)history.replaceState({},'', '/')}
  async function portal(){if(!admin){setLoginError('');history.pushState({},'', '/admin/login');setLogin(true);return}try{await api('auth/logout',{});setAdmin(false);setProfile(null);setPin('');setChosen(null);setPreparedResources(null);setPage('Overview');history.replaceState({},'', '/');refresh()}catch(e){setSessionError((e as Error).message)}}
  const errors=[cities.error,models.error,observations.error,scenarios.error,graph.error,defaults.error,complaints.error,weather.error,civic.error,feedback.error,audit.error,sessionError].filter(Boolean);
  const areaPicker=!admin&&civilian.ready&&!civilian.open?<LocalArea city={city} pin={pin} onArea={(nextCity,nextPin)=>{setCity(nextCity);setPin(nextPin);setChosen(null);setPreparedResources(null)}}/>:null;
  const content=<main>
        {page!=='Overview'&&areaPicker}
        {page!=='Overview'&&!admin&&<div className="page-heading"><div><span className="eyebrow">{activeCity?.name.toUpperCase()} / CIVICFLUX</span><h1>{page}<span>.</span></h1></div><button data-tour="refresh" className="refresh-button" onClick={refresh}><RefreshCw size={15}/>Refresh</button></div>}

        {errors.length>0&&<div className="error" role="alert">{admin?[...new Set(errors)].join(' · '):'Some information is unavailable. Try refreshing or check the source panels.'} <button onClick={()=>{setSessionError('');refresh()}}>Retry</button></div>}
        {models.loading&&!models.data&&page!=='Overview'&&<p className="loading" role="status">Loading research inventory…</p>}
        {page==='Overview'&&admin?<AdminOverview onRefresh={refresh} city={activeCity} observations={currentObservations} weather={currentWeather} context={currentCivic} reports={localReports} navigate={navigate}/>:page==='Overview'&&<Dashboard notice={<>{areaPicker}<LocalContext city={city} pin={pin} onPin={setPin} revision={revision}/></>}  models={models.data??[]} observations={currentObservations} city={activeCity} reports={localReports} weather={currentWeather} context={currentCivic} navigate={navigate} admin={admin}/>}
        {page==='Overview'&&city!=='delhi'&&<OpenDataOverview city={city} pin={pin} onPin={setPin} admin={admin}/>}
        {page==='Data and sources'&&<DataSources/>}
        {page==='Monetary history'&&<MonetaryHistory key={city+pin} city={city} pin={pin} admin={admin}/>}
        {page==='Predictions'&&activeCity&&<Predictions key={city+String(admin)} city={activeCity} models={(models.data??[]).filter(m=>m.component!=='infrastructure_anomaly')} admin={admin}/>}
        {page==='City infra'&&admin&&<Infrastructure key={city}/>}
        {page==='City map'&&<CityMap onRetry={refresh} admin={admin} pincode={pin} key={city} city={activeCity} observations={currentObservations} weather={currentWeather} context={currentCivic} reports={localReports}/>}
        {page==='Profile'&&!admin&&(civilian.user?<CivilianProfile key={civilian.user.id} user={civilian.user} onUser={civilian.setUser} onLogout={civilian.logout} city={activeCity} revision={revision}/>:<GuestProfile city={activeCity} revision={revision}/>)}
        {page==='Report a problem'&&!admin&&<ReportProblem user={civilian.user} key={city+pin+(civilian.user?.id??'guest')} initialPin={pin} city={activeCity} onSaved={refresh}/>}
        {page==='Open reports'&&<OpenReports key={city} reports={localReports}/>}
        {page==='Review reports'&&admin&&<ReviewReports key={city} supervisor={profile?.role==='system_supervisor'} pincode={pin} city={city} revision={revision} onSaved={refresh}/>}

        {page==='Planning'&&admin&&<Planning observations={currentObservations} resourceOverride={preparedResources} onUsePool={r=>{setPreparedResources(r);navigate('Decisions')}} pincode={pin} key={city+pin} defaults={defaults.data} scenario={scenario} city={activeCity} graph={graph.data} onRun={s=>{setChosen(s);refresh()}} context={currentCivic} weather={currentWeather} feedback={feedback.data??{reviews:[],verifications:[]}} onSaved={refresh} revision={revision} scenarios={localScenarios} onSelect={setChosen}/>}
        {page==='Decisions'&&admin&&<Decisions observations={currentObservations} resourceOverride={preparedResources} onUsePool={r=>{setPreparedResources(r);navigate('Decisions')}} pincode={pin} key={city+pin} defaults={defaults.data} scenario={scenario} city={activeCity} graph={graph.data} onRun={s=>{setChosen(s);refresh()}} context={currentCivic} weather={currentWeather} feedback={feedback.data??{reviews:[],verifications:[]}} onSaved={refresh} revision={revision} scenarios={localScenarios} onSelect={setChosen}/>}

        {page==='Model validation'&&<ModelValidation models={models.data??[]}/>}
        <footer><span className="footer-brand">CIVICFLUX</span>{!admin&&page==='Overview'&&<a className="footer-admin-login" href="/admin/login" onClick={e=>{e.preventDefault();void portal()}}>Admin Login</a>}{city!=='delhi'&&<a href="/data-sources" onClick={e=>{e.preventDefault();navigate('Data and sources')}}>Data and sources</a>}</footer>
      </main>;
  if(!sessionReady)return <div className="session-loading" role="status">Opening CivicFlux…</div>;
  const guide=<div hidden={!admin&&civilian.open} inert={!admin&&civilian.open}><ProductTour key={admin?profile?.id:civilian.user?.id??'public'} admin={admin} identity={admin?profile?.id??'admin':civilian.user?.id??'public'} supervisor={profile?.role==='system_supervisor'} city={city} pin={pin} page={page} civilian={!!civilian.user} suspended={!admin&&(civilian.open||!civilian.ready)} navigate={navigate}/></div>;
  if(admin&&profile)return <AdminWelcome key={profile.id}><><AdminShell dark={dark} onThemeChange={()=>setDark(!dark)} profile={profile} page={page} navigate={navigate} onSignOut={portal}>{content}</AdminShell>{guide}</></AdminWelcome>;
  return <div style={{'--public-header-height':headerHeight+'px'} as React.CSSProperties} className={'app-shell '+(page!=='Overview'?'interior-page ':'')+(mobileNav?'mobile-nav-open':'')}>
    <div className="main-shell" inert={civilian.open&&!login}>{page==='Overview'&&!scrolled&&!compact&&<button className="intro-hover-zone" aria-label="Show navigation" onPointerEnter={revealHeader} onPointerLeave={hideHeader} onFocus={()=>{keyboardReveal.current=true;revealHeader()}} onClick={revealHeader}/>}<header onPointerEnter={revealHeader} onPointerLeave={hideHeader} ref={publicHeader} inert={page==='Overview'&&!scrolled&&!headerHover&&!compact} className={'topbar civilian-topbar '+(scrolled||page!=='Overview'||headerHover||compact?'is-scrolled':'')}><div className="top-brand-row"><a className="navigation-brand" href="/" onClick={e=>{e.preventDefault();window.location.assign('/')}}><span className="brand-mark"><Activity size={23}/></span><span className="brand-civic">Civic</span><span className="brand-flux">Flux</span></a></div><div className="topbar-actions"><span className="mode-indicator"><i className="status-dot"/>{admin?'Admin workspace · '+(activeCity?.name??city)+(pin?' · PIN '+pin:profile?.role==='officer'?' · Choose an assigned PIN':' · Supervisor'):'Public access'}</span><CitySelector cities={(cities.data??[]).filter(c=>!admin||!profile||profile.role==='system_supervisor'||profile.cities.includes(c.id)||profile.assignments.some(a=>a.city_id===c.id))} value={city} onChange={v=>{cancelLocationRequest();setCity(v);setChosen(null);setPreparedResources(null);setPin(profile?.assignments.find(a=>a.city_id===v)?.pincode??'')}}/><NotificationBell key={city+pin} city={city} pin={pin} revision={revision}/><button data-tour="theme" className="icon-button" aria-label={dark?'Switch to light theme':'Switch to dark theme'} onClick={()=>setDark(!dark)}>{dark?<Sun size={17}/>:<Moon size={17}/>}</button><AccountMenu name={civilian.user?.name} secondary={civilian.user?'Civilian account':undefined} actions={civilian.user?[{label:'Profile',onSelect:()=>navigate('Profile')},{label:'Sign out',onSelect:()=>{void civilian.logout().catch(e=>setSessionError((e as Error).message))}}]:[{label:'Civilian Login',onSelect:()=>civilian.login()},{label:'Guest profile',onSelect:()=>navigate('Profile')}]} /></div><button data-tour="public-menu-toggle" className="public-menu-toggle icon-button" aria-label={mobileNav?'Close navigation':'Open navigation'} aria-expanded={mobileNav} aria-controls="public-navigation" onClick={()=>setMobileNav(!mobileNav)}><span className="hamburger-lines" aria-hidden="true"><span/><span/><span/></span></button><nav id="public-navigation" data-tour="public-nav" className="horizontal-navigation" aria-label="Main navigation">{navigation.map((title,i)=><button key={title} aria-current={page===title?'page':undefined} className={page===title?'nav-item active':'nav-item'} onClick={()=>navigate(title)}><span>{title}</span><small>{String(i+1).padStart(2,'0')}</small></button>)}</nav></header>
      {content}

    </div>
    {guide}
    {civilian.open&&!admin&&!login&&<CivilianLogin session={civilian}/>}
    {login&&<div className="modal-backdrop" onClick={e=>{if(e.target===e.currentTarget)closeAdminLogin()}}><section ref={modal} role="dialog" aria-modal="true" aria-labelledby="login-title" className="login-modal"><button className="close-button" aria-label="Close login" onClick={closeAdminLogin}><X size={20}/></button><span className="brand-mark"><ShieldCheck size={26}/></span><span className="eyebrow">THE HUMAN IN THE LOOP</span><h2 id="login-title">Your area.<br/><em>Your workspace.</em></h2><p>Use username admin and your area’s six-digit postal PIN. Your session is limited to that area.</p><form onSubmit={authenticate}><label>Admin ID<input autoFocus autoComplete="username" placeholder="admin" readOnly required value={username} onChange={e=>setUsername(e.target.value)}/></label><label>Password<input type="password" autoComplete="current-password" placeholder="Six-digit postal PIN" inputMode="numeric" pattern="[0-9]{6}" minLength={6} maxLength={6} required value={password} onChange={e=>setPassword(e.target.value)}/></label><button className="primary" disabled={logging}>{logging?'Signing in…':'Enter the admin portal'}<ArrowUpRight size={18}/></button>{loginError&&<div className="error" role="alert">{loginError}</div>}</form><small>Public analysis stays available without an account.</small></section></div>}
  </div>
}


