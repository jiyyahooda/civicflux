export type ResourceAmounts={crews:number;workers:number;pumps:number;vehicles:number;budget:number;crew_hours:Record<string,number>};
export type ResourcePool=ResourceAmounts&{id:string;city_id:string;department:string;service_area:string;specialization:string;workers_on_shift:number;equipment:string;source_ref:string;valid_from:string;valid_until:string;updated_at:string;responsible_admin:string;current:boolean;assigned:ResourceAmounts;available:ResourceAmounts};
export type StaffAssignment={crews:number;workers:number;vehicles:number};
export type Reservation={id:string;scenario_id:string;pool_id:string;method:string;requirements:ResourceAmounts;assignments:Record<string,StaffAssignment>;created:string;actor:string;external_dispatch:false};
export type PlanReview={id:string;decision:string;actor:string;created:string;note:string;external_dispatch:false};
export type PlanStatus={reservation:Reservation|null;history:PlanReview[];external_dispatch:false};

export type PublicOperationalPool=Pick<ResourcePool,'id'|'city_id'|'department'|'service_area'|'specialization'|'valid_from'|'valid_until'|'updated_at'|'crews'|'workers'|'pumps'|'vehicles'|'budget'|'crew_hours'|'current'|'available'|'assigned'>;
