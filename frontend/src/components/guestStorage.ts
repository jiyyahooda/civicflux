const KEY='civicflux-prototype-guest';
export function loadGuestState():any{try{const v=JSON.parse(localStorage.getItem(KEY)??'{}');return v&&typeof v==='object'&&!Array.isArray(v)?v:{}}catch{return {}}}
function write(v:unknown){localStorage.setItem(KEY,JSON.stringify(v))}
export function rememberGuestReport(id:string){try{const s=loadGuestState();s.reports=[id,...(Array.isArray(s.reports)?s.reports:[]).filter((v:string)=>v!==id)].slice(0,50);write(s)}catch{}}
export async function guestApi<T>(path:string,body?:any,method?:string):Promise<T>{
 const s=loadGuestState();let result:unknown;
 if(path==='profile'){s.profile=body;write(s);result={...body,id:'guest',phone:''}}
 else if(path==='reports'){
 const ids=(Array.isArray(s.reports)?s.reports:[]).filter((id:unknown)=>typeof id==='string'&&/^[a-f0-9-]{36}$/i.test(id)).slice(0,50);
 result=(await Promise.all(ids.map(async(id:string)=>{try{const r=await fetch('/api/civic/reports/'+encodeURIComponent(id));return r.ok?await r.json():null}catch{return null}}))).filter(Boolean)
 }else if(path==='saved'&&body){const list=Array.isArray(s.saved)?s.saved:[];if(list.length>=50)throw new Error('Keep up to 50 guest places and routes.');result={...body,id:crypto.randomUUID()};s.saved=[result,...list];write(s)}
 else if(path==='saved')result=Array.isArray(s.saved)?s.saved:[];
 else if(path.startsWith('saved/')&&method==='DELETE'){s.saved=(Array.isArray(s.saved)?s.saved:[]).filter((v:{id:string})=>v.id!==path.slice(6));write(s);result={ok:true}}
 else throw new Error('This guest operation is unavailable.');
 return result as T;
}
