export async function api<T>(path:string,body?:unknown):Promise<T>{
 let response:Response;
 try{response=await fetch('/api/'+path,{credentials:'same-origin',...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});}
 catch{throw new Error('Cannot reach CivicFlux. Start the backend on port 8001 and frontend on port 5173 using the scripts in README.md, then retry.');}
 if(!response.ok){if(response.status===401&&!path.startsWith('auth/'))window.dispatchEvent(new Event('civicflux-session-expired'));const error=await response.json().catch(()=>({detail:'Server unavailable'}));throw new Error(typeof error.detail==='string'?error.detail:JSON.stringify(error.detail));}
 return response.json() as Promise<T>;
}
