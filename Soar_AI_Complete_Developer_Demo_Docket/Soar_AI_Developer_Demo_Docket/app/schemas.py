from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
from datetime import datetime
import re
class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
def utc(value):
 if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',value):raise ValueError('Use canonical YYYY-MM-DDTHH:MM:SSZ timestamps; fractional seconds are not part of this demo contract')
 d=datetime.fromisoformat(value.replace('Z','+00:00'))
 if not value.endswith('Z') or d.utcoffset().total_seconds()!=0:raise ValueError('UTC ISO-8601 with Z required')
 return value
class Authorization(Strict):
 status:Literal['ENABLED','DISABLED','REVOKED']
 issued_by:str
 issued_at:str
 expires_at:str
 scope:Literal['GROUND_PREPARATION_ONLY']
 _dates=field_validator('issued_at','expires_at')(utc)
class Event(Strict):
 schema_version:Literal['1.0']
 event_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,80}$')
 source_system:Literal['SIMULATED_MCC_ADAPTER']
 source_sequence:int=Field(ge=1)
 operator_id:str
 aircraft_id:str
 flight_id:str
 next_flight_id:str
 destination:str=Field(pattern=r'^[A-Z]{3}$')
 occurred_at:str
 received_at:str
 fault_code:str
 reported_symptom:str=Field(max_length=3000)
 crew_operational_status:str=Field(max_length=200)
 planning_authorization:Authorization
 safety_event_active:bool
 data_class:Literal['SYNTHETIC']
 note:str=Field(max_length=3000)
 _dates=field_validator('occurred_at','received_at')(utc)
 @model_validator(mode='after')
 def timing(self):
  if self.received_at<self.occurred_at:raise ValueError('received_at precedes occurred_at')
  return self
class Load(Strict):scenario_id:str='nominal'
class Analyze(Strict):mode:Literal['reference','ollama']='reference'
class Approve(Strict):
 case_version:int=Field(ge=1)
 plan_hash:str=Field(min_length=64,max_length=64)
 idempotency_key:str=Field(min_length=8,max_length=100)
class Update(Strict):
 source_sequence:int=Field(ge=2)
 destination:str|None=Field(default=None,pattern=r'^[A-Z]{3}$')
 planning_status:Literal['DISABLED','REVOKED']|None=None
 safety_event_active:bool|None=None
class Advance(Strict):
 clock_utc:str
 _date=field_validator('clock_utc')(utc)
class Outcome(Strict):
 source_system:Literal['SIMULATED_MAINTENANCE_SYSTEM']
 external_reference:str=Field(min_length=5,max_length=100)
 status:Literal['SERVICEABLE_RECORDED_EXTERNALLY','MAINTENANCE_CONTINUES']
 recorded_at:str
 note:str=Field(max_length=2000)
 _date=field_validator('recorded_at')(utc)
class SearchPlan(Strict):queries:list[str]=Field(min_length=1,max_length=3)
class Claim(Strict):
 text:str=Field(min_length=1,max_length=600)
 evidence_ids:list[str]=Field(min_length=1,max_length=8)
class ModelExplanation(Strict):
 summary:str=Field(min_length=1,max_length=1200)
 claims:list[Claim]=Field(min_length=1,max_length=6)
 unresolved_questions:list[str]=Field(max_length=8)
 dispatch_eligibility:Literal['UNKNOWN']
 preparation_only:Literal[True]

class FlightCreate(Strict):
 flight_id:str=Field(min_length=2,max_length=40,pattern=r'^[A-Za-z0-9_-]+$')
 operator_id:str=Field(default='SIM-AIR',min_length=2,max_length=40)
 aircraft_id:str=Field(min_length=2,max_length=40)
 display_number:str=Field(min_length=1,max_length=100)
 origin:str=Field(pattern=r'^[A-Z]{3}$')
 destination:str=Field(pattern=r'^[A-Z]{3}$')
 scheduled_out_utc:str
 scheduled_in_utc:str
 estimated_landing_utc:str
 estimated_inblock_utc:str
 other_turnaround_ready_utc:str
 dispatch_buffer_minutes:int=Field(ge=0,default=20)
 passengers:int=Field(ge=0,default=200)
 crew_ready:int=Field(ge=0,le=1,default=1)
 slot_confirmed:int=Field(ge=0,le=1,default=1)
 status:str=Field(default='SCHEDULED',max_length=40)
 source_basis:str=Field(default='User entered',max_length=200)
 data_class:Literal['SYNTHETIC','PUBLIC_REFERENCE']='SYNTHETIC'
 _dates=field_validator('scheduled_out_utc','scheduled_in_utc','estimated_landing_utc','estimated_inblock_utc','other_turnaround_ready_utc')(utc)

 @model_validator(mode='after')
 def validate_timing(self):
  if self.scheduled_out_utc>=self.scheduled_in_utc:raise ValueError('scheduled_out_utc must precede scheduled_in_utc')
  return self

class FlightUpdate(Strict):
 display_number:str|None=None
 origin:str|None=Field(default=None,pattern=r'^[A-Z]{3}$')
 destination:str|None=Field(default=None,pattern=r'^[A-Z]{3}$')
 scheduled_out_utc:str|None=None
 scheduled_in_utc:str|None=None
 estimated_landing_utc:str|None=None
 estimated_inblock_utc:str|None=None
 other_turnaround_ready_utc:str|None=None
 dispatch_buffer_minutes:int|None=Field(default=None,ge=0)
 passengers:int|None=Field(default=None,ge=0)
 crew_ready:int|None=Field(default=None,ge=0,le=1)
 slot_confirmed:int|None=Field(default=None,ge=0,le=1)
 status:str|None=None
 source_basis:str|None=None
 _dates=field_validator('scheduled_out_utc','scheduled_in_utc','estimated_landing_utc','estimated_inblock_utc','other_turnaround_ready_utc')(lambda v:utc(v) if v is not None else v)

