# { "Depends": "py-genlayer:kzybg95x1gn21dw72m7hyg0maaap04n4nx55j9yt6fkdqxtz6bz0" }
"""Cross-contract, two-party state machine; no caller-supplied certificate."""
import genlayer as gl
from genlayer.types import Address
from genlayer.storage import TreeMap
import hashlib
import json
import re


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def require_id(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise gl.vm.UserError("Invalid ID")


def sender():
    return gl.message.sender_address.as_hex.lower()


def checked_address(value):
    addr = Address(value)
    if addr.as_hex.lower() == "0x" + "0" * 40:
        raise gl.vm.UserError("Zero address prohibited")
    return addr


def pair_member(rec, actor):
    return actor in (rec["owner"], rec["counterparty"])


def source_pair(anchor, protocol, case_id):
    require_id(case_id)
    view = gl.contract.get_at(anchor).view()
    if view.get_protocol_version() != protocol:
        raise gl.vm.UserError("Incompatible anchor protocol")
    raw = view.get_case(case_id)
    proof = view.get_certificate(case_id)
    if not raw or not proof:
        raise gl.vm.UserError("Missing frozen case or certificate")
    data, cert = json.loads(raw), json.loads(proof)
    actual = digest({k:v for k,v in data.items() if k != "input_sha256"})
    if data.get("case_id") != case_id or cert.get("case_id") != case_id or data.get("input_sha256") != actual or cert.get("input_sha256") != actual:
        raise gl.vm.UserError("Certificate binding mismatch")
    return data, cert

def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return False
    y,m,d = [int(x) for x in value.split("-")]
    if not 2000 <= y <= 2199 or not 1 <= m <= 12:
        return False
    leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
    return 1 <= d <= (31,29 if leap else 28,31,30,31,30,31,31,30,31,30,31)[m-1]


class DeadlineLedger(gl.contract.Contract):
    anchor: Address
    obligations: TreeMap[str,str]
    proposals: TreeMap[str,str]
    filings: TreeMap[str,str]
    used_cases: TreeMap[str,str]

    def __init__(self, anchor_address: str):
        self.anchor = checked_address(anchor_address)

    @gl.public.view
    def get_anchor_address(self) -> str:
        return self.anchor.as_hex

    @gl.public.view
    def get_protocol_version(self) -> str:
        return "deadline-ledger-v2"

    def _load(self, obligation_id):
        raw = self.obligations.get(obligation_id,"")
        if not raw:
            raise gl.vm.UserError("Unknown obligation")
        return json.loads(raw)

    def _save(self, record):
        self.obligations[record["obligation_id"]] = json.dumps(record,sort_keys=True)

    def _certificate(self, case_id):
        data,cert = source_pair(self.anchor,"noticeclock-v2",case_id)
        if cert.get("status") != "COMPILED" or not valid_date(cert.get("deadline")) or not valid_date(data.get("event_date")) or cert["deadline"] < data["event_date"]:
            raise gl.vm.UserError("Compiled deadline required")
        return data,cert

    @gl.public.write
    def open_obligation(self, obligation_id: str, case_id: str, counterparty: str) -> None:
        require_id(obligation_id)
        if self.obligations.get(obligation_id,"") or self.used_cases.get(case_id,""):
            raise gl.vm.UserError("Duplicate obligation or certificate")
        other = checked_address(counterparty).as_hex.lower()
        data,cert = self._certificate(case_id)
        actor = sender()
        if actor != data["owner"] or actor == other:
            raise gl.vm.UserError("Owner and distinct counterparty required")
        rec = {"obligation_id":obligation_id,"owner":actor,"counterparty":other,
               "initial_case":case_id,"active_case":case_id,"active_deadline":cert["deadline"],
               "event_date":data["event_date"],"event_kind":data["event_kind"],
               "holidays":data["holidays"],"revision":1,"status":"AWAITING_ACCEPTANCE",
               "pending_extension":"","filing_id":"","history":[{"case_id":case_id,"deadline":cert["deadline"],"input_sha256":cert["input_sha256"]}]}
        self.used_cases[case_id] = obligation_id
        self._save(rec)

    @gl.public.write
    def accept_obligation(self, obligation_id: str) -> None:
        rec = self._load(obligation_id)
        if sender()!=rec["counterparty"] or rec["status"]!="AWAITING_ACCEPTANCE":
            raise gl.vm.UserError("Counterparty must accept a new obligation")
        rec["status"]="OPEN"
        self._save(rec)

    @gl.public.write
    def propose_extension(self, obligation_id: str, proposal_id: str, replacement_case: str) -> None:
        require_id(proposal_id)
        rec = self._load(obligation_id)
        actor=sender()
        if not pair_member(rec,actor) or rec["status"]!="OPEN" or rec["pending_extension"]:
            raise gl.vm.UserError("Open obligation and no pending extension required")
        if self.proposals.get(proposal_id,"") or self.used_cases.get(replacement_case,"") or rec["revision"]>=32:
            raise gl.vm.UserError("Duplicate proposal or certificate, or revision cap")
        data,cert=self._certificate(replacement_case)
        if data["owner"]!=actor or data["event_date"]!=rec["event_date"] or data["event_kind"]!=rec["event_kind"] or data["holidays"]!=rec["holidays"]:
            raise gl.vm.UserError("Replacement must preserve frozen trigger and calendar")
        if cert["deadline"]<=rec["active_deadline"]:
            raise gl.vm.UserError("Extension must move deadline later")
        proposal={"proposal_id":proposal_id,"obligation_id":obligation_id,"proposed_by":actor,
                  "base_revision":rec["revision"],"case_id":replacement_case,"deadline":cert["deadline"],
                  "input_sha256":cert["input_sha256"],"status":"PENDING","resolved_by":""}
        self.proposals[proposal_id]=json.dumps(proposal,sort_keys=True)
        self.used_cases[replacement_case]=obligation_id
        rec["pending_extension"]=proposal_id
        self._save(rec)

    @gl.public.write
    def resolve_extension(self, obligation_id: str, proposal_id: str, approve: bool) -> None:
        rec=self._load(obligation_id)
        raw=self.proposals.get(proposal_id,"")
        if not raw or rec["pending_extension"]!=proposal_id or rec["status"]!="OPEN":
            raise gl.vm.UserError("No matching pending extension")
        p=json.loads(raw)
        actor=sender()
        if not pair_member(rec,actor) or p["status"]!="PENDING" or p["base_revision"]!=rec["revision"]:
            raise gl.vm.UserError("Unauthorized or stale extension")
        if approve and actor==p["proposed_by"]:
            raise gl.vm.UserError("Other signer must approve")
        p["status"]="APPROVED" if approve else "DECLINED"
        p["resolved_by"]=actor
        if approve:
            rec["active_case"]=p["case_id"]
            rec["active_deadline"]=p["deadline"]
            rec["revision"]+=1
            rec["history"].append({"case_id":p["case_id"],"deadline":p["deadline"],"input_sha256":p["input_sha256"]})
        rec["pending_extension"]=""
        self.proposals[proposal_id]=json.dumps(p,sort_keys=True)
        self._save(rec)

    @gl.public.write
    def file_notice(self, obligation_id: str, filing_id: str, observed_date: str, evidence: str) -> None:
        require_id(filing_id)
        rec=self._load(obligation_id)
        if sender()!=rec["owner"] or rec["status"]!="OPEN" or rec["pending_extension"]:
            raise gl.vm.UserError("Owner must file against an open settled revision")
        if self.filings.get(filing_id,"") or not valid_date(observed_date) or observed_date<rec["event_date"] or not evidence.strip() or len(evidence)>1500:
            raise gl.vm.UserError("Invalid or duplicate notice")
        f={"filing_id":filing_id,"obligation_id":obligation_id,"observed_date":observed_date,"evidence":evidence,
           "evidence_sha256":digest(evidence),"revision":rec["revision"],"case_id":rec["active_case"],
           "deadline":rec["active_deadline"],"status":"PENDING"}
        self.filings[filing_id]=json.dumps(f,sort_keys=True)
        rec["filing_id"]=filing_id
        rec["status"]="NOTICE_PENDING"
        self._save(rec)

    @gl.public.write
    def resolve_notice(self, obligation_id: str, filing_id: str, accept: bool) -> None:
        rec=self._load(obligation_id)
        if sender()!=rec["counterparty"] or rec["status"]!="NOTICE_PENDING" or rec["filing_id"]!=filing_id:
            raise gl.vm.UserError("Counterparty must resolve pending notice")
        f=json.loads(self.filings[filing_id])
        f["status"]=("ON_TIME" if f["observed_date"]<=f["deadline"] else "LATE") if accept else "DISPUTED"
        f["resolved_by"]=sender()
        rec["status"]=f["status"]
        self.filings[filing_id]=json.dumps(f,sort_keys=True)
        self._save(rec)

    @gl.public.view
    def get_obligation(self, obligation_id: str) -> str:
        return self.obligations.get(obligation_id,"")

    @gl.public.view
    def get_extension(self, proposal_id: str) -> str:
        return self.proposals.get(proposal_id,"")

    @gl.public.view
    def get_notice(self, filing_id: str) -> str:
        return self.filings.get(filing_id,"")
