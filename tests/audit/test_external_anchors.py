import json
from app.core.anchors import initialize,export_anchor,verify_anchor
from app.config import settings
from app.core.audit import AuditLogger

def test_external_anchor_restore_and_forgery(tmp_path):
    directory=tmp_path/"protected";initialize(directory)
    AuditLogger.log_event("test","auditor","ANCHOR","EXECUTED","fixture")
    anchor=export_anchor(directory)
    restored=tmp_path/"restored.jsonl";restored.write_bytes(settings.AUDIT_LOG_PATH.read_bytes())
    assert verify_anchor(anchor,directory/"trusted-public.key",restored)
    restored.write_text("",encoding="utf-8")
    assert not verify_anchor(anchor,directory/"trusted-public.key",restored)
    fake=tmp_path/"other";initialize(fake)
    assert not verify_anchor(anchor,fake/"trusted-public.key",settings.AUDIT_LOG_PATH)
