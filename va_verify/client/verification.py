"""
Client for the VA Veteran Service History and Eligibility API (v2).

Authentication: OAuth 2.0 — bearer token passed in Authorization header.
Sandbox base URL: https://sandbox-api.va.gov/services/veteran_verification/v2
Production base URL: https://api.va.gov/services/veteran_verification/v2

All POST endpoints use demographic data to find a Veteran (no ICN needed).
GET endpoints require an ICN in the OAuth token context (user-authenticated flow).

This client wraps the POST (demographic-search) variants, which are the most
useful for a standalone CLI application that doesn't run inside VA.gov.
"""

from __future__ import annotations
from typing import Optional

from .. import config
from ..models import (
    VeteranStatus,
    ServiceHistory,
    DisabilityRating,
    EnrolledBenefit,
    Flash,
)
from .base import VAAPIError, _raise_for_status, build_session

_PREFIX = "/services/veteran_verification/v2"


def _veteran_attrs(
    first_name: str,
    last_name: str,
    birth_date: str,
    street_address_line1: str,
    city: str,
    country: str,
    zipcode: str,
    *,
    middle_name: Optional[str] = None,
    state: Optional[str] = None,
    gender: Optional[str] = None,
    mothers_maiden_name: Optional[str] = None,
    home_phone_number: Optional[str] = None,
    birth_place_city: Optional[str] = None,
    birth_place_state: Optional[str] = None,
    birth_place_country: Optional[str] = None,
) -> dict:
    """Build the VeteranAttributes payload for POST endpoints."""
    payload: dict = {
        "first_name": first_name,
        "last_name": last_name,
        "birth_date": birth_date,
        "street_address_line1": street_address_line1,
        "city": city,
        "country": country,
        "zipcode": zipcode,
    }
    if middle_name:
        payload["middle_name"] = middle_name
    if state:
        payload["state"] = state
    if gender:
        payload["gender"] = gender
    if mothers_maiden_name:
        payload["mothers_maiden_name"] = mothers_maiden_name
    if home_phone_number:
        payload["home_phone_number"] = home_phone_number
    if birth_place_city:
        payload["birth_place_city"] = birth_place_city
    if birth_place_state:
        payload["birth_place_state"] = birth_place_state
    if birth_place_country:
        payload["birth_place_country"] = birth_place_country
    return payload


class VerificationClient:
    """
    Wraps the Veteran Service History and Eligibility API (POST endpoints).

    Requires an OAuth 2.0 bearer token. Obtain one via the VA sandbox OAuth
    flow before instantiating this client.

    Usage::

        client = VerificationClient(token="Bearer eyJ...")
        status = client.get_status(
            first_name="Alfredo", last_name="Armstrong",
            birth_date="1993-06-08",
            street_address_line1="17020 Tortoise St",
            city="Round Rock", country="USA", zipcode="78664",
        )
    """

    def __init__(self, token: str):
        """
        Parameters
        ----------
        token: Full bearer token string, e.g. "Bearer eyJ...".
               If you pass a raw token without the "Bearer " prefix it will
               be added automatically.
        """
        if not token.startswith("Bearer "):
            token = f"Bearer {token}"
        base = config.get_base_url()
        self._base = base + _PREFIX
        self._session = build_session({"Authorization": token})

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, payload: dict) -> dict:
        resp = self._session.post(self._base + path, json=payload)
        _raise_for_status(resp)
        return resp.json()

    def _attrs(
        self,
        first_name: str,
        last_name: str,
        birth_date: str,
        street_address_line1: str,
        city: str,
        country: str,
        zipcode: str,
        **kwargs,
    ) -> dict:
        return _veteran_attrs(
            first_name, last_name, birth_date,
            street_address_line1, city, country, zipcode,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_status(self, first_name: str, last_name: str, birth_date: str,
                   street_address_line1: str, city: str, country: str,
                   zipcode: str, **kwargs) -> VeteranStatus:
        """Confirm Title 38 Veteran status via demographic search."""
        payload = self._attrs(first_name, last_name, birth_date,
                              street_address_line1, city, country, zipcode,
                              **kwargs)
        data = self._post("/status", payload)
        return VeteranStatus.from_dict(data)

    def get_service_history(self, first_name: str, last_name: str,
                            birth_date: str, street_address_line1: str,
                            city: str, country: str, zipcode: str,
                            **kwargs) -> ServiceHistory:
        """Retrieve military service history via demographic search."""
        payload = self._attrs(first_name, last_name, birth_date,
                              street_address_line1, city, country, zipcode,
                              **kwargs)
        data = self._post("/service_history", payload)
        return ServiceHistory.from_dict(data)

    def get_disability_rating(self, first_name: str, last_name: str,
                              birth_date: str, street_address_line1: str,
                              city: str, country: str, zipcode: str,
                              **kwargs) -> DisabilityRating:
        """Retrieve VA disability ratings via demographic search."""
        payload = self._attrs(first_name, last_name, birth_date,
                              street_address_line1, city, country, zipcode,
                              **kwargs)
        data = self._post("/disability_rating", payload)
        return DisabilityRating.from_dict(data)

    def get_enrolled_benefits(self, first_name: str, last_name: str,
                              birth_date: str, street_address_line1: str,
                              city: str, country: str, zipcode: str,
                              **kwargs) -> list[EnrolledBenefit]:
        """Retrieve enrolled VA benefits via demographic search."""
        payload = self._attrs(first_name, last_name, birth_date,
                              street_address_line1, city, country, zipcode,
                              **kwargs)
        data = self._post("/enrolled_benefits", payload)
        return [EnrolledBenefit.from_dict(b) for b in data.get("veteran_benefits", [])]

    def get_flashes(self, first_name: str, last_name: str, birth_date: str,
                    street_address_line1: str, city: str, country: str,
                    zipcode: str, **kwargs) -> list[Flash]:
        """Retrieve eligibility flashes via demographic search."""
        payload = self._attrs(first_name, last_name, birth_date,
                              street_address_line1, city, country, zipcode,
                              **kwargs)
        data = self._post("/flashes", payload)
        return [Flash.from_dict(f) for f in data.get("flashes", [])]
