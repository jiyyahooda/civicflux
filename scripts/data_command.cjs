// Native interpreter selection; no shell quoting or POSIX-only Python alias.
const {spawnSync}=require('node:child_process');
const fs=require('node:fs');const path=require('node:path');
const root=path.resolve(__dirname,'..');
const options=process.platform==='win32'?['.venv-windows/Scripts/python.exe','.venv/Scripts/python.exe']:['.venv/bin/python'];
const relative=options.find(p=>fs.existsSync(path.join(root,p)));
if(!relative){console.error('Run the platform setup first to create the native Python environment.');process.exit(1)}
const command=process.argv[2],extra=process.argv.slice(3);
function run(args){const r=spawnSync(path.join(root,relative),args,{cwd:root,stdio:'inherit',env:{...process.env,PYTHONUTF8:'1'}});if(r.error)console.error(r.error.message);return r.status??1}
if(command==='preflight')process.exit(run(['scripts/data_preflight.py',...extra]));
if(command==='verify-all'){
 let failure=run(['scripts/data_pipeline.py','verify','--strict']);
 failure=run(['-m','pytest','-q'])||failure;
 const build=spawnSync(process.platform==='win32'?'corepack.cmd':'corepack',['pnpm','--dir','frontend','build'],{cwd:root,stdio:'inherit',shell:process.platform==='win32'});
 process.exit(build.status||failure);
}
process.exit(run(['scripts/data_pipeline.py',command,...extra]));
