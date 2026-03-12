"""
Terminal display layer using Rich.

All display functions accept model objects and render them to the terminal.
Keeping display logic isolated here makes it straightforward to swap in a
GUI renderer later — just add a gui.py alongside this file and import it
instead in cli.py.
"""

from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

from ..models import (
    ConfirmationStatus,
    VeteranStatus,
    ServiceHistory,
    DisabilityRating,
    EnrolledBenefit,
    Flash,
)

console = Console()


def _status_color(status: str) -> str:
    return "green" if status.lower() == "confirmed" else "red"


def print_confirmation_status(result: ConfirmationStatus) -> None:
    status = result.veteran_status
    color = _status_color(status)
    panel = Panel(
        Text(status.upper(), style=f"bold {color}", justify="center"),
        title="[bold]Veteran Confirmation API[/bold]",
        subtitle="Title 38 Status",
        border_style=color,
        padding=(1, 4),
    )
    console.print(panel)


def print_veteran_status(result: VeteranStatus) -> None:
    status = result.veteran_status
    color = _status_color(status)
    lines = Text(status.upper(), style=f"bold {color}")
    if result.not_confirmed_reason:
        lines.append(f"\nReason: {result.not_confirmed_reason}", style="yellow")
    panel = Panel(
        lines,
        title="[bold]Veteran Status[/bold]",
        subtitle="Title 38 (Service History & Eligibility API)",
        border_style=color,
        padding=(1, 4),
    )
    console.print(panel)


def print_service_history(history: ServiceHistory) -> None:
    if not history.episodes:
        console.print("[yellow]No service history records found.[/yellow]")
        return

    for i, ep in enumerate(history.episodes, 1):
        table = Table(
            title=f"Service Episode {i} — {ep.branch_of_service}",
            box=box.ROUNDED,
            show_header=False,
            title_style="bold cyan",
        )
        table.add_column("Field", style="bold", min_width=22)
        table.add_column("Value")

        table.add_row("Name", f"{ep.first_name} {ep.last_name}")
        table.add_row("Branch", ep.branch_of_service)
        table.add_row("Service Type", ep.service_type or "—")
        table.add_row("Component", ep.component_of_service or "—")
        table.add_row("Pay Grade", ep.pay_grade or "—")
        table.add_row("Start Date", ep.start_date or "—")
        table.add_row("End Date", ep.end_date or "—")
        table.add_row("Discharge Status", ep.discharge_status or "—")
        table.add_row("Separation Reason", ep.separation_reason or "—")
        table.add_row("Combat Pay", "Yes" if ep.combat_pay else "No")

        if ep.deployments:
            dep_lines = "\n".join(
                f"{d.location}: {d.start_date} – {d.end_date}" for d in ep.deployments
            )
            table.add_row("Deployments", dep_lines)

        console.print(table)
        console.print()

    if history.military_summary:
        console.print("[bold]Military Summary[/bold]")
        for k, v in history.military_summary.items():
            console.print(f"  {k}: {v}")


def print_disability_rating(rating: DisabilityRating) -> None:
    combined = rating.combined_disability_rating
    color = "green" if combined == 100 else "yellow" if combined and combined >= 50 else "white"

    console.print(Panel(
        Text(
            f"{combined}% Combined Rating" if combined is not None else "No combined rating",
            style=f"bold {color}",
            justify="center",
        ),
        title="[bold]Disability Rating[/bold]",
        subtitle=f"Effective: {rating.combined_effective_date or '—'}",
        border_style=color,
        padding=(0, 4),
    ))

    if not rating.individual_ratings:
        console.print("[yellow]No individual ratings found.[/yellow]")
        return

    table = Table(
        title="Individual Ratings",
        box=box.SIMPLE_HEAD,
        title_style="bold",
    )
    table.add_column("Diagnosis", style="cyan", max_width=40)
    table.add_column("Decision")
    table.add_column("Rating %", justify="right")
    table.add_column("Effective Date")
    table.add_column("End Date")
    table.add_column("Static")

    for r in rating.individual_ratings:
        table.add_row(
            r.diagnostic_type_name or r.diagnostic_text or r.diagnostic_type_code or "—",
            r.decision or "—",
            str(r.rating_percentage) if r.rating_percentage is not None else "—",
            r.effective_date or "—",
            r.rating_end_date or "—",
            "Yes" if r.static_ind else "No",
        )

    console.print(table)


def print_enrolled_benefits(benefits: list[EnrolledBenefit]) -> None:
    if not benefits:
        console.print("[yellow]No enrolled benefits found.[/yellow]")
        return

    table = Table(title="Enrolled VA Benefits", box=box.ROUNDED, title_style="bold cyan")
    table.add_column("Program Code", style="bold")
    table.add_column("Program Name", style="cyan")
    table.add_column("Effective Date")

    for b in benefits:
        table.add_row(b.program_code, b.program_name, b.award_effective_date or "—")

    console.print(table)


def print_flashes(flashes: list[Flash]) -> None:
    if not flashes:
        console.print("[yellow]No eligibility flashes found.[/yellow]")
        return

    table = Table(title="Eligibility Flashes", box=box.ROUNDED, title_style="bold cyan")
    table.add_column("Flash", style="cyan")

    for f in flashes:
        table.add_row(f.flash_name)

    console.print(table)
