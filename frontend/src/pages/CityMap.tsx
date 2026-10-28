import {useState} from 'react';
import AirQualityMap from '../components/AirQualityMap';
import ScenarioMap from '../components/ScenarioMap';
import StationMap,{type MapMode} from '../components/StationMap';
import GoogleTraffic from '../components/GoogleTraffic';
import RainfallChart from '../components/RainfallChart';
import {WeatherPanel} from '../components/CivicPanels';
import {api} from '../api/client';
import {useApi} from '../hooks/useApi';
import type {City,Observations} from '../types/api';
import type {Weather,CivicContext,CivicReport} from '../types/civic';
export default function CityMap({city,observations,weather,reports,admin=false}:{admin?:boolean;city:City|undefined;observations:Observations|null;weather:Weather|null;context:CivicContext|null;reports:CivicReport[]}){
 const [mode,setMode]=useState<MapMode>('all'),[view,setView]=useState('observations');const rain=useApi(()=>api<{precipitation_tiles_configured:boolean}>('maps/weather-configuration'));
 const modes:[MapMode,string][]=[['all','All conditions'],['rainfall','Rainfall'],['air','Air quality'],['traffic','Traffic'],['water','Water supply'],['infrastructure','Infrastructure alerts']];
 return <><div className="segmented map-modes" aria-label="Map mode">{modes.map(([id,label])=><button key={id} aria-pressed={mode===id} className={mode===id?'selected':''} onClick={()=>{setMode(id);setView(admin&&(id==='water'||id==='infrastructure')?'scenario':'observations')}}>{label}</button>)}</div>{admin&&mode!=='air'&&<div className="segmented map-modes" aria-label="Map data source"><button className={view==='observations'?'selected':''} onClick={()=>setView('observations')}>Available observations</button><button className={view==='scenario'?'selected':''} onClick={()=>setView('scenario')}>Simulated scenario</button></div>}{mode==='air'&&admin?<StationMap observations={observations} city={city?.name??''} reports={reports} weatherData={weather} mode="air"/>:mode==='air'?<AirQualityMap city={city?.id??'delhi'}/>:admin&&view==='scenario'?<ScenarioMap city={city?.id??'delhi'} initialLayer={mode==='water'?'water':mode==='rainfall'?'drainage':mode==='traffic'?'road':'all'}/>:mode==='traffic'&&city?.map_reference?<GoogleTraffic city={city.name} centre={city.map_reference}/>:<StationMap observations={observations} city={city?.name??''} reports={reports} weatherData={weather} mode={mode} precipitationOverlay={mode==='rainfall'&&rain.data?.precipitation_tiles_configured}/>} {mode==='rainfall'&&view==='observations'&&<><WeatherPanel weather={weather}/><RainfallChart weather={weather}/></>}</>
}
