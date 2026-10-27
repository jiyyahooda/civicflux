"""City-scoped public context and verified administrative records."""
from datetime import datetime, timezone
from pathlib import Path
import json
from backend.services.city_service import city
from backend.db import repository as repo
from project_paths import CONFIG

SOURCES = {
 'delhi': {'police': 'https://traffic.delhipolice.gov.in/en/news-alertadvisory/advisory', 'municipal': 'https://mcdonline.nic.in/'},
 'chennai': {'police': 'https://gctp.in/', 'municipal': 'https://chennaicorporation.gov.in/'},
 'chandigarh': {'police': 'https://portal.chandigarhpolice.gov.in/', 'municipal': 'https://mcchandigarh.gov.in/'},
}

def postal(identifier):
    city(identifier)
    return json.loads((CONFIG/'postal_reference.json').read_text(encoding='utf-8'))[identifier]

def verify_pin(identifier, pin):
    entries = [row for row in postal(identifier)['records'] if row['pin'] == pin]
    if not entries:
        from fastapi import HTTPException
        raise HTTPException(422, 'PIN is not listed for this city in the verified postal reference. Choose a listed postal area or request a reference update.')
    return entries

def active(item):
    now=datetime.now(timezone.utc)
    try:
        start=datetime.fromisoformat(item['valid_from']); end=datetime.fromisoformat(item['valid_until'])
        return start.tzinfo is not None and end.tzinfo is not None and start<=now<=end
    except (ValueError,KeyError,TypeError):return False

def context(identifier):
    configuration=city(identifier)
    from backend.api.references import reference
    from backend.api.resources import pools_for
    snapshots=json.loads((CONFIG/'official_notices.json').read_text(encoding='utf-8'))
    notices=[n for n in [*repo.all_records('civic_notice'),*snapshots] if n['city_id']==identifier and active(n)]
    inventory=[n for n in repo.all_records('resource_inventory') if n['city_id']==identifier and active(n)]
    publications=[n for n in repo.all_records('publication') if n['city_id']==identifier]
    reports=[n for n in repo.all_records('complaint') if n['city_id']==identifier]
    confirmed=[n for n in reports if n.get('validation')=='valid' and n['status']!='closed']
    return {'city_id':identifier,'city_name':configuration['name'],'checked_at':repo.now(),
      'reference':reference(identifier), 'operational_pools':pools_for(identifier,public=True),
      'sources':SOURCES[identifier], 'notices':notices, 'publications':publications,
      'inventory':inventory[:1], 'confirmed_active_count':len(confirmed),
      'official_notices_status':'approved_imports_only',
      'official_notices_note':'No automatic police feed is configured. Open the official source for the latest notices. Imported notices expire at their recorded end time.',
      'resource_note':'Operational availability requires a current, authorized roster. Published annual budgets and historical staffing are reference information only.'}
