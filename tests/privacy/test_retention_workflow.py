import pytest
from app.core.retention import inventory,quarantine,restore,apply_reviewed

def test_quarantine_restores_and_removal_requires_review(tmp_path):
    root=tmp_path/"repo";(root/"data").mkdir(parents=True)
    history=root/"data/execution_traces.jsonl";history.write_text("sensitive fixture",encoding="utf-8")
    folder=tmp_path/"private";quarantine(root,folder)
    assert b"sensitive fixture" not in (folder/"history.enc").read_bytes()
    restored=tmp_path/"restored";restore(folder,restored)
    assert (restored/"data/execution_traces.jsonl").read_text()=="sensitive fixture"
    with pytest.raises(ValueError):apply_reviewed(root,folder)
    assert history.exists()
    history.write_text("changed",encoding="utf-8")
    with pytest.raises(ValueError):apply_reviewed(root,folder,True)
    history.write_text("sensitive fixture",encoding="utf-8")
    assert apply_reviewed(root,folder,True)["removed"]==1
    assert not history.exists()


def test_bundle_tampering_is_rejected(tmp_path):
    root=tmp_path/"repo";(root/"data").mkdir(parents=True)
    (root/"data/audit_log.jsonl").write_text("fixture",encoding="utf-8")
    folder=tmp_path/"private";quarantine(root,folder)
    data=bytearray((folder/"history.enc").read_bytes());data[-1]^=1;(folder/"history.enc").write_bytes(data)
    with pytest.raises(ValueError):restore(folder,tmp_path/"restore")
