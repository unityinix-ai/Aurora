from well.ledger import WellLedger
EVIDENCE={"observed","reported","inferred","disputed","unverified"}
class WellService:
 def __init__(self,ledger:WellLedger): self.ledger=ledger
 def add_observation(self,*,owner_id,source_ref,text,evidence_status="reported",actor="user"):
  if not all(isinstance(x,str) and x.strip() for x in (owner_id,source_ref,text)): raise ValueError("owner, source and text required")
  if evidence_status not in EVIDENCE: raise ValueError("unsupported evidence status")
  return self.ledger.append(aggregate_id="owner:"+owner_id,event_type="observation.recorded",actor=actor,payload={"owner_id":owner_id,"source_ref":source_ref,"text":text,"evidence_status":evidence_status})
 def propose_pattern(self,*,owner_id,title,summary,supporting_event_ids,derivation,confidence,counterexamples=None,actor="well-engine"):
  if not all(isinstance(x,str) and x.strip() for x in (owner_id,title,summary,derivation)): raise ValueError("required field missing")
  if not supporting_event_ids: raise ValueError("supporting observations required")
  if isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not 0<=confidence<=1: raise ValueError("confidence must be between 0 and 1")
  owned={e["event_id"] for e in self.ledger.list_events("owner:"+owner_id) if e["event_type"]=="observation.recorded"}
  if not set(supporting_event_ids)<=owned: raise ValueError("supporting observations must belong to owner")
  return self.ledger.append(aggregate_id="owner:"+owner_id,event_type="pattern.proposed",actor=actor,payload={"owner_id":owner_id,"title":title,"summary":summary,"supporting_event_ids":list(supporting_event_ids),"derivation":derivation,"confidence":float(confidence),"counterexamples":list(counterexamples or []),"status":"proposed"})
 def get_record(self,owner_id,event_id):
  return next((e for e in self.ledger.list_events("owner:"+owner_id) if e["event_id"]==event_id),None)
 def review_pattern(self,*,owner_id,pattern_event_id,status,reviewer,note=""):
  if status not in {"reviewed","rejected"}: raise ValueError("invalid review status")
  p=self.get_record(owner_id,pattern_event_id)
  if not p or p["event_type"]!="pattern.proposed": raise ValueError("pattern not found")
  return self.ledger.append(aggregate_id="owner:"+owner_id,event_type="pattern.reviewed",actor=reviewer,payload={"owner_id":owner_id,"pattern_event_id":pattern_event_id,"status":status,"note":note})
 def search(self,*,owner_id,query,limit=20):
  if not owner_id.strip() or not query.strip(): return []
  terms={x.casefold() for x in query.split() if len(x)>1}; events=self.ledger.list_events("owner:"+owner_id)
  reviews={e["payload"]["pattern_event_id"]:e["payload"]["status"] for e in events if e["event_type"]=="pattern.reviewed"}; out=[]
  for e in events:
   if e["event_type"] not in {"observation.recorded","pattern.proposed"}: continue
   p=e["payload"]; hay=" ".join(str(p.get(k,"")) for k in ("text","title","summary","source_ref")).casefold(); matched=sorted(t for t in terms if t in hay)
   if matched: out.append({"event":e,"matched_terms":matched,"review_status":reviews.get(e["event_id"],p.get("status","source")),"retrieval_method":"lexical-token-overlap-v1"})
  out.sort(key=lambda r:(len(r["matched_terms"]),r["event"]["seq"]),reverse=True); return out[:max(1,min(int(limit),100))]
