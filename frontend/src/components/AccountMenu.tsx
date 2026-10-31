import {useEffect,useId,useRef,useState} from 'react';
import {UserRound} from 'lucide-react';
type Action={label:string;onSelect:()=>void};
type Props={name?:string;secondary?:string;admin?:boolean;actions:Action[]};
/** Presentation only: callers retain the existing authenticated actions and routes. */
export default function AccountMenu({name,secondary,admin=false,actions}:Props){
 const [open,setOpen]=useState(false);const root=useRef<HTMLDivElement>(null),trigger=useRef<HTMLButtonElement>(null),menu=useRef<HTMLDivElement>(null);const id=useId();
 useEffect(()=>{if(!open)return;const outside=(e:PointerEvent)=>{if(!root.current?.contains(e.target as Node))setOpen(false)};document.addEventListener('pointerdown',outside);return()=>document.removeEventListener('pointerdown',outside)},[open]);
 useEffect(()=>{if(open)menu.current?.querySelector<HTMLButtonElement>('[role=menuitem]')?.focus()},[open]);
 function close(){setOpen(false);trigger.current?.focus()}
 return <div className="account-menu" data-tour="account-menu" ref={root} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget as Node))setOpen(false)}} onKeyDown={e=>{if(e.key==='Escape'&&open){e.preventDefault();e.stopPropagation();close()}if(!open)return;const buttons=Array.from(menu.current?.querySelectorAll<HTMLButtonElement>('[role=menuitem]')??[]);const index=buttons.indexOf(document.activeElement as HTMLButtonElement);let next:number|undefined;if(e.key==='ArrowDown')next=(index+1)%buttons.length;if(e.key==='ArrowUp')next=(index-1+buttons.length)%buttons.length;if(e.key==='Home')next=0;if(e.key==='End')next=buttons.length-1;if(next!==undefined){e.preventDefault();buttons[next]?.focus()}}}>
 <button ref={trigger} data-tour="account-trigger" className="account-avatar" aria-label={admin?'Administrator account':name?'Your account':'Account and login'} aria-haspopup="menu" aria-expanded={open} aria-controls={id} onClick={()=>setOpen(!open)} onKeyDown={e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();setOpen(true)}}}><UserRound size={18} aria-hidden="true"/></button>
 {open&&<div ref={menu} id={id} className="account-dropdown" role="menu" aria-label="Account menu">{name&&<div className="account-identity" role="presentation"><strong>{admin?'Administrator':name}</strong>{secondary&&<span>{secondary}</span>}</div>}{actions.map(action=><button type="button" role="menuitem" key={action.label} onClick={()=>{close();action.onSelect()}}>{action.label}</button>)}</div>}
 </div>;
}
