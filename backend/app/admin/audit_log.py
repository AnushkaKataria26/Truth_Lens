import uuid
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DB Model (SQLAlchemy — defined here for reference, actual model in db_models.py)
# ─────────────────────────────────────────────────────────────────────────────
# class AdminAuditLog(Base):
#     __tablename__ = "admin_audit_logs"
#     id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     admin_user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
#     action_type = Column(String, nullable=False)
#       # "remove_post" | "ban_user" | "unban_user" | "override_risk" |
#       # "agent_manual_trigger" | "lora_rollback" | "system_config_change"
#     target_type = Column(String, nullable=False)   # "post" | "user" | "analysis" | "system"
#     target_id = Column(String, nullable=False)
#     reason = Column(String(500), nullable=True)
#     metadata_ = Column("metadata", JSONB, nullable=True)  # before/after state for overrides
#     ip_address = Column(String, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#
# ─── ROW-LEVEL SECURITY ──────────────────────────────────────────────────────
# The audit log table must NEVER be deleted from, even for banned users or
# removed posts. Retain all audit records indefinitely. Apply the following
# PostgreSQL migration post-schema-creation:
#
#   ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;
#   ALTER TABLE admin_audit_logs FORCE ROW LEVEL SECURITY;
#
#   -- Allow SELECT for admin roles (read-only access)
#   CREATE POLICY audit_select_policy ON admin_audit_logs
#       FOR SELECT
#       USING (true);
#
#   -- Allow INSERT for the application role (new audit entries)
#   CREATE POLICY audit_insert_policy ON admin_audit_logs
#       FOR INSERT
#       WITH CHECK (true);
#
#   -- Block ALL DELETE operations except for the superuser role
#   CREATE POLICY audit_no_delete_policy ON admin_audit_logs
#       FOR DELETE
#       TO truthlens_superuser
#       USING (true);
#
#   -- Revoke DELETE privilege from the application role explicitly
#   REVOKE DELETE ON admin_audit_logs FROM truthlens_app;
#
# This ensures no application code path can ever delete audit records.
# ──────────────────────────────────────────────────────────────────────────────

VALID_ACTION_TYPES = {
    "remove_post",
    "ban_user",
    "unban_user",
    "override_risk",
    "agent_manual_trigger",
    "lora_rollback",
    "system_config_change",
}

VALID_TARGET_TYPES = {"post", "user", "analysis", "system", "agent"}


@dataclass
class AuditEntry:
    id: str
    admin_user_id: str
    action_type: str
    target_type: str
    target_id: str
    reason: Optional[str] = None
    metadata: Optional[dict] = None   # before/after state for override actions
    ip_address: Optional[str] = None
    created_at: str = ""


# In-memory buffer for mock — production writes directly to DB
_audit_buffer: list[AuditEntry] = []


def log_admin_action(
    admin_user_id: str,
    action_type: str,
    target_type: str,
    target_id: str,
    reason: Optional[str] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditEntry:
    """
    Record every admin action to the audit trail.
    Called by all admin endpoints AFTER the action succeeds — never before.
    Stored in DB table: admin_audit_logs (append-only, immutable, never deleted).
    """
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        admin_user_id=admin_user_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        metadata=metadata,
        ip_address=ip_address,
        created_at=datetime.utcnow().isoformat(),
    )

    # [MOCK] In production:
    # db.add(AdminAuditLog(
    #     admin_user_id=admin_user_id,
    #     action_type=action_type,
    #     target_type=target_type,
    #     target_id=target_id,
    #     reason=reason,
    #     metadata_=metadata,
    #     ip_address=ip_address,
    # ))
    # db.commit()

    _audit_buffer.append(entry)
    logger.info(
        f"AUDIT: admin={admin_user_id} action={action_type} "
        f"target={target_type}:{target_id} reason={reason}"
    )
    return entry


def get_audit_log(
    page: int = 1,
    limit: int = 50,
    action_filter: Optional[str] = None,
    admin_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    """
    Retrieve paginated audit log entries, newest first.
    Supports filtering by action_type, admin_user_id, and date range.
    """
    # [MOCK] In production:
    # query = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())
    # if action_filter:
    #     query = query.where(AdminAuditLog.action_type == action_filter)
    # if admin_filter:
    #     query = query.where(AdminAuditLog.admin_user_id == admin_filter)
    # if date_from:
    #     query = query.where(AdminAuditLog.created_at >= date_from)
    # if date_to:
    #     query = query.where(AdminAuditLog.created_at <= date_to)
    # query = query.offset((page - 1) * limit).limit(limit)

    filtered = list(reversed(_audit_buffer))  # newest first
    if action_filter:
        filtered = [e for e in filtered if e.action_type == action_filter]
    if admin_filter:
        filtered = [e for e in filtered if e.admin_user_id == admin_filter]
    if date_from:
        filtered = [e for e in filtered if e.created_at >= date_from]
    if date_to:
        filtered = [e for e in filtered if e.created_at <= date_to]

    start = (page - 1) * limit
    page_entries = filtered[start:start + limit]

    return {
        "entries": [asdict(e) for e in page_entries],
        "total": len(filtered),
        "page": page,
        "limit": limit,
    }
