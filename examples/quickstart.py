#!/usr/bin/env python3
"""End-to-end Magellan Data Spotlight batch pipeline against the REST API.

This is the same flow the MCP server exposes as tools, written out plainly so you
can see what an agent is doing on your behalf — or wire Magellan Data into a
pipeline that has no agent in it at all.

    export MAGELLAN_API_KEY=mgln_sk_live_...
    python quickstart.py --urls moosend.com constantcontact.com --type pe_ownership

Nothing costs credits until the download step, and the script stops to ask before
it gets there. Pass --yes to skip the prompt in automated runs.

Requires: httpx  (pip install httpx)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx

API_BASE = os.environ.get("MAGELLAN_API_BASE", "https://api.magellandata.io")
OUTPUT_TYPES = (
    "parent_companies",
    "pe_ownership",
    "corporate_families",
    "pe_portfolios",
)

# Flat-rate types let us quote a price before the run finishes. The per-record
# types don't, so we read the price off the completed run instead.
FLAT_RATE_CREDITS_PER_URL = {"parent_companies": 70, "pe_ownership": 70}

POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS = 1200  # large runs genuinely take this long


def api(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    response = client.request(method, f"{API_BASE}{path}", **kwargs)
    if response.status_code >= 400:
        sys.exit(f"HTTP {response.status_code} on {method} {path}: {response.text}")
    return response.json()


def submit_batch(client: httpx.Client, urls: list[str]) -> str:
    """Create a batch. Free. Invalid URLs are reported but don't block creation."""
    result = api(client, "POST", "/v1/batch", json={"urls": urls})
    invalid = result.get("invalid_urls") or []
    if invalid:
        print(f"  skipped {len(invalid)} unparseable URL(s): {', '.join(invalid[:5])}")
    print(f"  batch {result['batch_id']} — {result['valid_url_count']} valid URLs")
    return result["batch_id"]


def process_batch(client: httpx.Client, batch_id: str, output_types: list[str]) -> list[str]:
    """Kick off async processing. Free. One run per output type, returns immediately."""
    result = api(
        client,
        "POST",
        f"/v1/batch/{batch_id}/process",
        json={"output_types": output_types},
    )
    run_ids = [run["run_id"] for run in result["runs"]]
    print(f"  started {len(run_ids)} run(s)")
    return run_ids


def poll_until_complete(client: httpx.Client, run_id: str) -> dict:
    """Poll a run to completion. Free. Be patient — minutes, not seconds."""
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        run = api(client, "GET", f"/v1/batch/run/{run_id}")
        status = run["run_status"]
        if status == "completed":
            return run
        if status == "failed":
            sys.exit(f"  run {run_id} failed: {run.get('error', 'no detail given')}")
        print(f"  {run_id}: {status} …")
        time.sleep(POLL_INTERVAL_SECONDS)
    sys.exit(f"  run {run_id} still running after {POLL_TIMEOUT_SECONDS}s — check later")


def download_run(client: httpx.Client, run_id: str) -> str:
    """CHARGES CREDITS on first call. Returns a presigned CSV URL (1-hour TTL).

    Re-downloads are free forever — is_purchased persists. If the link expires
    (HTTP 403, 'Request has expired'), just call this again at no cost.
    """
    result = api(client, "POST", f"/v1/batch/run/{run_id}/download")
    return result["download_url"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--urls", nargs="+", required=True, help="Company domains to enrich")
    parser.add_argument(
        "--type",
        dest="output_types",
        nargs="+",
        default=["pe_ownership"],
        choices=OUTPUT_TYPES,
        help="One or more output types",
    )
    parser.add_argument("--out", default="results", help="Output filename prefix")
    parser.add_argument("--yes", action="store_true", help="Skip the spend confirmation")
    args = parser.parse_args()

    api_key = os.environ.get("MAGELLAN_API_KEY")
    if not api_key:
        sys.exit("Set MAGELLAN_API_KEY (get one at https://magellandata.io)")

    headers = {"Authorization": f"Bearer {api_key}"}

    with httpx.Client(headers=headers, timeout=60.0) as client:
        print("Checking credits…")
        credits = api(client, "GET", "/v1/credits")
        balance = credits["available_credits"]
        print(f"  balance: {balance:,} credits\n")

        # Quote the flat-rate portion up front. Per-record types can't be quoted
        # until their run completes.
        flat = sum(
            FLAT_RATE_CREDITS_PER_URL.get(t, 0) * len(args.urls) for t in args.output_types
        )
        per_record = [t for t in args.output_types if t not in FLAT_RATE_CREDITS_PER_URL]
        if flat:
            print(f"Flat-rate portion: {flat:,} credits")
        if per_record:
            print(f"Per-record types ({', '.join(per_record)}): priced after the run completes")
        print()

        print("Submitting batch…")
        batch_id = submit_batch(client, args.urls)

        print("Processing…")
        run_ids = process_batch(client, batch_id, args.output_types)

        print("\nPolling for completion…")
        completed = [poll_until_complete(client, run_id) for run_id in run_ids]

        total = sum(run["price"] for run in completed)
        print("\n--- Ready to download ---")
        for run in completed:
            print(f"  {run['output_type']:20s} {run['price']:>10,} credits")
        print(f"  {'TOTAL':20s} {total:>10,} credits")
        print(f"  balance after: {balance - total:,}\n")

        if total > balance:
            sys.exit("Insufficient credits. Top up at https://magellandata.io")

        if not args.yes:
            if input("Download and spend these credits? [y/N] ").strip().lower() != "y":
                print("Stopped. Nothing was charged — the runs stay available.")
                return

        for run in completed:
            url = download_run(client, run["run_id"])
            # The presigned URL needs no auth header. Fetch it with a bare client.
            with httpx.Client(timeout=300.0, follow_redirects=True) as anon:
                csv = anon.get(url)
                csv.raise_for_status()
            path = f"{args.out}_{run['output_type']}.csv"
            with open(path, "wb") as handle:
                handle.write(csv.content)
            size_mb = len(csv.content) / 1_048_576
            print(f"  wrote {path} ({size_mb:.1f} MB)")

        print("\nEvery output row carries input_url — join on that to get back to your list.")


if __name__ == "__main__":
    main()
