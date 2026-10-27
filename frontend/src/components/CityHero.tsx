import {lazy,Suspense,useEffect,useRef,useState} from 'react';
import {ArrowDown,ArrowUpRight,Radio,Network,ShieldCheck} from 'lucide-react';
import type {HeroMotion} from './FluxScene';
const FluxScene=lazy(()=>import('./FluxScene'));
const chapters=[{tag:'01 / Sense',title:'Every connection.',em:'Changes everything.',copy:'A living view of your city. From environmental signals to the systems that keep life moving.'},{tag:'02 / Understand',title:'See the ripple.',em:'Before the impact.',copy:'Explore infrastructure dependencies, test scenarios and understand where action matters.'},{tag:'03 / Act',title:'Intelligence.',em:'Human at the centre.',copy:'Turn connected evidence into clear priorities. Every intervention starts with human judgement.'}];
export default function CityHero({ready,total,onExplore}:{ready:number;total:number;onExplore:()=>void}){
 const section=useRef<HTMLElement>(null),motion=useRef<HeroMotion>({progress:0,x:0,y:0}),[chapter,setChapter]=useState(0);
 useEffect(()=>{
  const media=matchMedia('(prefers-reduced-motion: reduce)');let frame=0;
  const update=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{const element=section.current;if(!element)return;const rect=element.getBoundingClientRect(),p=Math.max(0,Math.min(1,-rect.top/Math.max(1,rect.height-innerHeight+125)));motion.current.progress=media.matches?0:p;element.style.setProperty('--journey',String(p));setChapter(p>.66?2:p>.3?1:0);})};
  addEventListener('scroll',update,{passive:true});addEventListener('resize',update);update();return()=>{cancelAnimationFrame(frame);removeEventListener('scroll',update);removeEventListener('resize',update)};
 },[]);
 const enter=()=>document.getElementById('city-dashboard')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
 return <section ref={section} className="orbital-hero" onPointerMove={e=>{if(e.pointerType==='touch'||matchMedia('(prefers-reduced-motion: reduce)').matches)return;const rect=e.currentTarget.getBoundingClientRect();motion.current.x=(e.clientX-rect.left)/rect.width*2-1;motion.current.y=(e.clientY%innerHeight)/innerHeight*2-1;section.current?.style.setProperty('--cursor-x',motion.current.x+'');section.current?.style.setProperty('--cursor-y',motion.current.y+'')}} onPointerLeave={()=>{motion.current.x=0;motion.current.y=0;section.current?.style.setProperty('--cursor-x','0');section.current?.style.setProperty('--cursor-y','0')}}>
  <div className="journey-stage"><div className="journey-grid"/><div className="journey-glow"/>
   <div className="orbital-visual"><Suspense fallback={<div className="fallback-orb"><i/><i/><i/></div>}><FluxScene motion={motion}/></Suspense><div className="orbital-caption">The connected city / A visual exploration</div></div>
   <div className="journey-copy" key={chapter}><span className="eyebrow"><i className="status-dot"/>CivicFlux / {chapters[chapter].tag}</span><h1>{chapters[chapter].title}<br/><em>{chapters[chapter].em}</em></h1><p>{chapters[chapter].copy}</p><div className="journey-actions"><button className="primary" onClick={enter}>Explore your city <ArrowDown size={16}/></button><button className="journey-link" onClick={onExplore}>Meet the models <ArrowUpRight size={16}/></button></div></div>
   <div className="orbital-label label-weather"><Radio size={18}/><div><strong>Sense the city</strong><small>Weather & air quality</small></div><span className="signal-bars"><i/><i/><i/><i/></span></div>
   <div className="orbital-label label-network"><Network size={18}/><div><strong>Connect the systems</strong><small>Infrastructure & dependencies</small></div></div>
   <div className="orbital-label label-human"><ShieldCheck size={18}/><div><strong>Keep people in control</strong><small>Review. Decide. Respond.</small></div></div>
   <div className="journey-footer"><span>{total?<><b>{String(ready).padStart(2,'0')}</b> connected model components</>:'Connecting the model suite…'}</span><div className="journey-chapters">{chapters.map((c,i)=><span key={i} className={chapter===i?'current':''}>{c.tag}<i/></span>)}</div><button onClick={enter}>Scroll to discover <ArrowDown size={14}/></button></div>
  </div>
 </section>
}
