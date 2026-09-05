"""Template for authoritative geography ingestion.

Map an official source file into the canonical Core Geography columns. Never infer missing codes from names alone without a reviewed crosswalk.
"""
CANONICAL_COLUMNS = [
 'place_id','place_type','name','parent_place_id','state_code','state_name',
 'district_code','district_name','subdistrict_code','subdistrict_name',
 'block_code','block_name','panchayat_code','panchayat_name','village_code','village_name',
 'latitude','longitude','valid_from','valid_to','source_id','quality_class','record_status'
]
