from src.civicflux.optimization import solve_cpsat,greedy_allocate,DEFAULT_WEIGHTS,validate_weights

def plan(cases,resources,weights=None):
    weights=validate_weights(weights or DEFAULT_WEIGHTS)
    results={'CP-SAT':solve_cpsat(cases,resources,weights), 'utility_greedy':greedy_allocate(cases,resources,'utility',weights), 'severity_greedy':greedy_allocate(cases,resources,'severity',weights)}
    explanations=[]
    for case in cases:
        breakdown={k:weights[k]*case[k]*(-1 if k=='carbon_penalty' else 1) for k in weights}
        explanations.append({**case,'score_breakdown':breakdown,'utility':sum(breakdown.values())})
    return {'comparisons':results,'candidates':explanations,'weights':weights,'constraints':['Shared hypothetical budget','Crew hours per skill','Pump availability','Each candidate selected at most once'],'dispatch_allowed':False}


def plan_localities(cases,resources,severity_weight=.6,population_weight=.4):
    """Extend the existing OR-Tools planner with actual staff/vehicle capacities.

    Candidate inputs are officer assessments, not research-model geography.
    """
    from ortools.sat.python import cp_model
    import math
    total=severity_weight+population_weight
    if total<=0:raise ValueError('At least one priority weight must be positive')
    sw,pw=severity_weight/total,population_weight/total
    known=[c['affected_people_count'] for c in cases if c.get('affected_people_count') is not None]
    maximum=max(known,default=0)
    enriched=[]
    for original in cases:
        c=dict(original);c['crew_hours_required']=c['duration_hours']*c['required_crews'];severity=c['severity']/4
        population=None if c.get('affected_people_count') is None else (c['affected_people_count']/maximum if maximum else 0)
        c['priority_score']=(severity if sw>0 else 0) if population is None else sw*severity+pw*population
        c['normalized_severity']=severity;c['normalized_population']=population
        c['reason']=f"Severity {c['damage_priority']}; "+('affected population unknown, severity weight renormalized to 100%.' if population is None else f"{c['affected_people_count']} people ({c['population_basis']}); weights {sw:.0%}/{pw:.0%}.")
        enriched.append(c)
    def fits(selected):
        return all(c['duration_hours']<=resources.get('work_window_hours',float('inf')) for c in selected) and all(sum(c[k] for c in selected)<=resources[r]+1e-9 for k,r in [('cost','budget'),('pumps_required','pumps'),('required_crews','crews'),('required_workers','workers'),('required_vehicles','vehicles')]) and all(sum(c['crew_hours_required'] for c in selected if c['crew_type']==k)<=v+1e-9 for k,v in resources['crew_hours'].items())
    def result(selected,status):
        return {'selected':selected,'status':status,'used':{'budget':sum(c['cost'] for c in selected),'pumps':sum(c['pumps_required'] for c in selected),'crew_hours':{k:sum(c['crew_hours_required'] for c in selected if c['crew_type']==k) for k in resources['crew_hours']},'crews':sum(c['required_crews'] for c in selected),'workers':sum(c['required_workers'] for c in selected),'vehicles':sum(c['required_vehicles'] for c in selected)},'objective':sum(c['priority_score'] for c in selected),'unfunded':[{**c,'unfunded_reason':('Package exceeds declared capacity, work window or specialization.' if not fits([c]) else 'Not selected by this alternative under the shared constraints and priority ordering.')} for c in enriched if c['case_id'] not in {s['case_id'] for s in selected}],'dispatch_allowed':False}
    model=cp_model.CpModel();choices=[model.NewBoolVar('case_'+c['case_id']) for c in enriched]
    for key,capacity in [('cost','budget'),('pumps_required','pumps'),('required_crews','crews'),('required_workers','workers'),('required_vehicles','vehicles')]:model.Add(sum(c[key]*x for c,x in zip(enriched,choices))<=resources[capacity])
    for c,x in zip(enriched,choices):
        if c['duration_hours']>resources.get('work_window_hours',float('inf')):model.Add(x==0)
    for skill,limit in resources['crew_hours'].items():model.Add(sum(math.ceil(c['crew_hours_required']*60)*x for c,x in zip(enriched,choices) if c['crew_type']==skill)<=math.floor(limit*60))
    model.Maximize(sum(round(c['priority_score']*100000)*x for c,x in zip(enriched,choices)))
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=5;solver.parameters.num_search_workers=1;solver.parameters.random_seed=42
    status=solver.Solve(model);selected=[c for c,x in zip(enriched,choices) if solver.Value(x)] if status in (cp_model.OPTIMAL,cp_model.FEASIBLE) else []
    comparisons={'CP-SAT':result(selected,solver.StatusName(status))}
    for method,key in [('utility_greedy','priority_score'),('severity_greedy','severity')]:
        chosen=[]
        for c in sorted(enriched,key=lambda c:(c[key],c['priority_score'],c['case_id']),reverse=True):
            if fits([*chosen,c]):chosen.append(c)
        comparisons[method]=result(chosen,'HEURISTIC_FEASIBLE')
    selected_ids={c['case_id'] for c in selected}
    unresolved=[{**c,'unfunded_reason':('The package exceeds declared capacity, work window or crew specialization.' if not fits([c]) else 'No supported positive priority under the selected weights and available evidence.' if c['priority_score']<=0 else 'Other selected packages use the available shared capacity.')} for c in enriched if c['case_id'] not in selected_ids]
    return {'comparisons':comparisons,'candidates':enriched,'unfunded':unresolved,'weights':{'severity':sw,'affected_population':pw},'constraints':['Declared locality funds','Unreserved pool capacity','Workers and crews','Vehicles and pumps','Specialized crew-hours','City and PIN jurisdiction'],'sustainability_effect':'Not quantified: no independently supported causal impact model is available.'}
