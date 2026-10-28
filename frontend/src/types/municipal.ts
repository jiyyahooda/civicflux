import type {Scenario,Allocation,Candidate} from './api';
import type {Reservation,PlanReview} from './operational';
export type AdminProfile={id:string;username:string;display_name:string;role:string;cities:string[];assignments:{pincode:string;city_id:string;locality_name:string}[]};
export type Pin={pincode:string;city_id:string;locality_name:string;source:string;jurisdiction_note:string};
export type Budget={id:string;city_id:string;pincode:string;pool_id:string;budget:number;severity_weight:number;population_weight:number;fiscal_year:string;source_ref:string};
export type LocalCandidate=Pick<Candidate,'case_id'|'node_id'|'cost'|'duration_hours'|'pumps_required'|'crew_type'>&{title:string;required_crews:number;required_workers:number;required_vehicles:number;reason:string;affected_people_count:number|null;damage_priority:string};
export type MunicipalPlan=Omit<Scenario,'allocation'>&{pincode?:string;budget_id?:string;pool_id?:string;incident_ids?:string[];internal_review_status?:string;progress:string;reservation:Reservation|null;decisions:PlanReview[];allocation:{comparisons:Record<string,Omit<Allocation,'selected'>&{selected:LocalCandidate[];unfunded?:{title:string;unfunded_reason:string}[]}>;candidates:LocalCandidate[];unfunded?:{title:string;unfunded_reason:string}[]}};
