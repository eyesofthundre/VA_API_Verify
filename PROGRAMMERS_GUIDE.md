# Programmer's Guide — VA API Verify

A technical reference for developers picking up this project. This guide covers the architecture, code structure, data flow, authentication mechanics, and how to extend or maintain the codebase.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Directory Structure](#3-directory-structure)
4. [Environment & Configuration](#4-environment--configuration)
5. [Layer-by-Layer Walkthrough](#5-layer-by-layer-walkthrough)
   - 5.1 [CLI Layer — `cli.py`](#51-cli-layer--clipy)
   - 5.2 [Client Layer — `client/`](#52-client-layer--client)
   - 5.3 [Model Layer — `models/`](#53-model-layer--modelsveteranpy)
   - 5.4 [Display Layer — `display/`](#54-display-layer--display)
   - 5.5 [Configuration — `config.py`](#55-configuration--configpy)
6. [Authentication — Two Methods Explained](#6-authentication--two-methods-explained)
7. [Data Flow — End to End](#7-data-flow--end-to-end)
8. [Error Handling Strategy](#8-error-handling-strategy)
9. [VA API Endpoints Reference](#9-va-api-endpoints-reference)
10. [Running & Testing Locally](#10-running--testing-locally)
11. [Common Extension Points](#11-common-extension-points)
12. [Dependency Notes](#12-dependency-notes)
13. [Known Gotchas & Edge Cases](#13-known-gotchas--edge-cases)

---

## 1. Project Overview

**VA API Verify** is a Python CLI tool that queries two official U.S. Department of Veterans Affairs (VA) REST APIs:

| API | Auth Method | Purpose |
|-----|-------------|---------|
| Veteran Confirmation API v1 | API Key (`apikey` header) | Single yes/no veteran status check |
| Veteran Service History and Eligibility API v2 | OAuth 2.0 Bearer Token | Detailed service history, disability, benefits, flashes |

The tool wraps these APIs behind a clean command-line interface using the **Click** library, formats results with **Rich**, and deserializes responses into typed **dataclasses**.

The sandbox environment (`https://sandbox-api.va.gov`) is safe to use during development — it accepts the same request shapes as production but returns synthetic test data.

---

## 2. Architecture Summary

The codebase follows a clean **4-layer architecture**:

```
┌──────────────────────────────────┐
│         CLI Layer (cli.py)       │  ← User-facing commands (Click)
├──────────────────────────────────┤
│       Client Layer (client/)     │  ← HTTP calls to VA APIs
├──────────────────────────────────┤
│       Model Layer (models/)      │  ← Typed dataclasses for API responses
├──────────────────────────────────┤
│      Display Layer (display/)    │  ← Rich-formatted terminal output
└──────────────────────────────────┘
         ↑ all layers read from ↑
         config.py  (env vars, base URLs)
```

Each layer has one job. The CLI doesn't know how HTTP works. The clients don't know how to render tables. The display doesn't know about the VA API schema. This separation makes it easy to swap or extend any one layer without touching the others.

---

## 3. Directory Structure

```
VA_API_Verify/
├── .env                        # Secret credentials (not committed to git)
├── .gitignore                  # Excludes .env, __pycache__, etc.
├── requirements.txt            # Runtime Python dependencies
├── openapi.json                # Official VA OpenAPI 3.0.1 spec (reference)
└── va_verify/                  # Main Python package
    ├── __init__.py             # Package marker (empty)
    ├── __main__.py             # Enables `python -m va_verify`
    ├── cli.py                  # Click command definitions
    ├── config.py               # Environment variable loading
    ├── client/
    │   ├── __init__.py
    │   ├── base.py             # Shared session builder, error type
    │   ├── confirmation.py     # ConfirmationClient (API key auth)
    │   └── verification.py     # VerificationClient (OAuth auth)
    ├── models/
    │   ├── __init__.py
    │   └── veteran.py          # All response dataclasses
    └── display/
        ├── __init__.py
        └── terminal.py         # Rich-based output functions
```

---

## 4. Environment & Configuration

**File:** `va_verify/config.py`

All configuration is read from environment variables, which are typically loaded from a `.env` file. In production you would inject these via your deployment environment (e.g., systemd, Docker, CI secrets).

### Variables

| Variable | Required For | Description |
|----------|-------------|-------------|
| `VA_ENV` | All commands | `sandbox` or `production` |
| `VA_API_KEY` | `confirm` command | API key for Veteran Confirmation API v1 |
| `VA_TOKEN` | All other commands | Full `Bearer <token>` string for Verification API v2 |

### How Config is Structured

```python
# config.py
class Config:
    env: str          # "sandbox" or "production"
    api_key: str      # raw key value
    token: str        # includes "Bearer " prefix

    @property
    def base_url(self) -> str:
        # Returns "https://sandbox-api.va.gov" or "https://api.va.gov"
```

Config is instantiated once per command invocation. There is no global singleton — each CLI command creates a fresh `Config()` when it runs.

### Loading Credentials at Runtime

The `.env` file is **not** automatically loaded by Python. The operating system environment must already have these variables set before `python3 -m va_verify` is called. In development, you typically:

```bash
# Option A: export manually before running
export VA_API_KEY=abc123
python3 -m va_verify confirm ...

# Option B: use a shell loader like direnv, or source manually
source .env
python3 -m va_verify confirm ...
```

> **Note:** If you want automatic `.env` loading, add `python-dotenv` to `requirements.txt` and call `load_dotenv()` at the top of `__main__.py`.

---

## 5. Layer-by-Layer Walkthrough

### 5.1 CLI Layer — `cli.py`

**Framework:** [Click](https://click.palletsprojects.com/)

Click turns Python functions into CLI commands using decorators. The entry point is a `@click.group()` called `cli`, and each subcommand is registered with `@cli.command()`.

#### Command Group Structure

```python
@click.group()
@click.version_option("0.1.0")
def cli():
    """VA Veteran Verification CLI"""
    pass
```

#### Shared Options Pattern

The Verification API commands all accept the same demographic fields. Rather than repeating 10+ `@click.option()` decorators on every command, they are bundled into a reusable decorator:

```python
def _veteran_demographic_options(f):
    """Stacks all common Click options onto a command function."""
    @click.option("--first-name", required=True)
    @click.option("--last-name", required=True)
    @click.option("--dob", required=True, help="YYYY-MM-DD")
    # ... more options ...
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper
```

This is applied to commands like:

```python
@cli.command()
@_veteran_demographic_options
def service_history(**kwargs):
    ...
```

#### Typical Command Body

Every command follows this exact pattern:

```python
@cli.command()
@_veteran_demographic_options
def disability(**kwargs):
    config = Config()                               # 1. Load config
    client = VerificationClient(config)             # 2. Create client
    result = client.get_disability_rating(**kwargs) # 3. Call API
    print_disability_rating(result)                 # 4. Render output
```

Error handling wraps the entire body in a `try/except VAAPIError` block that prints a red error panel via Rich.

---

### 5.2 Client Layer — `client/`

#### `base.py` — Shared HTTP Utilities

```python
class VAAPIError(Exception):
    """Raised when the VA API returns a non-2xx response."""
    def __init__(self, status_code: int, message: str): ...
```

```python
def _raise_for_status(response: requests.Response) -> None:
    """
    Converts HTTP errors into VAAPIError.
    Tries to parse JSON error body from VA API response first.
    Falls back to HTTP status text if JSON parsing fails.
    """

def build_session(headers: dict) -> requests.Session:
    """
    Creates a requests.Session with the given headers pre-set.
    Using a Session (rather than raw requests.get) enables connection
    pooling and makes it easier to add retry logic later.
    """
```

#### `confirmation.py` — Veteran Confirmation API v1

```python
class ConfirmationClient:
    ENDPOINT = "/services/veteran-confirmation/v1/status"

    def __init__(self, config: Config):
        self.session = build_session({
            "apikey": config.api_key,
            "Content-Type": "application/json",
        })
        self.base_url = config.base_url

    def confirm_veteran_status(self, **kwargs) -> ConfirmationStatus:
        payload = self._build_payload(**kwargs)   # camelCase field mapping
        response = self.session.post(url, json=payload)
        _raise_for_status(response)
        return ConfirmationStatus.from_dict(response.json())
```

**Important:** This API uses **camelCase** field names in the request body (e.g., `firstName`, `streetAddressLine1`). This differs from the Verification API which uses **snake_case**.

#### `verification.py` — Veteran Verification API v2

```python
class VerificationClient:
    BASE_PATH = "/services/veteran_verification/v2"

    def __init__(self, config: Config):
        self.session = build_session({
            "Authorization": config.token,   # "Bearer <token>"
            "Content-Type": "application/json",
        })

    def get_veteran_status(self, **kwargs) -> VeteranStatus: ...
    def get_service_history(self, **kwargs) -> ServiceHistory: ...
    def get_disability_rating(self, **kwargs) -> DisabilityRating: ...
    def get_enrolled_benefits(self, **kwargs) -> list[EnrolledBenefit]: ...
    def get_flashes(self, **kwargs) -> list[Flash]: ...
```

Each method:
1. Builds a JSON payload with snake_case field names
2. POSTs to the appropriate endpoint
3. Calls `_raise_for_status()`
4. Deserializes the JSON response into the appropriate dataclass

**Why POST for reads?** The VA Verification API uses POST instead of GET for all queries. This is because the request body contains PII (personally identifiable information) that should not appear in server logs or browser history as URL query parameters.

---

### 5.3 Model Layer — `models/veteran.py`

All API response objects are Python **dataclasses** with a `from_dict()` class method for JSON deserialization.

#### Why Dataclasses?

- Type hints on every field make the data shape explicit and IDE-friendly
- `@dataclass` auto-generates `__init__`, `__repr__`, and `__eq__`
- `from_dict()` centralizes the JSON-to-object mapping, so the rest of the codebase never has to do `response["data"]["attributes"]["veteran_status"]`

#### Model Hierarchy

```
ConfirmationStatus          ← confirm command response
  └── veteran_status: str

VeteranStatus               ← status command response
  ├── veteran_status: str
  └── not_confirmed_reason: str | None

ServiceHistory              ← service-history command response
  ├── episodes: list[ServiceEpisode]
  └── military_summary: dict
        ServiceEpisode
          ├── branch_of_service: str
          ├── service_type: str
          ├── start_date / end_date: str
          ├── pay_grade: str
          ├── discharge_status: str
          └── deployments: list[Deployment]
                Deployment
                  ├── location: str
                  ├── start_date: str
                  └── end_date: str

DisabilityRating            ← disability command response
  ├── combined_disability_rating: int
  ├── combined_effective_date: str
  └── individual_ratings: list[IndividualRating]
        IndividualRating
          ├── decision: str
          ├── diagnostic_code: str
          ├── diagnostic_text: str
          ├── rating_percentage: int
          ├── effective_date: str
          └── static_ind: bool

EnrolledBenefit             ← benefits command response (list of these)
  ├── program_code: str
  ├── program_name: str
  └── award_effective_date: str

Flash                       ← flashes command response (list of these)
  └── flash_name: str
```

#### `from_dict()` Pattern

```python
@dataclass
class ServiceEpisode:
    branch_of_service: str
    deployments: list[Deployment]

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceEpisode":
        return cls(
            branch_of_service=data.get("branch_of_service", "Unknown"),
            deployments=[Deployment.from_dict(d) for d in data.get("deployments", [])],
        )
```

All `from_dict()` methods use `.get()` with sensible defaults so the program doesn't crash if the API omits optional fields.

---

### 5.4 Display Layer — `display/terminal.py`

**Framework:** [Rich](https://rich.readthedocs.io/)

Rich provides styled terminal output: colored text, tables, panels, and progress bars. This layer accepts model objects and renders them — it has no knowledge of the VA API or HTTP.

#### Main Functions

| Function | Input | Output |
|----------|-------|--------|
| `print_confirmation_status(status)` | `ConfirmationStatus` | Green/Red panel |
| `print_veteran_status(status)` | `VeteranStatus` | Panel with optional reason |
| `print_service_history(history)` | `ServiceHistory` | Tables per episode + deployments |
| `print_disability_rating(rating)` | `DisabilityRating` | Summary panel + individual ratings table |
| `print_enrolled_benefits(benefits)` | `list[EnrolledBenefit]` | Benefits table |
| `print_flashes(flashes)` | `list[Flash]` | Simple flash list |

#### Color Logic Example

```python
# Disability rating color coding
if combined >= 100:
    color = "green"
elif combined >= 50:
    color = "yellow"
else:
    color = "red"
```

#### Rich Console Usage

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Panels (bordered boxes)
console.print(Panel("[green]CONFIRMED[/green]", title="Veteran Status"))

# Tables
table = Table("Branch", "Start Date", "End Date")
table.add_row("Army", "2001-01-01", "2005-12-31")
console.print(table)
```

---

### 5.5 Configuration — `config.py`

```python
import os

class Config:
    def __init__(self):
        self.env = os.environ.get("VA_ENV", "sandbox")
        self.api_key = os.environ.get("VA_API_KEY", "")
        self.token = os.environ.get("VA_TOKEN", "")

    @property
    def base_url(self) -> str:
        if self.env == "production":
            return "https://api.va.gov"
        return "https://sandbox-api.va.gov"
```

Simple, no magic. If environment variables are missing, the values default to empty strings, which will cause a `401 Unauthorized` from the VA API — a clear and actionable error.

---

## 6. Authentication — Two Methods Explained

### Method 1: API Key (Confirmation API v1)

The VA Confirmation API uses a simple API key sent as a custom HTTP header:

```http
POST /services/veteran-confirmation/v1/status HTTP/1.1
Host: sandbox-api.va.gov
apikey: your-api-key-here
Content-Type: application/json

{ "firstName": "John", "lastName": "Doe", ... }
```

**Where to get it:** VA Developer Portal → Apply for Veteran Confirmation API access.

### Method 2: OAuth 2.0 Bearer Token (Verification API v2)

The Verification API uses OAuth 2.0, specifically the **Client Credentials Grant (CCG)** flow. This is a machine-to-machine flow where your application exchanges a client ID + secret for a short-lived JWT (JSON Web Token).

```http
POST /services/veteran_verification/v2/status HTTP/1.1
Host: sandbox-api.va.gov
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{ "first_name": "John", "last_name": "Doe", ... }
```

**Token Lifetime:** Typically 1 hour. When expired you get a `401`. You must re-obtain a token from the VA auth endpoint.

> **Note:** This project currently expects the token to already be set in `VA_TOKEN`. It does **not** implement the OAuth token refresh flow. Adding token refresh would be a natural next enhancement — see [Section 11](#11-common-extension-points).

**camelCase vs snake_case:** The two APIs use different field naming conventions for the same demographic data:

| Field | Confirmation API (v1) | Verification API (v2) |
|-------|----------------------|-----------------------|
| First name | `firstName` | `first_name` |
| Street address | `streetAddressLine1` | `street_line` |
| Date of birth | `birthDate` | `birth_date` |

Each client handles this mapping internally in its `_build_payload()` method.

---

## 7. Data Flow — End to End

Here is the complete path of a `service-history` command:

```
User runs:
  python3 -m va_verify service-history --first-name John --last-name Doe ...
        │
        ▼
__main__.py
  calls: cli()   ← Click entry point
        │
        ▼
cli.py: service_history(**kwargs)
  1. Config()                  ← reads VA_ENV, VA_TOKEN from env
  2. VerificationClient(config) ← builds requests.Session with Bearer header
  3. client.get_service_history(first_name="John", last_name="Doe", ...)
        │
        ▼
client/verification.py: get_service_history()
  1. _build_payload(**kwargs)  ← maps CLI args to VA API JSON body
  2. session.post(url, json=payload)  ← HTTPS POST to sandbox-api.va.gov
  3. _raise_for_status(response)      ← raises VAAPIError if not 2xx
  4. ServiceHistory.from_dict(response.json()["data"]["attributes"])
        │
        ▼
models/veteran.py: ServiceHistory.from_dict(data)
  → Constructs ServiceHistory with list[ServiceEpisode]
  → Each ServiceEpisode contains list[Deployment]
        │
        ▼
cli.py: print_service_history(result)
        │
        ▼
display/terminal.py: print_service_history(history)
  → Renders Rich tables for each service episode
  → Renders deployment sub-table if deployments exist
        │
        ▼
Terminal output displayed to user
```

---

## 8. Error Handling Strategy

### `VAAPIError`

Defined in `client/base.py`. All HTTP-level errors are converted to this exception type:

```python
class VAAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"VA API Error {status_code}: {message}")
```

`_raise_for_status()` converts the raw `requests.Response` into a `VAAPIError`:

```python
def _raise_for_status(response: requests.Response) -> None:
    if response.status_code < 400:
        return
    try:
        error_body = response.json()
        message = error_body.get("errors", [{}])[0].get("detail", response.reason)
    except Exception:
        message = response.reason
    raise VAAPIError(response.status_code, message)
```

### CLI Error Handling

Each CLI command catches `VAAPIError` and renders a red panel:

```python
try:
    result = client.get_service_history(...)
    print_service_history(result)
except VAAPIError as e:
    console.print(Panel(f"[red]{e}[/red]", title="API Error"))
    raise SystemExit(1)
```

### Common HTTP Errors from VA API

| Status Code | Meaning | Fix |
|-------------|---------|-----|
| 401 | Bad or missing credentials | Check `VA_API_KEY` / `VA_TOKEN` in `.env` |
| 403 | Authorized but not permitted | Your key doesn't have access to this endpoint |
| 404 | Veteran not found | Add more demographic fields to improve match |
| 422 | Invalid request body | Check field names and formats |
| 429 | Rate limited | Slow down requests; sandbox has low limits |
| 500 | VA server error | Transient; retry after a moment |

---

## 9. VA API Endpoints Reference

### Veteran Confirmation API v1

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/services/veteran-confirmation/v1/status` | `apikey` header |

**Request Body Fields (camelCase):**

```json
{
  "firstName": "John",
  "middleName": "Robert",
  "lastName": "Doe",
  "birthDate": "1980-01-15",
  "gender": "M",
  "streetAddressLine1": "123 Main St",
  "city": "Austin",
  "state": "TX",
  "zipCode": "78701",
  "country": "USA",
  "phone": "5125551234",
  "birthPlaceCity": "San Antonio",
  "birthPlaceState": "TX"
}
```

**Response:**

```json
{
  "veteran_status": "confirmed"   // or "not confirmed"
}
```

---

### Veteran Service History and Eligibility API v2

Base path: `/services/veteran_verification/v2`

All endpoints use POST with the same demographic body (snake_case fields):

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "birth_date": "1980-01-15",
  "street_line": "123 Main St",
  "city": "Austin",
  "state": "TX",
  "zip_code": "78701",
  "country": "USA"
}
```

| Endpoint | Returns |
|----------|---------|
| `/status` | Veteran status + optional reason |
| `/service_history` | List of service episodes + deployments |
| `/disability_rating` | Combined rating + individual ratings |
| `/enrolled_benefits` | List of enrolled benefit programs |
| `/flashes` | List of eligibility flash names |

For complete response schemas, refer to `openapi.json` in the project root.

---

## 10. Running & Testing Locally

### Run in Sandbox Mode

```bash
# Set up environment
export VA_ENV=sandbox
export VA_API_KEY=your_sandbox_api_key
export VA_TOKEN="Bearer your_sandbox_oauth_token"

# Run any command
python3 -m va_verify confirm \
  --first-name John \
  --last-name Doe \
  --dob 1990-05-20 \
  --address "1 VA Drive" \
  --city Washington \
  --state DC \
  --zip 20001 \
  --country USA
```

### Verify Installation

```bash
python3 -m va_verify --help
```

Should print the available commands without error.

### Run with a Virtual Environment (Recommended)

```bash
# Create venv
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python3 -m va_verify --help

# Deactivate when done
deactivate
```

### No Automated Tests Yet

There is currently no test suite in this project. If you are adding one:

- Use `pytest` as the test framework
- Mock the `requests.Session` with `unittest.mock.patch` or `responses` library to avoid real HTTP calls in unit tests
- Integration tests should target the sandbox environment
- Test `from_dict()` methods on models independently with fixture JSON

---

## 11. Common Extension Points

### Add a New VA API Endpoint

1. **Add a method to `VerificationClient`** in `client/verification.py`:

   ```python
   def get_new_endpoint(self, **kwargs) -> NewModel:
       payload = self._build_payload(**kwargs)
       response = self.session.post(f"{self.base_url}{self.BASE_PATH}/new_endpoint", json=payload)
       _raise_for_status(response)
       return NewModel.from_dict(response.json()["data"]["attributes"])
   ```

2. **Add a dataclass** to `models/veteran.py`:

   ```python
   @dataclass
   class NewModel:
       some_field: str

       @classmethod
       def from_dict(cls, data: dict) -> "NewModel":
           return cls(some_field=data.get("some_field", ""))
   ```

3. **Add a display function** to `display/terminal.py`:

   ```python
   def print_new_model(model: NewModel) -> None:
       console.print(Panel(model.some_field, title="New Endpoint"))
   ```

4. **Add a CLI command** to `cli.py`:

   ```python
   @cli.command()
   @_veteran_demographic_options
   def new_command(**kwargs):
       config = Config()
       client = VerificationClient(config)
       result = client.get_new_endpoint(**kwargs)
       print_new_model(result)
   ```

### Add OAuth Token Auto-Refresh

Currently `VA_TOKEN` must be set manually. To automate this:

1. Add `VA_CLIENT_ID` and `VA_CLIENT_SECRET` to `.env`
2. In `Config`, add a `get_token()` method that POSTs to the VA token endpoint
3. In `VerificationClient.__init__`, call `config.get_token()` and use the result
4. Add a `requests` adapter with retry logic to catch `401` responses and re-fetch the token

### Add JSON / CSV Output

Add a `--output-format` option to commands:

```python
@click.option("--output-format", type=click.Choice(["table", "json", "csv"]), default="table")
def service_history(output_format, **kwargs):
    result = client.get_service_history(**kwargs)
    if output_format == "json":
        import json, dataclasses
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        print_service_history(result)
```

### Support `.env` Auto-Loading

Add to `requirements.txt`:

```
python-dotenv>=1.0
```

Add to `va_verify/__main__.py` (at the very top, before the import of `cli`):

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 12. Dependency Notes

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >=2.31 | HTTP client for VA API calls |
| `click` | >=8.1 | CLI framework — decorators for commands/options |
| `rich` | >=13.0 | Terminal formatting — tables, panels, color |

All are pure Python and install cleanly on M1 Macs without Rosetta.

### Why `requests` over `httpx`?

`requests` was chosen for simplicity and wide familiarity. `httpx` would be a reasonable drop-in if async support or HTTP/2 is ever needed — the interface is nearly identical.

### Why `click` over `argparse`?

Click provides a better developer experience with decorators, type coercion, help text generation, and command groups. `argparse` is in the standard library but requires significantly more boilerplate for the same result.

---

## 13. Known Gotchas & Edge Cases

### camelCase vs snake_case Request Bodies

The two VA APIs have different field naming conventions (see [Section 6](#6-authentication--two-methods-explained)). If you add a new field to the demographic payload, make sure you add it in the right format for each client.

### `VA_TOKEN` Must Include "Bearer "

The `VA_TOKEN` environment variable must be the **full** Authorization header value:

```
VA_TOKEN=Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Not just the raw token. If you set it without the `Bearer ` prefix, the VA API will return a `401`.

### Sandbox Returns Synthetic Data

The sandbox does not contain real veteran records. It responds with test fixtures based on the request content. Do not attempt to verify real people using the sandbox environment.

### Rate Limiting in Sandbox

The sandbox environment has very low rate limits compared to production. If you are running automated tests or scripts, add a short `time.sleep(0.5)` between calls to avoid `429 Too Many Requests`.

### `response.json()["data"]["attributes"]` Assumption

The `VerificationClient` methods assume the VA API always returns data under `response.json()["data"]["attributes"]`. This follows the JSON:API specification that the VA uses. If a future endpoint deviates from this, you will need to adjust the deserialization path.

### Optional Demographic Fields Improve Match Rate

The VA's matching algorithm uses a confidence score based on how many fields match. If you only provide first name, last name, and date of birth, you may get a `404` for someone who is in the system. Adding `--middle-name`, `--gender`, or `--birth-place` significantly improves the match rate.

### `openapi.json` Is the Source of Truth

The project includes `openapi.json`, the official VA OpenAPI 3.0.1 specification. If there is ever a discrepancy between this code and the VA API's actual behavior, the OpenAPI spec is authoritative. Use it to verify field names, types, and required vs. optional fields.

---

## Quick Onboarding Checklist

- [ ] Clone the repo and `cd` into it
- [ ] Create and activate a virtual environment
- [ ] `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env` (or create `.env` manually) and fill in your credentials
- [ ] Run `python3 -m va_verify --help` to confirm the CLI loads
- [ ] Read `openapi.json` for the full API spec when working on a new endpoint
- [ ] Follow the 4-layer architecture: CLI → Client → Model → Display

---

*Questions? Check the VA Developer Portal documentation or file an issue in the project repository.*
