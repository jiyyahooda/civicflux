export type TourContext={admin:boolean;city:string;supervisor:boolean;civilian?:boolean};
export type TourStep={id:string;topic:string;page:string;target:string;title:string;text:string;prepare?:string[];action?:{event:'click'|'change';selector?:string;expect?:string;hint:string};condition?:'admin'|'public';missing?:string};
const t=(id:string)=>`[data-tour="${id}"]`;
const publicSteps:TourStep[]=[
 {id:'landing',topic:'Welcome',page:'Overview',target:t('explore'),title:'Welcome to CivicFlux',text:'Explore conditions in your city and report local issues. Choose Explore your city to reach the dashboard.'},
 {id:'public-nav',topic:'Navigation',page:'Overview',target:t('public-nav'),prepare:['explore'],title:'Your main navigation',text:'Overview, City map, Predictions, Report a problem and Monetary history are your main pages. Choose a city and postal area to see the relevant available information.'},
 {id:'report-form',topic:'Reports',page:'Report a problem',target:t('report-form'),title:'Report and track an issue',text:'Describe an issue and capture evidence here. After submitting, keep your report ID and use Track your report below to follow its status; this tour submits nothing.'},
 {id:'map-modes',topic:'City map',page:'City map',target:t('map-modes'),title:'Explore your city map',text:'Switch between rainfall, air quality, traffic, water supply and infrastructure alerts. Each view shows its available sources and explains missing coverage.'},
 {id:'account-menu',topic:'Account',page:'City map',target:t('account-menu'),title:'Your account, in one place',text:'Open this avatar for Civilian Login or your existing Profile. Admin Login is in the public Overview footer; guests can still access their browser-local profile.'},
];
const adminSteps:TourStep[]=[
 {id:'admin-area',topic:'Welcome',page:'Overview',target:t('admin-area'),title:'Welcome to your workspace',text:'Your assigned jurisdiction appears here. The existing permissions determine which records and actions you can access.'},
 {id:'admin-nav',topic:'Navigation',page:'Overview',target:t('admin-nav'),title:'Your workspace navigation',text:'Use these tabs for City map, Review reports, Predictions, Planning, Decisions, City infra and Monetary history. Your current tab is highlighted.'},
 {id:'review-queue',topic:'Reports',page:'Review reports',target:t('review-queue'),title:'Manage reports',text:'Review reports for your assigned area and open a record to verify it or respond. Changes are saved only when you deliberately submit them.'},
 {id:'decision-mode',topic:'Decisions',page:'Decisions',target:t('decision-mode'),title:'Compare conditions and scenarios',text:'Switch between Current situation and What if to explore the available assessments. Planning contains the related resource and budget workflows.'},
 {id:'admin-account',topic:'Account',page:'Decisions',target:t('account-menu'),title:'Your administrator account',text:'Open the avatar to see your administrator role and assigned jurisdiction. Sign out is available in the same compact menu.'},
];
export const tourCatalog=[...publicSteps,...adminSteps];
export function availableSteps(context:TourContext){return context.admin?adminSteps:publicSteps}
export type Progress=Record<string,'completed'|'skipped'>;
export function readProgress(raw:string|null):Progress{try{const parsed=JSON.parse(raw??'{}');if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))return {};return Object.fromEntries(Object.entries(parsed).filter(([id,value])=>tourCatalog.some(s=>s.id===id)&&(value==='completed'||value==='skipped'))) as Progress}catch{return {}}}
