#!/usr/bin/env python3
"""CLI Script: Automated End-to-End ITOM Telemetry Sync Pipeline.

This script executes the complete data pipeline:
1. (Optional) Ingest latest Intune managed devices via Microsoft Graph API.
2. Aggregate raw records, normalize manufacturer strings, and compute fleet metrics.
3. Validate mathematical invariants across 25,987 endpoint records.
4. Save precomputed `data/intune_summary.json` payload.
5. (Optional) Synchronize payload and device records to Firestore.

Usage:
    python scripts/run_sync.py [--skip-fetch] [--skip-firestore]
"""

import argparse
import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.sync.firestore_sync import FirestoreSyncService
from src.sync.graph_client import GraphClient
from src.sync.payload_generator import PayloadGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_sync")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Execute complete ITOM Intune telemetry extraction, aggregation, and sync pipeline."
    )
    parser.add_argument(
        "--raw-data",
        default=os.path.join(PROJECT_ROOT, "data", "intune_ops_analytics.json"),
        help="Path to raw telemetry JSON file",
    )
    parser.add_argument(
        "--summary-data",
        default=os.path.join(PROJECT_ROOT, "data", "intune_summary.json"),
        help="Path to aggregated summary JSON file",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        default=True,  # Default to true when Graph credentials might not be configured in local test env
        help="Skip Graph API live network fetch and use existing raw data file",
    )
    parser.add_argument(
        "--fetch-live",
        action="store_true",
        help="Force live fetch from Microsoft Graph API",
    )
    parser.add_argument(
        "--skip-firestore",
        action="store_true",
        help="Skip Firestore synchronization step",
    )
    return parser.parse_args()


def main() -> int:
    """Execute end-to-end synchronization pipeline."""
    args = parse_args()
    logger.info("=== Starting ITOM Telemetry Sync Pipeline ===")

    # Step 1: Live Ingestion (Optional)
    if args.fetch_live and not args.skip_fetch:
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        if not all([tenant_id, client_id, client_secret]):
            logger.warning("Graph API credentials missing; skipping live fetch and using existing raw dataset.")
        else:
            logger.info("Step 1: Ingesting device records from Microsoft Graph API...")
            client = GraphClient(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
            client.fetch_and_save(output_path=args.raw_data)

    # Step 2 & 3: Aggregation & Invariant Validation
    logger.info("Step 2: Processing and aggregating telemetry metrics...")
    generator = PayloadGenerator(default_sample_size=100)
    try:
        payload = generator.generate(
            input_file=args.raw_data,
            output_file=args.summary_data,
            sample_size=100,
        )
        logger.info("Step 3: Verified mathematical invariants across %d managed devices.",
                    payload["metrics"]["total_managed_devices"])
    except Exception as err:
        logger.error("Failed during payload generation: %s", err)
        return 1

    # Step 4: Firestore Sync (Optional)
    if not args.skip_firestore:
        logger.info("Step 4: Synchronizing payload to Firestore...")
        sync_service = FirestoreSyncService()
        status = sync_service.sync_summary_payload(payload=payload)
        logger.info("Firestore sync status: %s (offline: %s)", status.get("status"), status.get("offline_mode"))

    logger.info("=== ITOM Telemetry Sync Pipeline Completed Successfully ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
