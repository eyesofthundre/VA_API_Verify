"""
Client for the VA Veteran Confirmation API (v1).

Authentication: API key passed in the `apiKey` header.
Sandbox base URL: https://sandbox-api.va.gov/services/veteran-confirmation/v1
Production base URL: https://api.va.gov/services/veteran-confirmation/v1

This API answers a single question: is this person a confirmed Title 38 Veteran?
It uses demographic data (no SSN) and a simple API key — making it the
easiest starting point before the OAuth-based Verification API.

Note: An older v0 API existed but is deprecated and no longer available.
"""

from __future__ import annotations
from typing import Optional

from .. import config
from ..models import ConfirmationStatus
from .base import VAAPIError, _raise_for_status, build_session

_PATH = "/services/veteran-confirmation/{version}/status"
_VERSION = "v1"


class ConfirmationClient:
    """
    Wraps the Veteran Confirmation API (v1).

    Usage::

        client = ConfirmationClient()
        result = client.confirm_status(
            first_name="Alfredo",
            last_name="Armstrong",
            birth_date="1993-06-08",
            street_address_line1="17020 Tortoise St",
            city="Round Rock",
            state="TX",
            country="USA",
            zip_code="78664",
        )
        print(result.veteran_status)  # "confirmed" or "not confirmed"
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or config.require_api_key()
        base = config.get_base_url()
        url_path = _PATH.format(version=_VERSION)
        self._url = base + url_path
        # v1 uses camelCase header name "apiKey"
        self._session = build_session({"apiKey": self._api_key})

    def confirm_status(
        self,
        *,
        first_name: str,
        last_name: str,
        birth_date: str,
        street_address_line1: str,
        city: str,
        state: str,
        country: str,
        zip_code: str,
        middle_name: Optional[str] = None,
        gender: Optional[str] = None,
        street_address_line2: Optional[str] = None,
        street_address_line3: Optional[str] = None,
        home_phone_number: Optional[str] = None,
        mothers_maiden_name: Optional[str] = None,
        birth_place_city: Optional[str] = None,
        birth_place_state: Optional[str] = None,
        birth_place_country: Optional[str] = None,
    ) -> ConfirmationStatus:
        """
        Confirm whether an individual is a Title 38 Veteran.

        Parameters
        ----------
        first_name:           Legal first name.
        last_name:            Legal last name.
        birth_date:           ISO date string, e.g. "1993-06-08".
        street_address_line1: Street address.
        city:                 City of residence.
        state:                State abbreviation, e.g. "TX".
        country:              Country code, e.g. "USA".
        zip_code:             ZIP code.
        middle_name:          Middle name (optional).
        gender:               "M" or "F" (optional, improves matching).
        home_phone_number:    Phone number (optional).
        mothers_maiden_name:  Mother's maiden name (optional).
        birth_place_*:        Birth location fields (optional).

        Returns
        -------
        ConfirmationStatus with .veteran_status of "confirmed" or "not confirmed".
        """
        # v1 API uses camelCase field names
        payload: dict = {
            "firstName": first_name,
            "lastName": last_name,
            "birthDate": birth_date,
            "streetAddressLine1": street_address_line1,
            "city": city,
            "state": state,
            "country": country,
            "zipCode": zip_code,
        }
        if middle_name:
            payload["middleName"] = middle_name
        if gender:
            payload["gender"] = gender
        if street_address_line2:
            payload["streetAddressLine2"] = street_address_line2
        if street_address_line3:
            payload["streetAddressLine3"] = street_address_line3
        if home_phone_number:
            payload["homePhoneNumber"] = home_phone_number
        if mothers_maiden_name:
            payload["mothersMaidenName"] = mothers_maiden_name
        if birth_place_city:
            payload["birthPlaceCity"] = birth_place_city
        if birth_place_state:
            payload["birthPlaceState"] = birth_place_state
        if birth_place_country:
            payload["birthPlaceCountry"] = birth_place_country

        resp = self._session.post(self._url, json=payload)
        _raise_for_status(resp)
        return ConfirmationStatus.from_dict(resp.json())
