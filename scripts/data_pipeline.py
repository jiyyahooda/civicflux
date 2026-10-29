"""Reproducible open-data ingestion. No training, Delhi writes or user URLs."""
import argparse,copy,csv,gzip,hashlib,io,json,math,re,sys,time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.data_integration.catalog import SOURCES,BBOX,REFERENCE,EXPECTED,ZONE_COUNTS,CAPACITIES,EVALUATED,ATTR_AIR,ATTR_RIVER
DATA=ROOT/'data'; RAW=DATA/'raw/open_city'; OUT=DATA/'processed'; MANIFEST=DATA/'manifest.json'
HOSTS={'data.opencity.in','ndp.ckan.civicdatalab.in','raw.githubusercontent.com','overpass-api.de','api.open-meteo.com','air-quality-api.open-meteo.com','flood-api.open-meteo.com','api.data.gov.in'}
KINDS={'hospital','fire_station','police','power_substation','water_works','pumping_station'}
CAVEAT="Measured from the PIN's post office point, not its full area."
def sha(content):return hashlib.sha256(content).hexdigest()
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def read_manifest():return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {'version':1,'scope':'Chennai and Chandigarh only; Delhi unchanged','sources':copy.deepcopy(SOURCES),'files':{},'evaluated_not_used':[{'title':t,'reason':r} for t,r in EVALUATED],'live_feeds':[{'id':'air','title':'Modelled US AQI','url':'https://air-quality-api.open-meteo.com/v1/air-quality','licence':'CC BY 4.0; free API non-commercial','attribution':ATTR_AIR,'mode':'live'},{'id':'river','title':'Modelled river discharge','url':'https://flood-api.open-meteo.com/v1/flood','licence':'CC BY 4.0; free API non-commercial','attribution':ATTR_RIVER,'mode':'live'}]}
def atomic_write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_name(path.name+'.tmp');temporary.write_bytes(content);temporary.replace(path)
def save_manifest(m):atomic_write(MANIFEST,canonical(m))
def allowed(url):
    u=urlsplit(url)
    if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password:raise ValueError('Source URL is outside the fixed HTTPS allowlist')
    return url
def request(url,*,data=None):
    import httpx
    # Explicit redirects are revalidated; a CKAN URL cannot redirect into a private network.
    for attempt in range(3):
        try:
            with httpx.Client(timeout=60,follow_redirects=False) as client:
                target=allowed(url)
                for redirect in range(5):
                    r=client.post(target,data=data) if data is not None else client.get(target)
                    if r.is_redirect:
                        from urllib.parse import urljoin
                        target=allowed(urljoin(target,r.headers['location']));continue
                    r.raise_for_status();return r.content
                raise ValueError('Too many redirects')
        except Exception:
            if attempt==2:raise
            time.sleep(.3*2**attempt)
def raw_path(s):return RAW/(s['id']+'.'+s['extension'])
def fetch_one(s):
    s=copy.deepcopy(s);p=raw_path(s)
    try:
        if p.exists():content=p.read_bytes()
        else:
            url=s['url'];post=None
            if s.get('resource_id'):
                metadata=json.loads(request(url))
                if not metadata.get('success'):raise ValueError('CKAN did not return a resource')
                resource=metadata['result'];url=allowed(resource['url']);s['resolved_url']=url
                s['resource_metadata']={k:resource.get(k) for k in ('id','format','last_modified','description','name')}
                RAW.mkdir(parents=True,exist_ok=True);(RAW/(s['id']+'.metadata.json')).write_bytes(canonical(resource))
            elif s['id'].startswith('facilities_'):
                bbox=','.join(map(str,BBOX[s['city']]))
                selectors=['amenity=hospital','amenity=fire_station','amenity=police','power=substation','man_made=water_works','man_made=pumping_station']
                query='[out:json][timeout:180];('+''.join('nwr["'+x.split('=')[0]+'"="'+x.split('=')[1]+'"]('+bbox+');' for x in selectors)+');out center tags;'
                post={'data':query};s['query']=query
            content=request(url,data=post);RAW.mkdir(parents=True,exist_ok=True);p.write_bytes(content)
        s.update(status='FETCHED',raw_sha256=sha(content),byte_size=len(content),retrieved_at=s.get('retrieved_at') or datetime.now(timezone.utc).isoformat())
        s['raw_metadata_sha256']=sha((RAW/(s['id']+'.metadata.json')).read_bytes()) if (RAW/(s['id']+'.metadata.json')).exists() else None
        if s.get('expected_sha256') and s['raw_sha256']!=s['expected_sha256']:s['warning']='Pinned file SHA256 differs from specification; fixture validation is mandatory.'
        s.pop('error',None)
    except Exception as error:
        s.update(status='NOT FETCHED',error=type(error).__name__+((' HTTP '+str(error.response.status_code)) if hasattr(error,'response') else '')+' while fetching fixed source; no replacement data used')
    return s
def fetch():
    m=read_manifest();old={s['id']:s for s in m['sources']}
    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks=[pool.submit(fetch_one,{**s,**old.get(s['id'],{})}) for s in SOURCES]
        result=[]
        for future in as_completed(tasks):
            s=future.result();result.append(s);print(s['id'],s['status'],s.get('byte_size',''),flush=True)
    m['sources']=sorted(result,key=lambda s:s['id']);save_manifest(m)
def haversine(a,b):
    la,lo,lb,lp=map(math.radians,(*a,*b));d=math.sin((lb-la)/2)**2+math.cos(la)*math.cos(lb)*math.sin((lp-lo)/2)**2
    return 6371.0088*2*math.asin(min(1,math.sqrt(d)))
def rounded(value):
    if isinstance(value,float):return round(value,5)
    if isinstance(value,(list,tuple)):return [rounded(v) for v in value]
    if isinstance(value,dict):return {k:rounded(v) for k,v in value.items()}
    return value
def collection(features):return {'type':'FeatureCollection','features':sorted(features,key=lambda f:str(f['id']))}
def feature(id,geom,props):return {'type':'Feature','id':str(id),'geometry':rounded(geom),'properties':props}
def validate_boundaries(id,raw):
    from shapely.geometry import shape,Point
    fs=raw['features'];expected={'che_wards':201,'che_cma':1,'chd_boundary':1,'chd_sectors':63}[id]
    if len(fs)!=expected:raise ValueError(f'{id}: expected {expected} raw features, found {len(fs)}')
    if any(not shape(f['geometry']).is_valid for f in fs):raise ValueError('Invalid source polygon')
    out=[]
    for i,f in enumerate(fs):
        p=f['properties']
        if id=='che_wards':
            if int(p['Ward_No'])==0:continue
            p={'ward_no':int(p['Ward_No']),'zone_no':p['Zone_No'],'zone_name':p['Zone_Name']};key=p['ward_no']
        elif id=='chd_sectors':p={'sector':str(p['Sector_nam'])};key=p['sector']
        else:p={};key=id
        out.append(feature(key,f['geometry'],p))
    if id=='che_wards':
        if {f['properties']['ward_no'] for f in out}!=set(range(1,201)):raise ValueError('Ward identifiers differ from 1..200')
        if Counter(f['properties']['zone_name'] for f in out)!=ZONE_COUNTS:raise ValueError('Zone count fixture mismatch')
    if id=='chd_sectors' and len({f['id'] for f in out})!=63:raise ValueError('Sector identifiers not unique')
    # Validate the supplied axis-order fixtures against the actual source, before shipping.
    point=Point(80.2707,13.0827) if id.startswith('che') else Point(76.7794,30.7333)
    if not any(shape(f['geometry']).covers(point) for f in out):raise ValueError('Axis-order containment fixture failed')
    if id=='che_wards' and not any(f['properties']['ward_no']==58 and shape(f['geometry']).covers(point) for f in out):raise ValueError('Reference point is not in specified ward 58')
    if id=='chd_sectors' and not any(f['properties']['sector']=='22' and shape(f['geometry']).covers(point) for f in out):raise ValueError('Reference point is not in specified sector 22')
    result=collection(out)
    if any(not shape(f['geometry']).is_valid for f in result['features']):raise ValueError('Rounding invalidated a polygon')
    return result
def parse_kml(path):
    """Streaming GDAL-style KML parser preserving SchemaData and dropping Z."""
    def points(text):return [[float(n) for n in p.split(',')[:2]] for p in (text or '').split()]
    def geometry(e):
        typ=e.tag.split('}')[-1]
        if typ=='Point':return {'type':'Point','coordinates':points(e.findtext('.//{*}coordinates'))[0]}
        if typ=='Polygon':
            rings=[]
            for boundary in ('outerBoundaryIs','innerBoundaryIs'):
                for ring in e.findall('./{*}'+boundary+'/{*}LinearRing/{*}coordinates'):rings.append(points(ring.text))
            return {'type':'Polygon','coordinates':rings}
        if typ=='MultiGeometry':
            children=[geometry(c) for c in e if c.tag.split('}')[-1] in ('Point','Polygon','MultiGeometry')]
            return {'type':'GeometryCollection','geometries':children}
        return None
    for _,element in ET.iterparse(path,events=('end',)):
        if element.tag.split('}')[-1]!='Placemark':continue
        props={x.attrib['name']:x.text for x in element.findall('.//{*}SimpleData')}
        props.update({x.attrib['name']:x.findtext('./{*}value') for x in element.findall('.//{*}Data')})
        for key in ('name','description','styleUrl'):
            value=element.findtext('./{*}'+key)
            if value:props[key]=value
        geom=next((geometry(x) for x in element if x.tag.split('}')[-1] in ('Point','Polygon','MultiGeometry')),None)
        if geom:yield geom,props
        element.clear()
def geodesic_area(geom):
    from pyproj import Geod
    from shapely.ops import orient
    if geom.is_empty:return 0
    if geom.geom_type in ('MultiPolygon','GeometryCollection'):return sum(geodesic_area(g) for g in geom.geoms)
    if geom.geom_type!='Polygon':return 0
    return abs(Geod(ellps='WGS84').geometry_area_perimeter(orient(geom,sign=1))[0])
def inundation_properties(p):
    depth=float(p['DEPTH'])
    if not math.isfinite(depth) or not 5<=depth<=60:raise ValueError('Depth fixture outside observed 5..60 inches')
    return {'id':p['OBJECTID_1'],'depth_in':depth,'remark':(p.get('F_REMARKS') or '').strip() or None}
def flood_layer(id,path):
    from shapely.geometry import shape,mapping,box
    from shapely import make_valid,set_precision
    from shapely.ops import unary_union
    repairs=0;precision_collapses=0;original_class_area={}
    rows=list(parse_kml(path));out=[];classes={};evidence={};clip=box(79.9539,12.8015,80.3953,13.3424)
    for i,(geom,p) in enumerate(rows):
        g=shape(geom)
        if id=='che_inundation_points':
            depth=float(p['DEPTH']);remark=(p.get('F_REMARKS') or '').strip() or None
            if not math.isfinite(depth) or not 5<=depth<=60:raise ValueError('Depth fixture outside observed 5..60 inches')
            if g.geom_type!='Point':raise ValueError('Expected inundation point')
            out.append(feature(p['OBJECTID_1'],geom,inundation_properties(p)));continue
        if id=='che_flood_hazard':
            candidates={}
            for k,v in p.items():
                text=str(v or '').strip().lower()
                if text in ('very high','high','moderate','low','very low'):candidates[k]=text.title()
            if len(set(candidates.values()))!=1:raise ValueError('Hazard classification ambiguous or absent; source stopped instead of guessing')
            hazard=next(iter(candidates.values()));evidence.update(candidates);classes[hazard]=classes.get(hazard,0)+1
            props={'class':hazard}
        else:props={k:str(v) for k,v in p.items() if k not in ('description','styleUrl')}
        if not g.is_valid:
            original_area=geodesic_area(g);fixed=make_valid(g)
            if original_area and abs(geodesic_area(fixed)-original_area)/original_area>.02:raise ValueError('Geometry repair exceeds 2 percent geodesic area drift')
            g=fixed;repairs+=1
        if g.geom_type=='GeometryCollection':
            def polygon_parts(v):
                if v.geom_type=='Polygon':return [v]
                return [p for child in getattr(v,'geoms',[]) for p in polygon_parts(child)]
            g=unary_union(polygon_parts(g))
        g=g.intersection(clip)
        if not g.is_empty:
            cls=props.get('class','all');original_class_area[cls]=original_class_area.get(cls,0)+geodesic_area(g)
            quantized=set_precision(g,1e-5,mode='valid_output')
            if quantized.is_empty:precision_collapses+=1;continue
            g=quantized
            out.append(feature(str(p.get('OBJECTID_12') or p.get('OBJECTID_1') or p.get('OBJECTID') or sha(canonical([geom,p]))[:24]),mapping(g),props))
    if len({f['id'] for f in out})!=len(out):raise ValueError('Duplicate stable feature identifiers')
    if id=='che_inundation_points' and not 150<=len(out)<=250:raise ValueError('Expected 150..250 inundation points, found '+str(len(out)))
    if id=='che_flood_hazard' and set(classes)!={'Very High','High','Moderate','Low','Very Low'}:raise ValueError('Hazard classes fixture mismatch')
    original=collection(out);before=len(gzip.compress(canonical(original),mtime=0));tolerance=0
    result=original
    if any(shape(f['geometry']).geom_type in ('Polygon','MultiPolygon','GeometryCollection') for f in out):
        while len(gzip.compress(canonical(result),mtime=0))>1500000:
            tolerance=.00001 if tolerance==0 else tolerance*2
            if tolerance>.01:raise ValueError('Layer cannot fit size without unsafe simplification')
            result=collection([feature(f['id'],mapping(shape(f['geometry']).simplify(tolerance,preserve_topology=True)),f['properties']) for f in out])
        for category in ('Very High','High','Moderate','Low','Very Low') if id=='che_flood_hazard' else ('all',):
            select=lambda f:category=='all' or f['properties'].get('class')==category
            a=sum(geodesic_area(shape(f['geometry'])) for f in out if select(f));b=sum(geodesic_area(shape(f['geometry'])) for f in result['features'] if select(f))
            if a and abs(a-b)/a>.02:raise ValueError('Simplification exceeds 2 percent geodesic area drift')
    if any(not shape(f['geometry']).is_valid for f in result['features']):raise ValueError('Invalid output geometry')
    drift={}
    for category,a in original_class_area.items():
        b=sum(geodesic_area(shape(f['geometry'])) for f in result['features'] if f['properties'].get('class','all')==category)
        drift[category]=abs(a-b)/a if a else 0
        if a and abs(a-b)/a>.02:raise ValueError('Combined precision/repair/simplification area drift exceeds 2 percent')
    return result,{'records_in':len(rows),'precision_collapses':precision_collapses,'original_geodesic_area_m2':original_class_area,'classification_evidence':{'field':'CATEGORY','value_mapping':{k:k for k in sorted(classes)}} if id=='che_flood_hazard' else {},'class_area_drift_fraction':drift,'simplification_degrees':tolerance,'original_gzip_bytes':before,'geometry_repairs':repairs}
def resolve_pin(pin,rows,layers):
    from shapely.geometry import Point,shape
    from shapely.ops import unary_union
    city='chennai' if pin.startswith('6') else 'chandigarh';expected=EXPECTED.get(pin);s,w,n,e=BBOX[city]
    candidates=[]
    for row in rows:
        if row['Pincode']!=pin:continue
        try:lat,lon=float(row['Latitude']),float(row['Longitude'])
        except (ValueError,TypeError):continue
        if s<=lat<=n and w<=lon<=e:candidates.append((lat,lon))
    if expected:
        fs=layers['che_wards' if city=='chennai' else 'chd_sectors']['features'];key='zone_name' if city=='chennai' else 'sector'
        region=unary_union([shape(f['geometry']) for f in fs if f['properties'][key] in expected])
        if region.is_empty:raise ValueError('Expected polygons missing')
        candidates=[p for p in candidates if (region.contains(Point(p[1],p[0])) if city=='chennai' else region.buffer(.003).covers(Point(p[1],p[0])))]
        if candidates:point=(median(p[0] for p in candidates),median(p[1] for p in candidates));quality='validated'
        else:
            center=region.centroid
            if not region.covers(center):center=region.representative_point()
            point=(center.y,center.x);quality='polygon-centroid'
    else:
        if candidates:
            center=(median(p[0] for p in candidates),median(p[1] for p in candidates))
            boundary=unary_union([shape(f['geometry']) for f in layers['chd_boundary']['features']]).buffer(.005)
            candidates=[p for p in candidates if haversine(p,center)<=5 and boundary.covers(Point(p[1],p[0]))]
        if not candidates:point=(30.7333,76.7794);quality='city-centre'
        else:point=(median(p[0] for p in candidates),median(p[1] for p in candidates));quality='boundary-validated'
    return {'pin':pin,'city':city,'lat':round(point[0],5),'lng':round(point[1],5),'coords_quality':quality,'coords_verified':quality in ('validated','boundary-validated')}
def facilities(city,raw,boundary):
    from shapely.geometry import shape,Point
    from shapely.ops import transform,unary_union
    from pyproj import Transformer
    epsg=32644 if city=='chennai' else 32643
    project=Transformer.from_crs(4326,epsg,always_xy=True).transform
    mask=transform(project,unary_union([shape(f['geometry']) for f in boundary['features']])).buffer(1000)
    result=[]
    for e in raw.get('elements',[]):
        p=e.get('tags',{});location=e.get('center',e);lat=location.get('lat');lon=location.get('lon')
        if lat is None or lon is None or not mask.covers(Point(*project(lon,lat))):continue
        kind=p.get('amenity') if p.get('amenity') in KINDS else 'power_substation' if p.get('power')=='substation' else p.get('man_made')
        if kind not in KINDS:continue
        result.append(feature('osm:'+e['type']+'/'+str(e['id']),{'type':'Point','coordinates':[lon,lat]},{'id':'osm:'+e['type']+'/'+str(e['id']),'kind':kind,'name':p.get('name') or None,'operator':p.get('operator') or None,'source':'OpenStreetMap'}))
    # Named features win over unnamed neighbours, then stable OSM ID.
    result.sort(key=lambda f:(not bool(f['properties']['name']),f['id']));kept=[]
    def norm(f):return re.sub(r'\W+','',(f['properties']['name'] or '').casefold())
    for f in result:
        if any(f['properties']['kind']==g['properties']['kind'] and (not norm(f) or not norm(g) or norm(f)==norm(g)) and haversine(tuple(reversed(f['geometry']['coordinates'])),tuple(reversed(g['geometry']['coordinates'])))<.05 for g in kept):continue
        kept.append(f)
    counts=Counter(f['properties']['kind'] for f in kept)
    if any(counts[k]==0 for k in ('hospital','fire_station','police')):raise ValueError('Required facility type has zero features')
    return collection(kept),dict(counts)
def lake_csv(text):
    from dateutil.parser import parse
    reader=csv.DictReader(io.StringIO(text));headers=reader.fieldnames or []
    if 'Year' in headers and len(headers)==13 and all(headers[i+1].strip().lower().startswith(name) for i,name in enumerate(('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'))):
        out=[];seen=set()
        for row in reader:
            year=int(row['Year'])
            for i,header in enumerate(headers[1:],1):
                month=f'{year:04d}-{i:02d}';raw=(row[header] or '').strip().replace(',','')
                value=None if raw.lower() in ('','na','n/a','null','-') else float(raw)
                if month in seen or (value is not None and (not math.isfinite(value) or value<0)):raise ValueError('Duplicate month or invalid reservoir storage')
                seen.add(month);out.append({'month':month,'mcft':value})
        return sorted(out,key=lambda r:r['month'])
    dates=[h for h in headers if re.search(r'date|month',h,re.I)];stores=[h for h in headers if re.search(r'mcft|storage|level',h,re.I)]
    if len(dates)!=1 or len(stores)!=1:raise ValueError('Ambiguous lake CSV headers: '+repr(headers))
    out=[];months=set()
    for row in reader:
        month=parse(row[dates[0]],dayfirst=True).strftime('%Y-%m')
        if month in months:raise ValueError('Duplicate lake month '+month)
        months.add(month);raw=(row[stores[0]] or '').strip().replace(',','')
        value=None if raw.lower() in ('','na','n/a','null','-') else float(raw)
        if value is not None and (not math.isfinite(value) or value<0):raise ValueError('Invalid lake storage')
        out.append({'month':month,'mcft':value})
    return sorted(out,key=lambda r:r['month'])
def exposure(pin,layers):
    from shapely.geometry import shape,Point
    point=Point(pin['lng'],pin['lat']);latlon=(pin['lat'],pin['lng']);out={'pin':pin['pin'],'city':pin['city'],'caveat':CAVEAT,'radius_km':2}
    def near(id):return [f for f in layers.get(id,{}).get('features',[]) if shape(f['geometry']).geom_type=='Point' and haversine(latlon,tuple(reversed(f['geometry']['coordinates'])))<=2]
    hazards=layers.get('che_flood_hazard');facs=layers.get('facilities_'+pin['city']);near_facs=near('facilities_'+pin['city'])
    def hazard(pt):
        hits=[f['properties']['class'] for f in (hazards or {}).get('features',[]) if shape(f['geometry']).covers(pt)]
        return next((v for v in ('Very High','High','Moderate','Low','Very Low') if v in hits),None)
    out.update(hazard_class_at_point=hazard(point) if hazards and pin['city']=='chennai' else None,hazard_available=bool(hazards) and pin['city']=='chennai',in_2015_inundation_zone=any(shape(f['geometry']).covers(point) for f in layers['che_flood_zone_2015']['features']) if pin['city']=='chennai' and 'che_flood_zone_2015' in layers else None)
    for id,key in [('che_flood_points_2015','flood_points_2015_within_r'),('che_inundation_points','inundation_points_within_r')]:out[key]=len(near(id)) if id in layers and pin['city']=='chennai' else None
    out['max_depth_in_within_r']=max((f['properties']['depth_in'] for f in near('che_inundation_points')),default=None) if pin['city']=='chennai' else None
    out['facilities_within_r']={k:sum(f['properties']['kind']==k for f in near_facs) for k in sorted(KINDS)} if facs else None
    out['nearest_km']={k:round(min((haversine(latlon,tuple(reversed(f['geometry']['coordinates']))) for f in facs['features'] if f['properties']['kind']==k),default=0),3) for k in ('hospital','fire_station','police')} if facs else None
    out['facilities_in_hazard_within_r']=sum(hazard(shape(f['geometry'])) in ('Very High','High','Moderate') for f in near_facs) if facs and hazards and pin['city']=='chennai' else None
    out['note']='No open flood-hazard dataset was found for Chandigarh.' if pin['city']=='chandigarh' else 'Historical mapped exposure; absence from a mapped zone does not establish safety.'
    return out
def build():
    m=read_manifest();sources={s['id']:s for s in m['sources']};m.pop('coordinate_failures',None);m['files']={};layers={};OUT.mkdir(parents=True,exist_ok=True)
    def emit(relative,value,source_ids):
        content=canonical(value);compressed=gzip.compress(content,mtime=0)
        if relative.endswith('.geojson') and len(compressed)>1500000:raise ValueError('Served layer exceeds 1.5 MB gzip')
        p=OUT/relative;atomic_write(p,content)
        m['files'][relative]={'sha256':sha(content),'bytes':len(content),'gzip_bytes':len(compressed),'source_ids':source_ids,'feature_count':len(value['features']) if isinstance(value,dict) and 'features' in value else None}
    def process(id,fn,relative):
        s=sources[id]
        if not raw_path(s).exists():s['status']='NOT FETCHED';return
        try:
            if s.get('raw_sha256') and sha(raw_path(s).read_bytes())!=s['raw_sha256']:raise ValueError('Raw file changed since fetch; refetch before processing')
            value,meta=fn(raw_path(s));emit(relative,value,[id]);s.update(status='OK',records_out=len(value.get('features',value.get('series',[]))),**meta);s.pop('error',None)
            if relative.endswith('.geojson'):layers[id]=value
        except Exception as error:s.update(status='FAILED',error=str(error)[:400]);print(id,'FAILED',s['error'],flush=True)
    for id in ('che_cma','che_wards','chd_boundary','chd_sectors'):
        process(id,lambda p,id=id:(validate_boundaries(id,json.loads(p.read_text())),{'records_in':len(json.loads(p.read_text())['features'])}),'datameet/'+id+'.geojson')
    pins=[];directory=sources['pin_directory'];rows=[]
    try:
        if raw_path(directory).exists():
            rows=list(csv.DictReader(io.StringIO(raw_path(directory).read_text(encoding='utf-8-sig'))))
            if len(rows)!=157126 or len({r['Pincode'] for r in rows})!=19300 or sum(r['Latitude'].strip().upper() in ('','NA') for r in rows)!=8838:raise ValueError('PIN directory row/distinct/empty-coordinate fixture mismatch')
            directory.update(status='OK',records_in=len(rows),records_out=0);directory.pop('error',None)
    except Exception as error:directory.update(status='FAILED',error=str(error));rows=[]
    for pin,(lat,lon) in REFERENCE.items():
        city='chennai' if pin.startswith('6') else 'chandigarh';needed=('che_cma','che_wards') if city=='chennai' else ('chd_boundary','chd_sectors')
        if rows and all(n in layers for n in needed):
            try:
                value=resolve_pin(pin,rows,layers)
                if abs(value['lat']-lat)>.002 or abs(value['lng']-lon)>.002:raise ValueError('PIN '+pin+' differs from reference by over 0.002 degrees')
            except Exception as error:
                m.setdefault('coordinate_failures',{})[pin]=str(error);continue
        else:value={'pin':pin,'city':city,'lat':lat,'lng':lon,'coords_quality':'reference-table','coords_verified':False}
        office=sorted({r['OfficeName'] for r in rows if r['Pincode']==pin})
        value.update(area_name=', '.join(office) if office else None,source_id='pin_directory' if value['coords_quality']!='reference-table' else 'user-spec-reference-table')
        pins.append(value)
    emit('derived/pincodes.json',sorted(pins,key=lambda p:p['pin']),['pin_directory']);directory['records_out']=len(pins)
    seed=ROOT/'seed/pincodes.json';seed.parent.mkdir(exist_ok=True);atomic_write(seed,canonical(sorted(pins,key=lambda p:p['pin'])))
    for id in ('che_flood_hazard','che_flood_zone_2015','che_flood_points_2015','che_inundation_points'):process(id,lambda p,id=id:flood_layer(id,p),'flood/'+id+'.geojson')
    for city in BBOX:
        boundary='che_cma' if city=='chennai' else 'chd_boundary';id='facilities_'+city
        if boundary not in layers:
            sources[id].update(status='NOT FETCHED' if not raw_path(sources[id]).exists() else 'FAILED',error='Validated city boundary unavailable; facilities not shipped');continue
        def convert(p,city=city,boundary=boundary):
            raw=json.loads(p.read_text());value,counts=facilities(city,raw,layers[boundary]);return value,{'records_in':len(raw.get('elements',[])),'kind_counts':counts}
        process(id,convert,'facilities/'+id+'.geojson')
    reservoirs=[]
    for key in CAPACITIES:
        id='lake_'+key;s=sources[id]
        if not raw_path(s).exists():continue
        try:
            metadata=json.loads((RAW/(id+'.metadata.json')).read_text())
            if 'mcft' not in (metadata.get('description','')+' '+raw_path(s).read_text().splitlines()[0]).lower():raise ValueError('Storage units not verified as mcft')
            series=lake_csv(raw_path(s).read_text(encoding='utf-8-sig'))
            if not series:raise ValueError('Empty reservoir series')
            if key in ('poondi','kannankottai') and next((r['month'] for r in series if r['mcft'] is not None),None)!=('2003-01' if key=='poondi' else '2020-12'):raise ValueError('Reservoir first-month fixture mismatch')
            for row in series:row['above_capacity_threshold']=row['mcft'] is not None and row['mcft']>1.05*CAPACITIES[key]
            reservoirs.append({'id':key,'name':s['reservoir_name'],'series':series,'first_month':next((r['month'] for r in series if r['mcft'] is not None),series[0]['month']),'last_month':next((r['month'] for r in reversed(series) if r['mcft'] is not None),series[-1]['month'])});s.update(status='OK',records_in=len(series),records_out=len(series));s.pop('error',None)
        except Exception as error:s.update(status='FAILED',error=str(error))
    # The supplied capacities sum to 13222, but their official verification is pending: do not compute % full.
    if len(reservoirs)==6:emit('derived/reservoirs.json',{'reservoirs':sorted(reservoirs,key=lambda r:r['id']),'dataset_last_updated':'2025-11-27','capacities_mcft':CAPACITIES,'capacities_verified':False,'capacity_source':'User-supplied reference constants; official CMWSSB verification pending. Percent full withheld.'},['lake_'+k for k in CAPACITIES])
    emit('derived/pin_exposure.json',{p['pin']:exposure(p,layers) for p in pins},list(layers))
    for p in OUT.rglob('*'):
        if p.is_file() and p.suffix in ('.json','.geojson') and str(p.relative_to(OUT)) not in m['files']:p.unlink()
    (OUT/'datameet').mkdir(parents=True,exist_ok=True)
    (OUT/'datameet/LICENCE.txt').write_text('Derived DataMeet city layers: CC BY-SA 2.5 India. Share derived layers under the same licence.\nChennai: Transparent Chennai team via DataMeet India community.\nChandigarh: DataMeet India community.\nhttps://creativecommons.org/licenses/by-sa/2.5/in/\n',encoding='utf-8')
    notice=OUT/'datameet/LICENCE.txt';notice_bytes=notice.read_bytes();m['files']['datameet/LICENCE.txt']={'sha256':sha(notice_bytes),'bytes':len(notice_bytes),'gzip_bytes':len(gzip.compress(notice_bytes,mtime=0)),'source_ids':['che_cma','che_wards','chd_boundary','chd_sectors'],'feature_count':None}
    for source in sources.values():
        metadata=RAW/(source['id']+'.metadata.json')
        if metadata.exists():source['raw_metadata_sha256']=sha(metadata.read_bytes())
        if source['id'] in ('che_cma','che_wards','chd_boundary','chd_sectors'):source['source_last_updated']='2023-11-16';source['attribution_url']='https://github.com/datameet/Municipal_Spatial_Data/tree/9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17/'+source['city'].title()
    m['verified_structure_deviations']=['User approved 2026-10-30: missing PIN latitudes encoded as NA (8838), not empty strings.','Hazard CATEGORY has five classes: Very High, High, Moderate, Low, Very Low; preserved without merging.','Reservoir CSVs use Year plus Jan-Dec columns; null padding retained, first_month means first non-null observation.','Puzhal CSV lacks an mcft header; the recorded CKAN resource description explicitly confirms mcft units.','All six reservoir files end in December 2021 despite the catalogue publication/update dates in 2025. Latest values are labelled 2021-12.']
    m['sources']=sorted(sources.values(),key=lambda s:s['id']);save_manifest(m);status()
def verify(strict=False):
    from shapely.geometry import shape
    m=read_manifest();errors=[]
    for relative,meta in m['files'].items():
        p=OUT/relative
        if not p.is_file() or sha(p.read_bytes())!=meta['sha256']:errors.append('Checksum mismatch / missing: '+relative);continue
        if relative.endswith('.geojson'):
            value=json.loads(p.read_text())
            if len(gzip.compress(p.read_bytes(),mtime=0))>1500000:errors.append('Layer over size cap: '+relative)
            if any(not shape(f['geometry']).is_valid for f in value['features']):errors.append('Invalid geometry: '+relative)
    if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>25000000:errors.append('Processed directory over 25 MB')
    pins=json.loads((OUT/'derived/pincodes.json').read_text()) if (OUT/'derived/pincodes.json').exists() else []
    if {p['pin'] for p in pins}!=set(REFERENCE):errors.append('Not all 19 non-Delhi target PINs passed')
    for p in pins:
        ref=REFERENCE[p['pin']]
        if abs(p['lat']-ref[0])>.002 or abs(p['lng']-ref[1])>.002 or not p['coords_quality']:errors.append('PIN fixture: '+p['pin'])
    if sum(CAPACITIES.values())!=13222:errors.append('Capacity constant fixture')
    incomplete=[s['id'] for s in m['sources'] if s['status']!='OK']
    print('PASS integrity checks' if not errors else 'FAIL '+ '; '.join(errors))
    print('INCOMPLETE sources: '+', '.join(incomplete) if incomplete else 'PASS all mandatory sources')
    for id,expected in [('che_cma',1),('che_wards',200),('chd_boundary',1),('chd_sectors',63)]:
        relative='datameet/'+id+'.geojson'
        if relative in m['files']:
            value=json.loads((OUT/relative).read_text())
            if len(value['features'])!=expected:errors.append('Boundary count fixture: '+id)
            if id=='che_wards' and (Counter(f['properties']['zone_name'] for f in value['features'])!=ZONE_COUNTS or {f['properties']['ward_no'] for f in value['features']}!=set(range(1,201))):errors.append('Ward identifiers/zone fixtures')
    flood=OUT/'flood/che_flood_hazard.geojson'
    if flood.is_file() and {f['properties']['class'] for f in json.loads(flood.read_text())['features']}!={'Very High','High','Moderate','Low','Very Low'}:errors.append('Five verified hazard classes fixture')
    if strict and incomplete:errors.append('Mandatory sources incomplete')
    return not errors
def status():
    for s in read_manifest()['sources']:print(s['id'],s['status'],s.get('records_out'),s.get('error',''),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['fetch','build','verify','status']);parser.add_argument('--strict',action='store_true');args=parser.parse_args()
    if args.command=='verify':sys.exit(0 if verify(args.strict) else 1)
    else:globals()[args.command]()
