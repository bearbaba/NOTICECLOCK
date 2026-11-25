import hashlib
import json


def seal(data,cert):
    data={k:v for k,v in data.items() if k!='input_sha256'}
    data["input_sha256"]=hashlib.sha256(json.dumps(data,sort_keys=True).encode("utf-8")).hexdigest()
    return data,dict(cert,case_id=data["case_id"],input_sha256=data["input_sha256"])


def mock_view(monkeypatch, records, protocol):
    import genlayer as gl
    class View:
        def view(self): return self
        def get_protocol_version(self): return protocol
        def get_case(self,cid): return json.dumps(records[cid][0]) if cid in records else ""
        def get_certificate(self,cid): return json.dumps(records[cid][1]) if cid in records else ""
    monkeypatch.setattr(gl.contract,"get_at",lambda _:View())

def setup(vm,deploy,alice,bob,monkeypatch):
    c=deploy("contracts/DeadlineLedger.py","0x"+"9"*40)
    from genlayer.types import Address
    owner=Address(alice).as_hex.lower()
    other=Address(bob).as_hex.lower()
    records={}
    for cid,deadline,actor in (("initial","2026-11-10",owner),("extended","2026-11-12",other),("shorter","2026-11-09",owner),("bad","2026-11-13",owner)):
        records[cid]=seal({"case_id":cid,"owner":actor,"event_date":"2026-11-02","event_kind":"DELIVERY" if cid=="bad" else "RECEIPT","holidays":["2026-11-05"]},{"status":"COMPILED","deadline":deadline})
    mock_view(monkeypatch,records,"noticeclock-v2")
    vm.sender=alice
    c.open_obligation("obligation","initial",other)
    return c,records,other


def test_extension_and_filing_lifecycle(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch):
    vm=direct_vm
    c,records,other=setup(vm,direct_deploy,direct_alice,direct_bob,monkeypatch)
    with vm.expect_revert("Counterparty"):
        c.accept_obligation("obligation")
    vm.sender=direct_bob
    c.accept_obligation("obligation")
    c.propose_extension("obligation","ext","extended")
    with vm.expect_revert("Other signer"):
        c.resolve_extension("obligation","ext",True)
    vm.sender=direct_charlie
    with vm.expect_revert("Unauthorized"):
        c.resolve_extension("obligation","ext",True)
    vm.sender=direct_alice
    with vm.expect_revert("settled revision"):
        c.file_notice("obligation","n1","2026-11-11","Notice reference")
    c.resolve_extension("obligation","ext",True)
    rec=json.loads(c.get_obligation("obligation"))
    assert rec["revision"]==2 and rec["active_deadline"]=="2026-11-12"
    assert rec["history"][0]["deadline"]=="2026-11-10"
    c.file_notice("obligation","n1","2026-11-11","Notice reference")
    with vm.expect_revert("Counterparty"):
        c.resolve_notice("obligation","n1",True)
    vm.sender=direct_bob
    c.resolve_notice("obligation","n1",True)
    assert json.loads(c.get_notice("n1"))["status"]=="ON_TIME"
    with vm.expect_revert("Open obligation"):
        c.propose_extension("obligation","again","extended")


def test_reject_stale_shorter_wrong_trigger_and_duplicate(direct_vm,direct_deploy,direct_alice,direct_bob,monkeypatch):
    vm=direct_vm
    c,records,other=setup(vm,direct_deploy,direct_alice,direct_bob,monkeypatch)
    with vm.expect_revert("Duplicate"):
        c.open_obligation("second","initial",other)
    vm.sender=direct_bob
    c.accept_obligation("obligation")
    vm.sender=direct_alice
    with vm.expect_revert("later"):
        c.propose_extension("obligation","ext","shorter")
    with vm.expect_revert("preserve frozen"):
        c.propose_extension("obligation","ext","bad")
    with vm.expect_revert("Invalid"):
        c.file_notice("obligation","n1","2026-02-30","test")
    c.file_notice("obligation","n1","2026-11-11","Late evidence")
    vm.sender=direct_bob
    c.resolve_notice("obligation","n1",True)
    assert json.loads(c.get_obligation("obligation"))["status"]=="LATE"


def test_tampered_source_and_review_fail_closed(direct_vm,direct_deploy,direct_alice,direct_bob,monkeypatch):
    c,records,other=setup(direct_vm,direct_deploy,direct_alice,direct_bob,monkeypatch)
    records["tamper"]=seal(dict(records["initial"][0],case_id="tamper"),{"status":"COMPILED","deadline":"2026-11-10"})
    # Corrupt the hash link without changing the source.
    records["tamper"][1]["input_sha256"]="wrong"
    with direct_vm.expect_revert("binding mismatch"):
        c.open_obligation("tamper","tamper",other)
    data={k:v for k,v in records["initial"][0].items() if k!="input_sha256"}
    records["review"]=seal(dict(data,case_id="review"),{"status":"REVIEW","deadline":""})
    with direct_vm.expect_revert("Compiled deadline"):
        c.open_obligation("review","review",other)
