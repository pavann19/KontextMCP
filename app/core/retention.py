"""Encrypted quarantine and manifest-checked, explicitly reviewed history removal."""
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

RUNTIME_NAMES=("enterprise_records.db","execution_traces.jsonl","audit_log.jsonl","audit_checkpoints.json")


def inventory(root):
    root=Path(root).resolve()
    rows=[]
    for name in RUNTIME_NAMES:
        path=root/"data"/name
        if path.is_file():
            value=path.read_bytes()
            rows.append({"path":path.relative_to(root).as_posix(),"size":len(value),"sha256":hashlib.sha256(value).hexdigest()})
    return {"version":1,"root":str(root),"files":rows,"destructive_action":"NONE; reviewed manifest required before removal"}


def quarantine(root,destination):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if destination.is_relative_to(root):raise ValueError("Quarantine must be outside the repository")
    destination.mkdir(parents=True,exist_ok=True)
    manifest=inventory(root)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
        for row in manifest["files"]:
            value=(root/row["path"]).read_bytes()
            if hashlib.sha256(value).hexdigest()!=row["sha256"]:raise ValueError("Runtime file changed; stop the application before export")
            archive.writestr(row["path"],value)
    if stream.tell()>128*1024*1024:raise ValueError("Use an offline database backup for history larger than 128 MiB")
    key=AESGCM.generate_key(bit_length=256);nonce=os.urandom(12)
    bundle=nonce+AESGCM(key).encrypt(nonce,stream.getvalue(),b"KontextMCP-retention-v1")
    with (destination/"history.enc").open("xb") as output:output.write(bundle)
    keypath=destination/"restore.key"
    with keypath.open("xb") as output:output.write(key)
    keypath.chmod(0o600)
    if os.name=="nt":
        import csv,subprocess
        sid=next(csv.reader(subprocess.check_output(["whoami","/user","/fo","csv","/nh"],text=True).strip().splitlines()))[1]
        subprocess.run(["icacls",str(keypath),"/inheritance:r","/grant:r",f"*{sid}:(F)"],capture_output=True,check=True)
    manifest["bundle_sha256"]=hashlib.sha256(bundle).hexdigest()
    with (destination/"review-manifest.json").open("x",encoding="utf-8") as output:json.dump(manifest,output,indent=2)
    return manifest


def restore(destination,output):
    destination=Path(destination);output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((destination/"review-manifest.json").read_text(encoding="utf-8"))
    bundle=(destination/"history.enc").read_bytes()
    if hashlib.sha256(bundle).hexdigest()!=manifest["bundle_sha256"]:raise ValueError("Quarantine bundle hash differs from reviewed manifest")
    plain=AESGCM((destination/"restore.key").read_bytes()).decrypt(bundle[:12],bundle[12:],b"KontextMCP-retention-v1")
    with zipfile.ZipFile(io.BytesIO(plain)) as archive:
        for row in manifest["files"]:
            target=(output/row["path"]).resolve()
            if not target.is_relative_to(output):raise ValueError("Invalid restore path")
            data=archive.read(row["path"])
            if hashlib.sha256(data).hexdigest()!=row["sha256"]:raise ValueError("History file hash mismatch")
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as stream:stream.write(data)
    return manifest


def apply_reviewed(root,destination,confirm_reviewed=False):
    if not confirm_reviewed:raise ValueError("Explicit reviewed-manifest confirmation required")
    import tempfile
    root=Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix="kontext-restore-check-") as check:
        manifest=restore(destination,check)
    if Path(manifest["root"]).resolve()!=root:raise ValueError("Manifest belongs to another repository")
    targets=[]
    for row in manifest["files"]:
        original=root/row["path"]
        if original.is_symlink():raise ValueError("Refusing a symlink removal target")
        target=original.resolve()
        if target.parent!=root/"data" or target.name not in RUNTIME_NAMES:raise ValueError("Removal target is outside allowed runtime files")
        if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest()!=row["sha256"]:raise ValueError("Runtime file changed since review")
        targets.append(target)
    # All absolute targets are checked before any file is removed. No recursive deletion.
    for target in targets:target.unlink()
    return {"removed":len(targets),"git_history":"Unchanged; history rewriting requires a separate review"}
