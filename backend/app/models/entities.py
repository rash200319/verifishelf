from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import ENUM, LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(
        ENUM("starter", "growth", "enterprise"),
        default="starter",
    )
    status: Mapped[str] = mapped_column(
        ENUM("pending_review", "approved", "rejected", "needs_more_info"),
        default="pending_review",
    )
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    business_url: Mapped[Optional[str]] = mapped_column(Text)
    onboarding_notes: Mapped[Optional[str]] = mapped_column(Text)
    review_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    torch_sub_id: Mapped[Optional[str]] = mapped_column(String(255))
    registration_number: Mapped[Optional[str]] = mapped_column(String(255))
    business_address: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    contact_title: Mapped[Optional[str]] = mapped_column(String(150))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    estimated_sku_range: Mapped[Optional[str]] = mapped_column(String(50))
    current_marketplaces: Mapped[Optional[str]] = mapped_column(String(500))
    authorized_attestation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    map_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(ENUM("live", "pending"), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class BrandMarketplace(Base):
    __tablename__ = "brand_marketplaces"
    __table_args__ = (UniqueConstraint("brand_id", "marketplace_id", name="uq_brand_marketplace"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    marketplace_id: Mapped[int] = mapped_column(
        ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    crawl_frequency_hrs: Mapped[Optional[int]] = mapped_column(Integer)
    country_code: Mapped[Optional[str]] = mapped_column(String(10))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class SellerCluster(Base):
    __tablename__ = "seller_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_name: Mapped[Optional[str]] = mapped_column(String(255))
    risk_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Seller(Base):
    __tablename__ = "sellers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("seller_clusters.id", ondelete="SET NULL")
    )
    seller_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storefront_url: Mapped[Optional[str]] = mapped_column(Text)
    embedding: Mapped[Optional[Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    marketplace_id: Mapped[int] = mapped_column(
        ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False
    )
    listing_title: Mapped[str] = mapped_column(Text, nullable=False)
    listing_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    advertised_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), default="USD")
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class PromoWindow(Base):
    __tablename__ = "promo_windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    marketplace_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("marketplaces.id", ondelete="SET NULL")
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    map_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    advertised_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_delta_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    classifier_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    classifier_type: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(
        ENUM("open", "reviewed", "dismissed", "resolved"),
        default="open",
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    reopened_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_compliant_checks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EnforcementLetter(Base):
    __tablename__ = "enforcement_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    violation_id: Mapped[int] = mapped_column(
        ForeignKey("violations.id", ondelete="CASCADE"), nullable=False
    )
    letter_content: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(50), default="gpt4o")
    screenshot_base64: Mapped[Optional[str]] = mapped_column(LONGTEXT)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    report_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_content: Mapped[Optional[str]] = mapped_column(LONGTEXT)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class BrandInvite(Base):
    __tablename__ = "brand_invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(ENUM("admin", "analyst"), default="analyst")
    invite_code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_by: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    marketplace_id: Mapped[int] = mapped_column(
        ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False
    )
    brand_marketplace_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("brand_marketplaces.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(
        ENUM("queued", "running", "completed", "failed"),
        default="queued",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class RawCrawlResult(Base):
    __tablename__ = "raw_crawl_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crawl_job_id: Mapped[int] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False
    )
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    raw_html: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(ENUM("admin", "analyst", "superadmin"), default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_brand_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    invite_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
