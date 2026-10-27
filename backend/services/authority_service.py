"""Application locality queues. These are not government delivery endpoints."""
from backend.db.connection import connection
from backend.services.city_service import city
ZONES=('north','north_west','south','south_west','south_east','north_east','east','west','central')

def authorities(identifier):
    configuration=city(identifier)
    with connection() as db:
        for zone in ZONES:
            db.execute('INSERT OR IGNORE INTO authorities(id,city_id,locality,name) VALUES (?,?,?,?)',
                (identifier+':'+zone,identifier,zone,zone.replace('_',' ').title()+' Authority'))
        return [dict(row) for row in db.execute('SELECT * FROM authorities WHERE city_id=? ORDER BY name',(identifier,))]

def assign(identifier,locality):
    if locality not in ZONES:raise ValueError('Unknown locality')
    authority=next(a for a in authorities(identifier) if a['locality']==locality)
    return {'authority_id':authority['id'],'authority_name':authority['name'],'locality':locality,
            'delivery_status':'local_queue','external_delivery':False}
