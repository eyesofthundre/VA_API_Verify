"""Dataclasses representing VA API response data."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Veteran Confirmation API models
# ---------------------------------------------------------------------------

@dataclass
class ConfirmationStatus:
    """Result from the Veteran Confirmation API (API key auth)."""
    veteran_status: str  # "confirmed" or "not confirmed"

    @classmethod
    def from_dict(cls, data: dict) -> "ConfirmationStatus":
        return cls(veteran_status=data.get("veteran_status", "unknown"))


# ---------------------------------------------------------------------------
# Veteran Service History & Eligibility API models
# ---------------------------------------------------------------------------

@dataclass
class VeteranStatus:
    """Title 38 Veteran status result."""
    veteran_status: str  # "confirmed" or "not confirmed"
    not_confirmed_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "VeteranStatus":
        attrs = data.get("data", {}).get("attributes", {})
        return cls(
            veteran_status=attrs.get("veteran_status", "unknown"),
            not_confirmed_reason=attrs.get("not_confirmed_reason"),
        )


@dataclass
class Deployment:
    location: str
    start_date: Optional[str]
    end_date: Optional[str]

    @classmethod
    def from_dict(cls, d: dict) -> "Deployment":
        return cls(
            location=d.get("location", ""),
            start_date=d.get("start_date"),
            end_date=d.get("end_date"),
        )


@dataclass
class ServiceEpisode:
    first_name: str
    last_name: str
    branch_of_service: str
    service_type: str
    component_of_service: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    pay_grade: Optional[str]
    discharge_status: Optional[str]
    separation_reason: Optional[str]
    combat_pay: Optional[bool]
    deployments: list[Deployment] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ServiceEpisode":
        attrs = d.get("attributes", {})
        deps = [Deployment.from_dict(dep) for dep in attrs.get("deployments", [])]
        return cls(
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            branch_of_service=attrs.get("branch_of_service", ""),
            service_type=attrs.get("service_type", ""),
            component_of_service=attrs.get("component_of_service"),
            start_date=attrs.get("start_date"),
            end_date=attrs.get("end_date"),
            pay_grade=attrs.get("pay_grade"),
            discharge_status=attrs.get("discharge_status"),
            separation_reason=attrs.get("separation_reason"),
            combat_pay=attrs.get("service_episode_combat_pay"),
            deployments=deps,
        )


@dataclass
class ServiceHistory:
    episodes: list[ServiceEpisode]
    # military_summary is sparse in the spec; store raw for now
    military_summary: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceHistory":
        episodes = [ServiceEpisode.from_dict(ep) for ep in data.get("data", [])]
        summary = data.get("military_summary", {})
        return cls(episodes=episodes, military_summary=summary)


@dataclass
class IndividualRating:
    decision: Optional[str]
    rating_percentage: Optional[int]
    effective_date: Optional[str]
    rating_end_date: Optional[str]
    diagnostic_type_code: Optional[str]
    diagnostic_type_name: Optional[str]
    diagnostic_text: Optional[str]
    static_ind: Optional[bool]

    @classmethod
    def from_dict(cls, d: dict) -> "IndividualRating":
        return cls(
            decision=d.get("decision"),
            rating_percentage=d.get("rating_percentage"),
            effective_date=d.get("effective_date"),
            rating_end_date=d.get("rating_end_date"),
            diagnostic_type_code=d.get("diagnostic_type_code"),
            diagnostic_type_name=d.get("diagnostic_type_name"),
            diagnostic_text=d.get("diagnostic_text"),
            static_ind=d.get("static_ind"),
        )


@dataclass
class DisabilityRating:
    combined_disability_rating: Optional[int]
    combined_effective_date: Optional[str]
    legal_effective_date: Optional[str]
    individual_ratings: list[IndividualRating] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "DisabilityRating":
        attrs = data.get("data", {}).get("attributes", {})
        ratings = [IndividualRating.from_dict(r) for r in attrs.get("individual_ratings", [])]
        return cls(
            combined_disability_rating=attrs.get("combined_disability_rating"),
            combined_effective_date=attrs.get("combined_effective_date"),
            legal_effective_date=attrs.get("legal_effective_date"),
            individual_ratings=ratings,
        )


@dataclass
class EnrolledBenefit:
    program_code: str
    program_name: str
    award_effective_date: Optional[str]

    @classmethod
    def from_dict(cls, d: dict) -> "EnrolledBenefit":
        return cls(
            program_code=d.get("program_code", ""),
            program_name=d.get("program_name", ""),
            award_effective_date=d.get("award_effective_date"),
        )


@dataclass
class Flash:
    flash_name: str

    @classmethod
    def from_dict(cls, d: dict) -> "Flash":
        return cls(flash_name=d.get("flash_name", ""))
