import {useEffect,useRef,useState} from 'react';
export function useApi<T>(loader:()=>Promise<T>,deps:unknown[]=[],options:{keepPreviousData?:boolean}={}){
 const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[revision,setRevision]=useState(0);const ref=useRef(loader);ref.current=loader;
 useEffect(()=>{let current=true;setLoading(true);setError('');if(!options.keepPreviousData)setData(null);ref.current().then(value=>{if(current)setData(value)}).catch(e=>{if(current)setError(String(e.message))}).finally(()=>{if(current)setLoading(false)});return()=>{current=false}},[...deps,revision,options.keepPreviousData]);
 return {data,error,loading,reload:()=>setRevision(n=>n+1)};
}
