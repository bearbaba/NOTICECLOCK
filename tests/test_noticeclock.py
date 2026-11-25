import json
import copy
import pytest

CLAUSE = "The notice must be submitted within five business days after receipt."
PATTERN = r"(?s).*Extract ONE unconditional notice deadline.*"
RULE = {"status":"READY","count_token":"five","basis":"BUSINESS","trigger":"RECEIPT","counting":"EXCLUDE_EVENT","quote":CLAUSE}

def mock(vm, data):
    vm.clear_mocks()
    vm.mock_llm(PATTERN, json.dumps(json.dumps(data)))

def setup(vm, deploy, alice, event="RECEIPT", date="2026-11-02", holidays='["2026-11-05"]', clause=CLAUSE):
    c = deploy("contracts/NoticeClock.py")
    vm.sender = alice
    c.freeze_case("case-a", clause, event, date, holidays)
    return c

def test_real_calculation_and_immutability(direct_vm, direct_deploy, direct_alice, direct_bob):
    c = setup(direct_vm, direct_deploy, direct_alice)
    frozen = c.get_case("case-a")
    assert c.check_date("case-a","2026-11-10") == "NOT_COMPILED"
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only case owner"):
        c.compile_deadline("case-a")
    direct_vm.sender = direct_alice
    mock(direct_vm, RULE)
    c.compile_deadline("case-a")
    assert direct_vm.run_validator() is True
    certificate = json.loads(c.get_certificate("case-a"))
    assert certificate["status"] == "COMPILED" and certificate["deadline"] == "2026-11-10"
    assert certificate["input_sha256"] == json.loads(frozen)["input_sha256"]
    assert c.check_date("case-a","2026-11-10") == "ON_TIME"
    assert c.check_date("case-a","2026-11-11") == "LATE"
    assert c.check_date("case-a","2026-11-01") == "BEFORE_TRIGGER"
    assert c.check_date("case-a","2026-02-30") == "INVALID_DATE"
    with direct_vm.expect_revert("already exists"):
        c.compile_deadline("case-a")
    with direct_vm.expect_revert("duplicate"):
        c.freeze_case("case-a", CLAUSE, "RECEIPT", "2026-11-02", "[]")
    assert c.get_case("case-a") == frozen

def test_validator_rejects_changed_facts(direct_vm,direct_deploy,direct_alice):
    c = setup(direct_vm,direct_deploy,direct_alice)
    mock(direct_vm,RULE)
    c.compile_deadline("case-a")
    for change in ({"count_token":"six"},{"basis":"CALENDAR"},{"trigger":"DELIVERY"},{"counting":"INCLUDE_EVENT"},{"quote":"five business days"}):
        mock(direct_vm,dict(RULE,**change))
        assert direct_vm.run_validator() is False
    mock(direct_vm,{"status":"REVIEW"})
    assert direct_vm.run_validator() is False

def test_trigger_mismatch_and_review(direct_vm,direct_deploy,direct_alice):
    c = setup(direct_vm,direct_deploy,direct_alice,event="DELIVERY")
    mock(direct_vm,RULE)
    c.compile_deadline("case-a")
    assert json.loads(c.get_certificate("case-a"))["reason"] == "TRIGGER_MISMATCH"
    assert c.check_date("case-a","2026-11-10") == "REVIEW"
    c.freeze_case("ambiguous","Respond promptly.","RECEIPT","2026-11-02","[]")
    mock(direct_vm,{"status":"REVIEW"})
    c.compile_deadline("ambiguous")
    assert direct_vm.run_validator() is True
    assert json.loads(c.get_certificate("ambiguous"))["deadline"] == ""

def test_leap_calendar_and_invalid_inputs(direct_vm,direct_deploy,direct_alice):
    c = direct_deploy("contracts/NoticeClock.py")
    direct_vm.sender = direct_alice
    clause = "Respond within 2 calendar days after receipt."
    with direct_vm.expect_revert("Invalid event date"):
        c.freeze_case("bad",clause,"RECEIPT","2026-02-29","[]")
    with direct_vm.expect_revert("Invalid event date"):
        c.freeze_case("bad",clause,"RECEIPT","2028-02-28",'["2028-03-01","2028-03-01"]')
    c.freeze_case("leap",clause,"RECEIPT","2028-02-28","[]")
    mock(direct_vm,dict(RULE,count_token="2",basis="CALENDAR",quote=clause))
    c.compile_deadline("leap")
    assert json.loads(c.get_certificate("leap"))["deadline"] == "2028-03-01"
