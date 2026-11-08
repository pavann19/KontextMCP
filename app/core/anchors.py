"""Portable Ed25519 audit anchors verified with an independently pinned public key."""
import base64
import hashlib
import json
import os
import csv
import subprocess
from filelock import FileLock
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from app.core.audit import AuditLogger
from app.config import settings


def initialize(directory):
    directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    if directory.is_relative_to(settings.DATA_DIR.resolve()):raise ValueError("Signing keys must be outside application data storage")
    key=Ed25519PrivateKey.generate()
    secret=directory/"signing-private.key"
    with secret.open("xb") as stream:stream.write(key.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()))
    secret.chmod(0o600)
    if os.name=="nt":
        principal=next(csv.reader(subprocess.check_output(["whoami","/user","/fo","csv","/nh"],text=True).strip().splitlines()))[1]
        subprocess.run(["icacls",str(secret),"/inheritance:r","/grant:r",f"*{principal}:(F)"],capture_output=True,check=True)
    public=directory/"trusted-public.key"
    with public.open("xb") as stream:stream.write(key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw))
    return {"public_key_sha256":hashlib.sha256(public.read_bytes()).hexdigest(),"directory":str(directory)}


def export_anchor(directory):
    directory=Path(directory).resolve()
    if directory.is_relative_to(settings.DATA_DIR.resolve()):raise ValueError("Anchor destination must be outside application data storage")
    # Keep the verified count and signed hash in one writer-locked snapshot.
    with AuditLogger._lock, FileLock(str(settings.AUDIT_LOG_PATH)+".writer.lock",timeout=30):
        valid,count,error=AuditLogger.verify_integrity()
        if not valid:raise ValueError(error)
        lines=[json.loads(line) for line in settings.AUDIT_LOG_PATH.read_text(encoding="utf-8").split("\n") if line.strip()]
        last_hash=lines[-1]["record_hash"] if lines else "0"*64
    key=Ed25519PrivateKey.from_private_bytes((directory/"signing-private.key").read_bytes())
    payload={"record_count":count,"last_hash":last_hash}
    signature=key.sign(json.dumps(payload,sort_keys=True).encode())
    document={**payload,"signature":base64.b64encode(signature).decode()}
    destination=directory/f"anchor-{count}-{payload['last_hash'][:16]}.json"
    with destination.open("x",encoding="utf-8") as stream:json.dump(document,stream,indent=2)
    return destination


def verify_anchor(anchor, trusted_public_key, log_path):
    """The public key must come from a separately trusted/pinned location."""
    from cryptography.exceptions import InvalidSignature
    try:
        doc=json.loads(Path(anchor).read_text(encoding="utf-8"))
        payload={"record_count":doc["record_count"],"last_hash":doc["last_hash"]}
        key=Ed25519PublicKey.from_public_bytes(Path(trusted_public_key).read_bytes())
        key.verify(base64.b64decode(doc["signature"],validate=True),json.dumps(payload,sort_keys=True).encode())
        # Validate the full chain, including event IDs, without changing global settings.
        prior="0"*64;hashes=[prior]
        for line in Path(log_path).read_text(encoding="utf-8").split("\n"):
            if not line.strip():continue
            row=json.loads(line)
            data={k:row[k] for k in ("trace_id","timestamp","user_id","user_role","action","target_resource","status","details")}
            data["target_resource"]=data["target_resource"] or "none"
            if row.get("event_id"):data["event_id"]=row["event_id"]
            if row["prev_hash"]!=prior or AuditLogger.compute_hash(prior,data)!=row["record_hash"]:return False
            prior=row["record_hash"];hashes.append(prior)
        count=doc["record_count"]
        return isinstance(count,int) and 0<=count<len(hashes) and hashes[count]==doc["last_hash"]
    except (ValueError,KeyError,TypeError,OSError,InvalidSignature):return False
