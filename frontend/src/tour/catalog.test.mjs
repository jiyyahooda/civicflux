import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import ts from 'typescript';
const root=resolve(import.meta.dirname,'..');
const source=readFileSync(resolve(import.meta.dirname,'catalog.ts'),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const {tourCatalog,availableSteps,readProgress}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
test('each role receives exactly five concise steps in every supported city',()=>{for(const city of ['delhi','chennai','chandigarh'])for(const admin of [false,true]){const steps=availableSteps({admin,city,supervisor:false});assert.equal(steps.length,5);assert.equal(steps.at(-1).topic,'Account');for(const s of steps){assert.ok(s.text.length<300);assert.ok(s.title&&s.target)}}});
test('public walkthroughs never navigate to restricted municipal pages',()=>{for(const civilian of [false,true]){const steps=availableSteps({admin:false,civilian,city:'delhi',supervisor:false});assert.ok(steps.every(s=>['Overview','Report a problem','City map'].includes(s.page)));assert.ok(steps.some(s=>s.id==='report-form'))}});
test('administrator walkthrough covers real review and decision workflows',()=>{for(const supervisor of [false,true]){const steps=availableSteps({admin:true,city:'chennai',supervisor});assert.ok(steps.some(s=>s.page==='Review reports'));assert.ok(steps.some(s=>s.page==='Decisions'));assert.ok(!steps.some(s=>s.page==='Profile'||s.page==='Report a problem'))}});
test('step IDs are unique and stored completion remains validated',()=>{assert.equal(new Set(tourCatalog.map(s=>s.id)).size,tourCatalog.length);for(const raw of ['broken','null','[]','1'])assert.deepEqual(readProgress(raw),{});assert.deepEqual(readProgress('{"landing":"completed","report-form":"skipped","unknown":"completed","admin-area":"bad"}'),{landing:'completed','report-form':'skipped'})});
function files(dir){return readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(resolve(dir,e.name)):e.name.endsWith('.tsx')?[resolve(dir,e.name)]:[])}
const controls=files(root).filter(f=>!f.includes('/tour/')).map(f=>readFileSync(f,'utf8')).join('\n');
const ids=new Set([...controls.matchAll(/data-tour="([a-z-]+)"/g)].map(m=>m[1]));
test('all spotlight targets and preparation controls exist in the real app',()=>{for(const s of tourCatalog){for(const match of s.target.matchAll(/data-tour="([\w-]+)"/g))assert.ok(ids.has(match[1]),s.id);for(const id of s.prepare??[])assert.ok(ids.has(id),s.id)}});
test('tour preparation never points at a save boundary',()=>{const writes=[...controls.matchAll(/data-tour="([\w-]+)" data-tour-save=/g)].map(m=>m[1]);for(const s of tourCatalog)for(const id of s.prepare??[])assert.ok(!writes.includes(id))});
