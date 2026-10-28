import {useEffect,useRef,useState,type RefObject} from 'react';
import * as THREE from 'three';
export type HeroMotion={progress:number;x:number;y:number};

export default function FluxScene({motion}:{motion:RefObject<HeroMotion>}){
 const host=useRef<HTMLDivElement>(null),[fallback,setFallback]=useState(false);
 useEffect(()=>{
  const node=host.current;if(!node)return;
  let renderer:THREE.WebGLRenderer;
  try{renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'});}catch{setFallback(true);return;}
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5));renderer.setClearColor(0,0);
  renderer.outputColorSpace=THREE.SRGBColorSpace;node.appendChild(renderer.domElement);
  const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(36,1,.1,100);
  const world=new THREE.Group();scene.add(world);
  const geometries:THREE.BufferGeometry[]=[],materials:THREE.Material[]=[];
  const keepG=<T extends THREE.BufferGeometry>(v:T)=>{geometries.push(v);return v};
  const keepM=<T extends THREE.Material>(v:T)=>{materials.push(v);return v};
  const coreMaterial=keepM(new THREE.MeshPhysicalMaterial({color:0x11251b,metalness:.6,roughness:.25,clearcoat:1,clearcoatRoughness:.2}));
  const core=new THREE.Mesh(keepG(new THREE.SphereGeometry(2.12,64,40)),coreMaterial);world.add(core);
  const accentMaterial=keepM(new THREE.LineBasicMaterial({color:0x00e676,transparent:true,opacity:.25}));
  const sphereGrid=new THREE.LineSegments(keepG(new THREE.WireframeGeometry(keepG(new THREE.IcosahedronGeometry(2.15,3)))),accentMaterial);world.add(sphereGrid);
  const continents=new THREE.Group();world.add(continents);
  const satelliteGeometry=keepG(new THREE.IcosahedronGeometry(.055,1));
  const signalMaterial=keepM(new THREE.MeshBasicMaterial({color:0x00e676}));
  // Procedural visual network: decorative geometry, not monitoring locations.
  const locations:THREE.Vector3[]=[];
  for(let i=0;i<80;i++){
   const phi=Math.acos(1-2*(i+.5)/80),theta=i*Math.PI*(3-Math.sqrt(5));
   const point=new THREE.Vector3().setFromSphericalCoords(2.2,phi,theta);locations.push(point);
   const marker=new THREE.Mesh(satelliteGeometry,signalMaterial);marker.position.copy(point);marker.scale.setScalar(i%7===0?1.6:.65);continents.add(marker);
  }
  const curves:THREE.CatmullRomCurve3[]=[];
  for(let i=0;i<locations.length;i+=5){
   const a=locations[i],b=locations[(i+13)%locations.length],mid=a.clone().add(b).normalize().multiplyScalar(2.8+(i%3)*.2);
   const curve=new THREE.CatmullRomCurve3([a,mid,b]);curves.push(curve);
   const line=new THREE.Line(keepG(new THREE.BufferGeometry().setFromPoints(curve.getPoints(40))),keepM(new THREE.LineBasicMaterial({color:0x00e676,transparent:true,opacity:.35})));world.add(line);
  }
  const travellers=curves.map(()=>{const m=new THREE.Mesh(satelliteGeometry,signalMaterial);m.scale.setScalar(.7);world.add(m);return m});
  const rings:THREE.Mesh[]=[];
  for(let i=0;i<3;i++){
   const ring=new THREE.Mesh(keepG(new THREE.TorusGeometry(2.8+i*.32,.011,6,160)),keepM(new THREE.MeshBasicMaterial({color:i===1?0x86aaff:0x00e676,transparent:true,opacity:.65})));
   ring.rotation.set(.5+i*.7,.3+i*.6,i*.2);rings.push(ring);world.add(ring);
  }
  const halo=new THREE.Mesh(keepG(new THREE.TorusGeometry(3.7,.003,4,160)),keepM(new THREE.MeshBasicMaterial({color:0x00e676,transparent:true,opacity:.25})));halo.rotation.x=.8;world.add(halo);
  const particlePositions=[];
  for(let i=0;i<360;i++){
   const angle=i*2.39996,radius=4+(i%17)/8;
   particlePositions.push(Math.cos(angle)*radius,Math.sin(angle*1.9)*3,Math.sin(angle)*radius);
  }
  const starsGeometry=keepG(new THREE.BufferGeometry());starsGeometry.setAttribute('position',new THREE.Float32BufferAttribute(particlePositions,3));
  const starsMaterial=keepM(new THREE.PointsMaterial({color:0xaad8be,size:.017,transparent:true,opacity:.55}));
  const stars=new THREE.Points(starsGeometry,starsMaterial);scene.add(stars);
  scene.add(new THREE.AmbientLight(0xffffff,2));
  const key=new THREE.PointLight(0x00e676,65,30);key.position.set(4,4,5);scene.add(key);
  const rim=new THREE.DirectionalLight(0x6688ff,4);rim.position.set(-4,2,-3);scene.add(rim);
  const fill=new THREE.DirectionalLight(0xffffff,3);fill.position.set(1,6,5);scene.add(fill);
  const theme=()=>{const dark=document.documentElement.dataset.theme==='dark',accent=new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()).getHex();
   accentMaterial.color.setHex(accent);signalMaterial.color.setHex(accent);key.color.setHex(accent);
   materials.forEach(material=>{if(material instanceof THREE.LineBasicMaterial)material.color.setHex(accent)});
   (halo.material as THREE.MeshBasicMaterial).color.setHex(accent);
   coreMaterial.color.setHex(dark?0x09251c:0xe5e6df);coreMaterial.metalness=dark?.65:.3;
   rings.forEach((ring,i)=>(ring.material as THREE.MeshBasicMaterial).color.setHex(i===1?0x839dff:accent));
   starsMaterial.color.setHex(dark?0x91d0ac:0xc5723e);
  };theme();
  const themeObserver=new MutationObserver(theme);themeObserver.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  const resize=()=>{const w=node.clientWidth,h=node.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();};
  const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(node);resize();
  let visible=true,frame=0,elapsed=0,previous=0,rotX=0,rotY=0;
  const visibility=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting});visibility.observe(node);
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  const draw=(now:number)=>{
   frame=requestAnimationFrame(draw);const dt=Math.min((now-previous)/1000,.05);previous=now;
   if(!visible||document.hidden)return;
   const {progress:p,x,y}=motion.current;elapsed+=reduced.matches?0:dt;
   rotX+=(y*.12-rotX)*.05;rotY+=(x*.22-rotY)*.05;
   world.position.y=reduced.matches?0:Math.sin(elapsed*.55)*.06;
   world.rotation.set(.12+(reduced.matches?0:rotX)+p*.5,elapsed*.035+(reduced.matches?0:rotY)+p*2.8,p*-.45);
   const scale=1+Math.sin(Math.min(p,1)*Math.PI)*.45;world.scale.setScalar(scale);
   rings.forEach((ring,i)=>{ring.rotation.z=elapsed*(i%2?-.06:.08)+i+p*(i+1)*.7;ring.position.z=Math.sin(p*Math.PI)*(i-1)*1.4;});
   travellers.forEach((marker,i)=>marker.position.copy(curves[i].getPoint((elapsed*.07+i*.17)%1)));
   stars.rotation.y=elapsed*.008+p*.35;
   const angle=p*.65;camera.position.set(Math.sin(angle)*5,1-p*1.4,12.8-p*2.5);camera.lookAt(0,0,0);
   key.position.x=4+x*2;key.position.y=4-y*2;renderer.render(scene,camera);
  };frame=requestAnimationFrame(draw);
  const lost=(e:Event)=>{e.preventDefault();setFallback(true)};renderer.domElement.addEventListener('webglcontextlost',lost);
  return()=>{cancelAnimationFrame(frame);visibility.disconnect();resizeObserver.disconnect();themeObserver.disconnect();renderer.domElement.removeEventListener('webglcontextlost',lost);geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());renderer.dispose();renderer.domElement.remove();};
 },[motion]);
 return <div className={'flux-scene '+(fallback?'scene-fallback':'')} ref={host} aria-hidden="true">{fallback&&<div className="fallback-orb"><i/><i/><i/></div>}</div>
}
