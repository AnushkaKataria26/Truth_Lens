from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    trust_index = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), default="pending")
    # minimal mock definition to foreign key relation

class Post(Base):
    __tablename__ = "posts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id"))  # linked analysis
    title = Column(String(200), nullable=False)
    caption = Column(String(1000), nullable=True)
    is_public = Column(Boolean, default=True)
    authenticity_score = Column(Float, nullable=False)
    risk_level = Column(String(50), nullable=False)
    media_thumbnail_url = Column(String(500), nullable=False)
    modality_tags = Column(JSONB)          # ["video", "audio"] — for filter
    upvote_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    bookmark_count = Column(Integer, default=0)
    report_count = Column(Integer, default=0)
    is_removed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Comment(Base):
    __tablename__ = "comments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)  # for replies
    body = Column(String(500), nullable=False)
    upvote_count = Column(Integer, default=0)
    is_removed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class Reaction(Base):
    __tablename__ = "reactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    target_type = Column(String(50))    # "post" | "comment"
    target_id = Column(UUID(as_uuid=True))
    reaction_type = Column(String(50))  # "upvote" | "bookmark" | "report"
    created_at = Column(DateTime, default=func.now())
    # unique constraint in actual DB: (user_id, target_type, target_id, reaction_type)

class Badge(Base):
    __tablename__ = "badges"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    badge_type = Column(String(100))     # "truth_seeker" | "fact_defender" | "community_educator"
    awarded_at = Column(DateTime, default=func.now())
    criteria_snapshot = Column(JSONB)  # what metrics qualified the user at award time

class AgentRunLog(Base):
    __tablename__ = "agent_run_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger = Column(String(100))
    papers_fetched = Column(Integer, default=0)
    patterns_extracted = Column(Integer, default=0)
    fine_tune_triggered = Column(Boolean, default=False)
    fine_tune_task_id = Column(String(255), nullable=True)
    rag_chunks_added = Column(Integer, default=0)
    summary_report = Column(Text)
    run_duration_ms = Column(Integer)
    created_at = Column(DateTime, default=func.now())

class TrainingData(Base):
    __tablename__ = "training_data"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_url = Column(String(1000), nullable=True)
    source_url = Column(String(1000), nullable=True)
    label = Column(String(50), nullable=False) # "real" or "fake"
    modality = Column(String(50), nullable=False, default="image") # "image", "audio", "video", "text"
    text_content = Column(Text, nullable=True) # for text modality
    local_path = Column(String(500), nullable=True) # Path where the file is stored locally
    created_at = Column(DateTime, default=func.now())
