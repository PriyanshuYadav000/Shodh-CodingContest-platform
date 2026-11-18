import re
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field,field_validator
class ProblemCreateRequest(BaseModel):
 slug:str=Field(min_length=3,max_length=100)
 title:str=Field(min_length=3,max_length=180)
 statement_md:str=Field(min_length=10,max_length=50000)
 input_format:str=Field(min_length=1,max_length=10000)
 output_format:str=Field(min_length=1,max_length=10000)
 constraints_text:str|None=Field(default=None,max_length=10000)
 time_limit_ms:int=Field(default=2000,ge=100,le=30000)
 memory_limit_mb:int=Field(default=256,ge=16,le=2048)
 points:int=Field(default=100,ge=1,le=100000)
 @field_validator("slug")
 @classmethod
 def valid_slug(cls,v):
  v=v.strip().lower()
  if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",v):raise ValueError("Invalid slug format")
  return v
 @field_validator("title")
 @classmethod
 def trim_title(cls,v):
  v=v.strip()
  if len(v)<3:raise ValueError("Title too short")
  return v
class ProblemUpdateRequest(BaseModel):
 model_config=ConfigDict(extra="forbid")
 is_active:bool|None=None
class ProblemResponse(BaseModel):
 model_config=ConfigDict(from_attributes=True)
 id:UUID;contest_id:UUID;slug:str;title:str;statement_md:str;input_format:str;output_format:str
 constraints_text:str|None;time_limit_ms:int;memory_limit_mb:int;points:int;created_by:UUID
 is_active:bool;created_at:datetime;updated_at:datetime
class ProblemPageResponse(BaseModel):
 items:list[ProblemResponse];total:int;limit:int;offset:int
