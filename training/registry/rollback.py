"""
Model Rollback
================
Reverts the active model to a previous version by updating the registry
status and the ``latest`` symlink.

Usage:
    python -m training.registry.rollback --name efficientnetv2 --version v0.9
"""

from __future__ import annotations

import argparse
import logging

from training.registry.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


def rollback(name: str, version: str, registry: ModelRegistry | None = None) -> bool:
    """Revert the active model to *version*.

    The currently active model is archived, and the specified *version* is
    promoted to active.

    Args:
        name: model family name.
        version: target version to roll back to.
        registry: optional pre-initialised ``ModelRegistry``.

    Returns:
        True if rollback succeeded, False if the target version was not found.
    """
    registry = registry or ModelRegistry()

    # Validate target exists
    target = registry.db.get_by_version(name, version)
    if target is None:
        logger.error("Cannot rollback: %s version %s not found", name, version)
        return False

    # Get current active for logging
    current = registry.get_active(name)
    if current:
        logger.info(
            "Rolling back %s: %s (active) → %s",
            name, current.version, version,
        )
    else:
        logger.info("No active version of %s — promoting %s directly", name, version)

    promoted = registry.promote(name, version)
    if promoted is None:
        logger.error("Promotion failed for %s %s", name, version)
        return False

    logger.info(
        "Rollback complete: %s is now active at version %s (path=%s)",
        name, promoted.version, promoted.path,
    )
    return True


def list_versions(name: str, registry: ModelRegistry | None = None) -> None:
    """Print all registered versions for a model family."""
    registry = registry or ModelRegistry()
    versions = registry.get_all_versions(name)

    if not versions:
        print(f"No versions found for '{name}'")
        return

    print(f"\n{'Version':<12} {'Status':<10} {'Created':<22} {'AUC-ROC':<10}")
    print("-" * 56)
    for v in versions:
        auc = v.metrics.get("auc_roc", "N/A") if v.metrics else "N/A"
        if isinstance(auc, float):
            auc = f"{auc:.4f}"
        print(f"{v.version:<12} {v.status:<10} {v.created_at[:19]:<22} {auc:<10}")
    print()


# ── CLI ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Rollback model to a previous version")
    sub = parser.add_subparsers(dest="command")

    roll = sub.add_parser("rollback", help="Rollback to a specific version")
    roll.add_argument("--name", required=True, help="Model family name")
    roll.add_argument("--version", required=True, help="Target version")

    ls = sub.add_parser("list", help="List all versions")
    ls.add_argument("--name", required=True, help="Model family name")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    if args.command == "rollback":
        success = rollback(args.name, args.version)
        if not success:
            raise SystemExit(1)
    elif args.command == "list":
        list_versions(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
