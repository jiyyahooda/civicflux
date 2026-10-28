import DelhiReference from '../components/DelhiReference';
import type {City,Observations} from '../types/api';
import type {CivicContext,CivicReport,Weather} from '../types/civic';
export default function Infrastructure({city}:{city:City|undefined;context:CivicContext|null;reports:CivicReport[];observations:Observations|null;weather:Weather|null}){return <><DelhiReference cityId={city?.id??'delhi'}/></>}
