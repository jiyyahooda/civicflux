"""Request-local postal jurisdiction. No client parameter grants authority."""
from contextvars import ContextVar
from fastapi import HTTPException
area=ContextVar('civicflux_area',default=None)
def current():return area.get()
def pin_of(item):return item.get('pincode') or item.get('postal_code') or item.get('inputs',{}).get('pincode')
def allows(item):
 scope=current()
 return not scope or (item.get('city_id')==scope['city_id'] and pin_of(item)==scope['pincode'])
def bind(item):
 scope=current()
 if not scope:return item
 if item.get('city_id',scope['city_id'])!=scope['city_id'] or pin_of(item) not in (None,scope['pincode']):raise HTTPException(403,'Outside your assigned area')
 return {**item,'city_id':scope['city_id'],'pincode':scope['pincode']}
