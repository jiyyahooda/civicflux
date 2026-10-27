import InfrastructureMap from '../components/InfrastructureMap';
import type {Graph,Scenario,Observations} from '../types/api';
export default function Infrastructure({graph,city,scenario,observations}:{graph:Graph|null;city?:string;scenario?:Scenario|null;observations:Observations|null}){return graph?<InfrastructureMap graph={graph} city={city} scenario={scenario} observations={observations}/>:<p role="status">Loading infrastructure graph…</p>}
