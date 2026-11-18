import pytest
from pydantic import ValidationError
from shodh.schemas.problem import ProblemCreateRequest,ProblemUpdateRequest
def payload(**kwargs):
 d={"slug":"two-sum","title":"Two Sum","statement_md":"Find pair with target sum.","input_format":"Read n and target","output_format":"Print answer"};d.update(kwargs);return d
def test_slug_normalized():
 assert ProblemCreateRequest(**payload(slug=" Two-Sum ")).slug=="two-sum"
@pytest.mark.parametrize("slug",["Bad slug","a--b","-x","x-","UPPER"])
def test_invalid_slug(slug):
 with pytest.raises(ValidationError):ProblemCreateRequest(**payload(slug=slug))
@pytest.mark.parametrize("field,value",[("time_limit_ms",99),("memory_limit_mb",15),("points",0)])
def test_limits(field,value):
 with pytest.raises(ValidationError):ProblemCreateRequest(**payload(**{field:value}))
def test_patch_only_active():
 assert ProblemUpdateRequest(is_active=False).is_active is False
 with pytest.raises(ValidationError):ProblemUpdateRequest(title="oops")
