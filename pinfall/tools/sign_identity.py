#!/usr/bin/env python3
"""Mint a durable iOS signing identity over the App Store Connect API, on Linux, with no Mac.

Why this exists. Signing needs a certificate AND its private key, and there was no `.p12`
anywhere on this box — only the ASC API key. The usual escape hatch, `xcodebuild
-allowProvisioningUpdates`, asks Apple to CREATE a certificate on the runner, and the account is
already at Apple's ceiling of three `Apple Distribution` certs. So that route fails, and the way
out of it (revoking one) would break whatever StreakMark and Rascal Naps sign with.

The `IOS_DISTRIBUTION` quota is separate and holds one of three. So: generate the keypair HERE,
send Apple only the CSR, and keep the private key. That is the whole trick — a certificate signed
by Apple is useless to anyone without the key that never left this machine, and having it means
any runner can sign without ever asking Apple for a new identity again.

    sign_identity.py --create      # keypair + CSR + certificate + .p12, then a matching profile
    sign_identity.py --show        # what exists today
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asc import call                                            # noqa: E402

SECRETS = os.path.expanduser("~/.secrets")
KEY = os.path.join(SECRETS, "pinfall_ios_dist.key")
CSR = os.path.join(SECRETS, "pinfall_ios_dist.csr")
CER = os.path.join(SECRETS, "pinfall_ios_dist.cer")
P12 = os.path.join(SECRETS, "pinfall_ios_dist.p12")
PASSFILE = os.path.join(SECRETS, "pinfall_ios_dist.pass")
PROFILE = os.path.join(SECRETS, "Pinfall_Runner.mobileprovision")

BUNDLE = "com.piotraiventures.pinfall"
PROFILE_NAME = "Pinfall_Runner"
SUBJECT = "/emailAddress=petesarney@gmail.com/CN=Piotr Sarna/C=US"


def sh(*args: str) -> None:
    subprocess.run(args, check=True, capture_output=True)


def make_csr() -> str:
    os.makedirs(SECRETS, exist_ok=True)
    if not os.path.exists(KEY):
        sh("openssl", "genrsa", "-out", KEY, "2048")
        os.chmod(KEY, 0o600)
    sh("openssl", "req", "-new", "-key", KEY, "-out", CSR, "-subj", SUBJECT)
    return "".join(l for l in open(CSR).read().splitlines() if "-----" not in l)


def create_cert() -> dict:
    """Apple returns the signed certificate as base64 DER in the response body."""
    csr_body = open(CSR).read()
    r = call("certificates", "POST", {"data": {
        "type": "certificates",
        "attributes": {"certificateType": "IOS_DISTRIBUTION", "csrContent": csr_body}}})
    attrs = r["data"]["attributes"]
    open(CER, "wb").write(base64.b64decode(attrs["certificateContent"]))
    return {"id": r["data"]["id"], "name": attrs.get("name"),
            "expires": attrs.get("expirationDate")}


def make_p12() -> str:
    pem = CER + ".pem"
    sh("openssl", "x509", "-inform", "DER", "-in", CER, "-out", pem)
    password = base64.urlsafe_b64encode(os.urandom(18)).decode().rstrip("=")
    # -legacy: macOS's security(1) cannot import a PKCS#12 sealed with OpenSSL 3's default
    # AES-256-CBC + PBKDF2 and fails with a bare "MAC verification failed", which reads like a
    # wrong password rather than an algorithm mismatch.
    sh("openssl", "pkcs12", "-export", "-legacy", "-inkey", KEY, "-in", pem,
       "-out", P12, "-passout", f"pass:{password}", "-name", "Pinfall iOS Distribution")
    open(PASSFILE, "w").write(password)
    os.chmod(PASSFILE, 0o600)
    os.chmod(P12, 0o600)
    return password


def create_profile(cert_id: str) -> dict:
    bundles = {x["attributes"]["identifier"]: x["id"]
               for x in call("bundleIds?limit=200")["data"]}
    if BUNDLE not in bundles:
        raise SystemExit(f"no bundle id {BUNDLE}")
    r = call("profiles", "POST", {"data": {
        "type": "profiles",
        "attributes": {"name": PROFILE_NAME, "profileType": "IOS_APP_STORE"},
        "relationships": {
            "bundleId": {"data": {"type": "bundleIds", "id": bundles[BUNDLE]}},
            "certificates": {"data": [{"type": "certificates", "id": cert_id}]}}}})
    a = r["data"]["attributes"]
    open(PROFILE, "wb").write(base64.b64decode(a["profileContent"]))
    return {"id": r["data"]["id"], "name": a.get("name"), "state": a.get("profileState"),
            "uuid": a.get("uuid")}


def show() -> int:
    for label, path in (("private key", KEY), ("certificate", CER), ("p12", P12),
                        ("profile", PROFILE)):
        print(f"  {label:<12} {'present' if os.path.exists(path) else 'MISSING':<8} {path}")
    certs = [c for c in call("certificates?limit=50")["data"]
             if c["attributes"].get("certificateType") == "IOS_DISTRIBUTION"]
    print(f"\n  iOS Distribution certs on the account: {len(certs)} of 3")
    for c in certs:
        print(f"    {c['attributes'].get('name')}  expires {c['attributes'].get('expirationDate')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    if a.show or not a.create:
        return show()

    if os.path.exists(P12) and os.path.exists(PROFILE):
        print("identity already exists — nothing to mint")
        return show()

    make_csr()
    cert = create_cert()
    print(f"certificate: {cert['name']}  id={cert['id']}  expires {cert['expires']}")
    pw = make_p12()
    print(f"p12 written, password in {PASSFILE} ({len(pw)} chars)")
    prof = create_profile(cert["id"])
    print(f"profile: {prof['name']}  {prof['state']}  uuid={prof['uuid']}")
    print("\nSecrets to push to the repo:")
    print("  IOS_DIST_P12_BASE64, IOS_DIST_P12_PASSWORD, IOS_PROFILE_BASE64")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
