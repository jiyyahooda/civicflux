import yaml
from fastapi import HTTPException
from project_paths import CONFIG

def cities():
    from backend.scope import current
    scope=current()
    rows=[yaml.safe_load(p.read_text(encoding='utf-8')) for p in sorted((CONFIG/'cities').glob('*.yaml'))]
    if not scope:return rows
    rows=[c for c in rows if c['id']==scope['city_id']]
    for c in rows:
        c['name']=scope['area_name'].split(',')[0]+' · '+scope['pincode'];c['pincode']=scope['pincode']
        c['map_reference']={'latitude':scope['latitude'],'longitude':scope['longitude'],'zoom':14} if scope['latitude'] is not None else None
        c['coordinate_source']=scope['coordinate_source']
    return rows
def city(identifier):
    item=next((c for c in cities() if c['id']==identifier),None)
    if item is None: raise HTTPException(404,'Unknown city')
    return item
