"""Fixed source catalogue from the user-supplied 2026-10-29 integration spec."""
DM_COMMIT = '9b4d1c2ece54cdeb6f5e8bad9ccad7844f783b17'
DM = 'https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/' + DM_COMMIT
PIN_URL = 'https://raw.githubusercontent.com/dropdevrahul/pincodes-india/d817d3e652e8167a70507350d9a8e4acda9113ef/pincode.csv'
ATTR_DM = {'chennai':'Chennai Municipal Data, received from the Transparent Chennai team, via DataMeet India community (CC BY-SA 2.5 India)', 'chandigarh':'Chandigarh Municipal Spatial Data via DataMeet India community (CC BY-SA 2.5 India)'}
ATTR_FLOOD = 'Greater Chennai Corporation via OpenCity.in; credit Vaidyanathan R (Public Domain)'
ATTR_LAKE = 'Chennai Metropolitan Water Supply and Sewerage Board via OpenCity.in (Public Domain)'
ATTR_AIR = 'Air quality: CAMS ENSEMBLE data provider (Copernicus Atmosphere Monitoring Service) via Open-Meteo.com'
ATTR_RIVER = 'River discharge: GloFAS via Open-Meteo.com'
SOURCES = []
def add(id,title,city,licence,attribution,**kwargs):
    SOURCES.append(dict(id=id,title=title,city=city,licence=licence,attribution=attribution,mode='static snapshot',status='NOT FETCHED',records_in=None,records_out=None,retrieved_at=None,**kwargs))
add('pin_directory','All India Pincode Directory','chennai,chandigarh','GODL-India','Department of Posts, Government of India, All India Pincode Directory (data.gov.in), Government Open Data License - India, via community mirror',url=PIN_URL,pin='d817d3e652e8167a70507350d9a8e4acda9113ef',expected_sha256='84af12fa29adddedfa9addcf46546000d89d2e2899b2993dc88050fafc8861e2',extension='csv',use='Postal reference points; Delhi is excluded from all updates.')
for id,city,file,title,count,sha in [
 ('che_cma','chennai','CMA.geojson','Chennai metropolitan outline',1,'89e81f8309a40ea9f24cf5e35c832b75ed937b65b111389d8ed8df4931804ad7'),
 ('che_wards','chennai','Wards.geojson','Chennai wards',201,'2dff80b6f514e644b9a428696909216e9d22aedd07c8ebab33192ec9e3cb1ab2'),
 ('chd_boundary','chandigarh','Chandigarh_Boundary.geojson','Chandigarh boundary',1,'47b39133b1f349b7afe74f6be6dc56dfe2cafa901939365e518e81e60e03e679'),
 ('chd_sectors','chandigarh','Chandigarh_Sectors.geojson','Chandigarh sectors',63,'06c17c07e07c2999d684feac37e360d103d2f2d5e478563dff4418dc2718e995')]:
    add(id,title,city,'CC BY-SA 2.5 India',ATTR_DM[city],url=DM+'/'+city.title()+'/'+file,attribution_url='https://github.com/datameet/Municipal_Spatial_Data/tree/'+DM_COMMIT+'/'+city.title(),pin=DM_COMMIT,expected_count=count,expected_sha256=sha,extension='geojson',use='Map scenario boundaries and coordinate validation')
for id,title,resource in [
 ('che_inundation_points','Inundation depth points','ceddf53f-03c0-4866-8ba8-5e84c8007a85'),
 ('che_flood_points_2015','Flooding points in 2015','80ed2fa7-1150-4f55-8125-682ab55282ac'),
 ('che_flood_hazard','Flood hazard zones','e61afe07-0f52-4be9-bdf3-5eb0f62b2ed6'),
 ('che_flood_zone_2015','2015 inundation zone','7cb3cecf-a95a-4786-8032-9c7417655d24')]:
    add(id,title,'chennai','Public Domain',ATTR_FLOOD if id!='che_flood_zone_2015' else 'chennaifloodsdss.in via OpenCity.in (Public Domain)',resource_id=resource,url='https://data.opencity.in/api/3/action/resource_show?id='+resource,extension='kml',source_last_updated='2024-01-10' if id=='che_flood_zone_2015' else '2025-11-25',use='Historical flood exposure, never an operational warning')
CAPACITIES = {'poondi':3231,'puzhal':3300,'chembarambakkam':3645,'cholavaram':1081,'kannankottai':500,'veeranam':1465}
for id,name,resource in [
 ('poondi','Poondi','8b0c0edc-4204-4f0f-8dc7-2db4817af04f'),('cholavaram','Cholavaram','20dc9876-ef1d-4cf1-9c42-f9d6c1f137db'),('chembarambakkam','Chembarambakkam','db41b1a4-5746-46d0-a006-e8fe2b1545a9'),('veeranam','Veeranam','a2f9aaad-7ac2-4a01-90d6-801eeef7d4b6'),('kannankottai','Kannankottai-Thervoy Kandigai','e0355257-d2d9-48be-a31e-6596a5fcdc07'),('puzhal','Puzhal (Red Hills)','febf2951-71eb-4807-9a06-246dadc1ef04')]:
    add('lake_'+id,name+' historical storage','chennai','Public Domain',ATTR_LAKE,resource_id=resource,url='https://data.opencity.in/api/3/action/resource_show?id='+resource,extension='csv',source_last_updated='2025-11-27',use='Historical monthly reservoir storage',reservoir_name=name)
BBOX = {'chennai':(12.8315,79.9839,13.3124,80.3653),'chandigarh':(30.6449,76.6850,30.8150,76.8690)}
for city in BBOX:
    add('facilities_'+city,city.title()+' facilities',city,'ODbL','©️ OpenStreetMap contributors (ODbL)',url='https://overpass-api.de/api/interpreter',extension='json',use='Nearby facility reference points; availability is unknown')
EVALUATED = [
 ('Chandigarh wards','Duplicate ward 5, reserve polygon, missing and duplicated population values; sectors used instead.'),
 ('Chennai Wards-2008','Pre-2011 boundaries; excluded.'),('Princeton / Stanford Chandigarh shapefiles','Access restricted.'),
 ('Census 2011 ward data','Identifiers do not match shipped layers; no formula requires it.'),
 ('GCC Budget 2026-27','PDF; link only: https://data.opencity.in/dataset/gcc-budget-2026-27'),
 ('GCC Relief Centres','October 2024 PDF; link only: https://data.opencity.in/dataset/gcc-relief-centres'),
 ('GCC stormwater base maps','PDF; link only, not parsed.'),('Return-period flood KMLs','Out of scope.'),
 ('GCC GIS REST server','Availability and licence unconfirmed.'),('Smart Cities portal','No Chandigarh catalogue enumerated.'),
 ('Complaint datasets','No verified open complaint data supplied; existing records retained, no synthetic operational reports added.'),
 ('AQICN','Requires token and separate terms; existing Delhi integration unchanged.'),
 ('GCC fire stations','Optional; no licence stated, not redistributed.'),('GCC health centres','Optional, not integrated; coordinate columns not verified.'),
 ('GCC flood hotspots 2020','Optional; not integrated.'),('CPCB data.gov.in','Optional; no verified API resource/key configured for this integration.')]
REFERENCE = {
 '160002':(30.69136,76.79257),'160003':(30.67653,76.79478),'160009':(30.74431,76.79504),'160011':(30.75672,76.78575),'160014':(30.75769,76.76861),'160017':(30.74208,76.78336),'160019':(30.72506,76.80428),'160036':(30.73458,76.75236),'160047':(30.69631,76.76903),
 '600001':(13.09284,80.28763),'600002':(13.07446,80.26989),'600004':(13.03254,80.26939),'600006':(13.05217,80.25179),'600017':(13.04293,80.23854),'600020':(13.00103,80.25731),'600028':(13.02458,80.26062),'600040':(13.08774,80.22164),'600042':(12.98264,80.22164),'600083':(13.03681,80.22707)}
EXPECTED = {'160009':['8','9'],'160011':['10','11'],'160014':['14'],'160017':['17'],'160019':['6','19','26','26E','27'],'160036':['36','40'],'160047':['47','48'],'600001':['ROYAPURAM'],'600002':['ROYAPURAM','TEYNAMPET'],'600004':['TEYNAMPET'],'600006':['TEYNAMPET'],'600017':['KODAMBAKKAM','TEYNAMPET'],'600020':['ADYAR'],'600028':['ADYAR'],'600040':['ANNANAGAR'],'600042':['ADYAR','PERUNGUDI'],'600083':['KODAMBAKKAM']}
ZONE_COUNTS = dict(zip(['THIRUVOTTIYUR','MANALI','MADHAVARAM','TONDIARPET','ROYAPURAM','THIRU-VI-KA-NAGAR','AMBATTUR','ANNANAGAR','TEYNAMPET','KODAMBAKKAM','VALASARAVAKKAM','ALANDUR','ADYAR','PERUNGUDI','SOZHINGANALLUR'],[14,7,12,15,15,15,15,15,18,16,13,12,13,11,9]))
