"""
VA API Verify — CLI entry point.

Commands:
  confirm          Veteran Confirmation API (API key, simplest)
  status           Title 38 status (Verification API, OAuth)
  service-history  Military service episodes (Verification API, OAuth)
  disability       Disability ratings (Verification API, OAuth)
  benefits         Enrolled VA benefits (Verification API, OAuth)
  flashes          Eligibility flashes (Verification API, OAuth)

Credentials are read from environment variables:
  VA_API_KEY   — required for 'confirm'
  VA_TOKEN     — bearer token required for all Verification API commands
  VA_ENV       — "sandbox" (default) or "production"

Load from a .env file before running, e.g.:
  export $(grep -v '^#' .env | xargs) && python -m va_verify confirm ...
"""

import os
import sys
import click
from rich.console import Console

from .client.base import VAAPIError
from .client.confirmation import ConfirmationClient
from .client.verification import VerificationClient
from .display import (
    print_confirmation_status,
    print_veteran_status,
    print_service_history,
    print_disability_rating,
    print_enrolled_benefits,
    print_flashes,
)

err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Shared demographic options used by Verification API commands
# ---------------------------------------------------------------------------

def _veteran_demographic_options(f):
    """Decorator that adds the required demographic options for POST endpoints."""
    options = [
        click.option("--first-name", required=True, help="Legal first name"),
        click.option("--last-name", required=True, help="Legal last name"),
        click.option("--dob", required=True, metavar="YYYY-MM-DD", help="Date of birth"),
        click.option("--address", required=True, help="Street address line 1"),
        click.option("--city", required=True, help="City"),
        click.option("--country", required=True, default="USA", show_default=True, help="Country code"),
        click.option("--zip", "zipcode", required=True, help="ZIP code"),
        click.option("--state", default=None, help="State abbreviation"),
        click.option("--gender", default=None, type=click.Choice(["M", "F"]), help="Gender (optional)"),
        click.option("--middle-name", default=None, help="Middle name (optional)"),
    ]
    for opt in reversed(options):
        f = opt(f)
    return f


def _get_verification_client() -> VerificationClient:
    token = os.environ.get("VA_TOKEN")
    if not token:
        err_console.print(
            "[red]Error:[/red] VA_TOKEN environment variable is not set.\n"
            "Set it to your OAuth bearer token before running this command.\n"
            "  export VA_TOKEN='eyJ...'"
        )
        sys.exit(1)
    return VerificationClient(token=token)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option("0.1.0", prog_name="va-verify")
def cli():
    """VA API Verify — query VA veteran verification APIs from the terminal."""


# ---------------------------------------------------------------------------
# confirm — Veteran Confirmation API (API key)
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--first-name", required=True, help="Legal first name")
@click.option("--last-name", required=True, help="Legal last name")
@click.option("--dob", required=True, metavar="YYYY-MM-DD", help="Date of birth")
@click.option("--address", required=True, help="Street address line 1")
@click.option("--city", required=True, help="City")
@click.option("--state", required=True, help="State abbreviation, e.g. TX")
@click.option("--country", default="USA", show_default=True, help="Country code")
@click.option("--zip", "zip_code", required=True, help="ZIP code")
@click.option("--gender", default=None, type=click.Choice(["M", "F"]), help="Gender (optional, improves matching)")
@click.option("--middle-name", default=None, help="Middle name (optional)")
def confirm(first_name, last_name, dob, address, city, state, country, zip_code, gender, middle_name):
    """
    Confirm Veteran status via the Veteran Confirmation API.

    Uses an API key (set VA_API_KEY). This is the simplest query —
    it only confirms whether someone is a Title 38 Veteran.

    Sandbox test users are available at:
      https://developer.va.gov/explore/api/veteran-confirmation/test-users
    """
    try:
        client = ConfirmationClient()
        result = client.confirm_status(
            first_name=first_name,
            last_name=last_name,
            birth_date=dob,
            street_address_line1=address,
            city=city,
            state=state,
            country=country,
            zip_code=zip_code,
            gender=gender,
            middle_name=middle_name,
        )
        print_confirmation_status(result)
    except VAAPIError as e:
        err_console.print(f"[red]API Error:[/red] {e}")
        sys.exit(1)
    except RuntimeError as e:
        err_console.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# status — Title 38 status (Verification API)
# ---------------------------------------------------------------------------

@cli.command()
@_veteran_demographic_options
def status(first_name, last_name, dob, address, city, country, zipcode, state, gender, middle_name):
    """Confirm Title 38 Veteran status via the Verification API (requires OAuth token)."""
    try:
        client = _get_verification_client()
        result = client.get_status(
            first_name=first_name,
            last_name=last_name,
            birth_date=dob,
            street_address_line1=address,
            city=city,
            country=country,
            zipcode=zipcode,
            state=state,
            gender=gender,
            middle_name=middle_name,
        )
        print_veteran_status(result)
    except VAAPIError as e:
        err_console.print(f"[red]API Error:[/red] {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# service-history
# ---------------------------------------------------------------------------

@cli.command("service-history")
@_veteran_demographic_options
def service_history(first_name, last_name, dob, address, city, country, zipcode, state, gender, middle_name):
    """Retrieve military service history (requires OAuth token)."""
    try:
        client = _get_verification_client()
        result = client.get_service_history(
            first_name=first_name,
            last_name=last_name,
            birth_date=dob,
            street_address_line1=address,
            city=city,
            country=country,
            zipcode=zipcode,
            state=state,
            gender=gender,
            middle_name=middle_name,
        )
        print_service_history(result)
    except VAAPIError as e:
        err_console.print(f"[red]API Error:[/red] {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# disability
# ---------------------------------------------------------------------------

@cli.command()
@_veteran_demographic_options
def disability(first_name, last_name, dob, address, city, country, zipcode, state, gender, middle_name):
    """Retrieve VA disability ratings (requires OAuth token)."""
    try:
        client = _get_verification_client()
        result = client.get_disability_rating(
            first_name=first_name,
            last_name=last_name,
            birth_date=dob,
            street_address_line1=address,
            city=city,
            country=country,
            zipcode=zipcode,
            state=state,
            gender=gender,
            middle_name=middle_name,
        )
        print_disability_rating(result)
    except VAAPIError as e:
        err_console.print(f"[red]API Error:[/red] {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# benefits
# ---------------------------------------------------------------------------

@cli.command()
@_veteran_demographic_options
def benefits(first_name, last_name, dob, address, city, country, zipcode, state, gender, middle_name):
    """Retrieve enrolled VA benefits (requires OAuth token)."""
    try:
        client = _get_verification_client()
        result = client.get_enrolled_benefits(
            first_name=first_name,
            last_name=last_name,
            birth_date=dob,
            street_address_line1=address,
            city=city,
            country=country,
            zipcode=zipcode,
            state=state,
            gender=gender,
            middle_name=middle_name,
        )
        print_enrolled_benefits(result)
    except VAAPIError as e:
        err_console.print(f"[red]API Error:[/red] {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# flashes
# ---------------------------------------------------------------------------

@cli.command()
@_veteran_demographic_options
def flashes(first_name, last_name, dob, address, city, country, zipcode, state, gender, middle_name):
    """Retrieve eligibility flashes (Agent Orange, PACT Act, etc.) (requires OAuth token)."""
    try:
        client = _get_verification_client()
        result = client.get_flashes(
            first_name=first_name,
            last_name=last_name,
            birth_date=dob,
            street_address_line1=address,
            city=city,
            country=country,
            zipcode=zipcode,
            state=state,
            gender=gender,
            middle_name=middle_name,
        )
        print_flashes(result)
    except VAAPIError as e:
        err_console.print(f"[red]API Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
