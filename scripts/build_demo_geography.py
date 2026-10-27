from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.graph import dependencies
r=ROOT;sources=json.loads((r/'data/geography/delhi_osm_sources.json').read_text());g=dependencies();assert len(sources)==8
# Clip line references to a declared scenario extent, not a city boundary.
def clip_line(coords):
    output=[];part=[];xmin,ymin,xmax,ymax=77.05,28.48,77.35,28.78
    for a,b in zip(coords,coords[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];lo,hi=0.,1.;valid=True
        for p,q in [(-dx,a[0]-xmin),(dx,xmax-a[0]),(-dy,a[1]-ymin),(dy,ymax-a[1])]:
            if p==0:
                if q<0:valid=False;break
            else:
                t=q/p
                if p<0:lo=max(lo,t)
                else:hi=min(hi,t)
        if not valid or lo>hi:
            if len(part)>1:output.append(part)
            part=[];continue
        left=[a[0]+lo*dx,a[1]+lo*dy];right=[a[0]+hi*dx,a[1]+hi*dy]
        if part and sum(abs(x-y) for x,y in zip(part[-1],left))>1e-7:
            if len(part)>1:output.append(part)
            part=[]
        if not part:part=[left]
        part.append(right)
    if len(part)>1:output.append(part)
    return output
for source in sources:
    original=source['geometry']
    paths=clip_line(original['coordinates']) if original['type']=='LineString' else [p for line in original['coordinates'] for p in clip_line(line)]
    assert paths,'Source outside scenario extent'
    source['display_geometry']={'type':'MultiLineString','coordinates':paths}
    if source['category']=='waterway':
        vertex=min((p for line in paths for p in line),key=lambda p:(p[0]-77.18)**2+(p[1]-28.62)**2)
        source['longitude'],source['latitude']=vertex

assets=[];names={};offsets={'pump':(-.004,-.004),'drainage':(-.002,.003),'road':(0,0),'water':(.003,-.003),'facility':(.005,.003)}
labels={'pump':'pump','drainage':'drain','road':'road segment','water':'water point','facility':'facility'}
for n in g['nodes']:
 index=int(n['id'].split('_')[-1]);a=sources[index%len(sources)];kind=n['node_type'];dy,dx=offsets[kind]
 label=a['name']+' · '+labels[kind]
 assets.append({'id':n['id'],'label':label,'kind':kind,'latitude':a['latitude']+dy,'longitude':a['longitude']+dx,'anchor':a['name'],'source_url':a['source_url'],'location_status':'Illustrative offset from an OSM geographic anchor; not a surveyed municipal asset','synthetic':True})
 names[n['id']]=label
features=[{'type':'Feature','properties':{'name':s['name'],'kind':s['category'],'osm_id':s['osm_id'],'source_url':s['source_url'],'condition':'unknown','geometry_status':'Sourced OSM segment clipped to the declared scenario extent, not an administrative boundary'},'geometry':s['display_geometry']} for s in sources]
reference={'type':'FeatureCollection','features':features}
body={'city_id':'delhi','status':'available','title':'Delhi geographic scenario','synthetic':True,'layout_method':'deterministic illustrative offsets','generator_version':'1.0','graph_fingerprint':g['fingerprint'],'attribution':'© OpenStreetMap contributors · ODbL 1.0','license_url':'https://opendatacommons.org/licenses/odbl/1-0/','source_note':'Road and waterway reference lines come from OSM/Nominatim. All pump, water-point, facility and scenario-node positions and graph links are illustrative. Named geographic anchors do not establish a real asset association.','sources':sources,'reference':reference,'assets':assets,'edges':g['edges'],'default_outages':['drainage_1','drainage_4','pump_3'],'default_assumptions':{'rain_mm':60,'blockage':.35,'vehicles_per_hour':900,'capacity_per_hour':1200},'real_incidents':False}
d=r/'data/geography';d.mkdir(parents=True,exist_ok=True);(d/'delhi_osm_reference.geojson').write_text(json.dumps(reference,indent=2));(d/'delhi_demo.json').write_text(json.dumps(body,indent=2));(d/'LICENSE.md').write_text('OpenStreetMap reference/derived geometry: © OpenStreetMap contributors, ODbL 1.0. https://www.openstreetmap.org/copyright\n\nGeocoding source: Nominatim / OpenStreetMap, retrieved 2026-10-28, source way URLs retained per record. Only the referenced segments are included, not complete inventories. Simulated asset locations, topology associations, conditions and incidents are synthetic, not surveyed municipal records.\n')
f=r/'frontend/src/data';f.mkdir(exist_ok=True);(f/'delhiDemoNames.json').write_text(json.dumps(names,indent=2));print('Created 8 sourced references,',len(assets),'explicitly simulated assets; model graph IDs/fingerprint unchanged.')
