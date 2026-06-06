"""
VAIBHAV GROWTH ENGINE - Main CLI Entry Point
============================================
AI-Powered Lead Discovery & Outreach Platform
Author: Vaibhav Sonava
GitHub: github.com/Vaibhavsonava2005
"""

import io
import sys
import click
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box
from rich.prompt import Confirm, Prompt
from rich.padding import Padding
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.align import Align
from rich.style import Style
from rich.markup import escape

from src.pipeline.growth_pipeline import GrowthPipeline
from src.analytics.metrics import AnalyticsEngine
from src.crm.crm_manager import CRMManager
from src.agents.ai_router import AIRouter
from src.config.settings import settings
from src.config.constants import APP_NAME, APP_VERSION, APP_AUTHOR, APP_GITHUB
from src.utils.logger import logger
from src.utils.validators import validate_domain
from src.services.hunter import HunterService
from src.services.prospeo import ProspeoService
from src.services.apollo import ApolloService
from src.services.brevo import BrevoService
import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Global console instance — UTF-8 safe on Windows
# ---------------------------------------------------------------------------
console = Console(
    file=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stdout, "buffer")
    else sys.stdout
)


# ---------------------------------------------------------------------------
# Banner & print helpers
# ---------------------------------------------------------------------------

def print_banner() -> None:
    """Render the VAIBHAV GROWTH ENGINE banner to the terminal."""
    banner_lines = [
        "╔════════════════════════════════════════════════════════╗",
        "║         VAIBHAV GROWTH ENGINE v1.0.0                  ║",
        "║   AI-Powered Lead Discovery & Outreach Platform       ║",
        "║            Created by Vaibhav Sonava                  ║",
        "║    github.com/Vaibhavsonava2005                       ║",
        "╚════════════════════════════════════════════════════════╝",
    ]
    banner_text = Text()
    for i, line in enumerate(banner_lines):
        if i == 0 or i == len(banner_lines) - 1:
            banner_text.append(line + "\n", style="bold cyan")
        elif i == 1:
            banner_text.append(line + "\n", style="bold bright_white")
        elif i == 2:
            banner_text.append(line + "\n", style="bold blue")
        elif i == 3:
            banner_text.append(line + "\n", style="bold magenta")
        else:
            banner_text.append(line + "\n", style="bold green")

    console.print()
    console.print(Align.center(banner_text))
    console.print(
        Align.center(
            Text(
                f"  {datetime.now().strftime('%A, %d %B %Y  •  %H:%M:%S')}  ",
                style="dim italic",
            )
        )
    )
    console.print()


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


# ---------------------------------------------------------------------------
# Safety checkpoint
# ---------------------------------------------------------------------------

def _render_safety_checkpoint(
    companies: int,
    decision_makers: int,
    verified_emails: int,
    campaign_name: str,
    emails_ready: int,
    ai_provider: str,
    mode: str,
) -> str:
    lines = [
        "╔════════════════════════════════════════╗",
        "║         CAMPAIGN SAFETY CHECK         ║",
        "╠════════════════════════════════════════╣",
        f"║  Companies Found:  {companies:<19}║",
        f"║  Decision Makers:  {decision_makers:<19}║",
        f"║  Verified Emails:  {verified_emails:<19}║",
        f"║  Campaign Name:    {campaign_name[:19]:<19}║",
        f"║  Emails Ready:     {emails_ready:<19}║",
        "║                                       ║",
        f"║  AI Provider:      {ai_provider:<19}║",
        f"║  Mode:             {mode:<19}║",
        "╚════════════════════════════════════════╝",
    ]
    return "\n".join(lines)


def show_safety_checkpoint(
    companies: int,
    decision_makers: int,
    verified_emails: int,
    campaign_name: str,
    emails_ready: int,
    ai_provider: str,
    dry_run: bool,
) -> bool:
    mode = "DRY-RUN" if dry_run else "LIVE"
    checkpoint = _render_safety_checkpoint(
        companies=companies,
        decision_makers=decision_makers,
        verified_emails=verified_emails,
        campaign_name=campaign_name,
        emails_ready=emails_ready,
        ai_provider=ai_provider,
        mode=mode,
    )

    console.print()
    console.rule("[bold yellow]⚠  MANDATORY SAFETY CHECK  ⚠[/bold yellow]", style="yellow")
    console.print()

    color = "yellow" if dry_run else "bold red"
    console.print(Align.center(Text(checkpoint, style=color)))
    console.print()

    if dry_run:
        print_info("DRY-RUN mode: emails will be generated but NOT delivered.")
    else:
        print_warning("LIVE mode: approving will dispatch real emails to real contacts.")

    console.print()
    approved: bool = Confirm.ask(
        "[bold white]Proceed with campaign?[/bold white]",
        default=False,
    )
    console.print()
    return approved


# ---------------------------------------------------------------------------
# Summary card
# ---------------------------------------------------------------------------

def show_summary_card(
    domain: str,
    campaign_name: str,
    companies_found: int,
    contacts_found: int,
    emails_sent: int,
    emails_skipped: int,
    duration_seconds: float,
    dry_run: bool,
    report_path: Optional[str] = None,
) -> None:
    console.print()
    console.rule("[bold green]Campaign Complete[/bold green]", style="green")
    console.print()

    summary_table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="green",
        padding=(0, 2),
        expand=False,
    )
    summary_table.add_column("Metric", style="bold cyan", min_width=22)
    summary_table.add_column("Value", style="bold white", min_width=20)

    mode_label = Text("DRY-RUN", style="bold yellow") if dry_run else Text("LIVE", style="bold green")

    summary_table.add_row("Target Domain", domain)
    summary_table.add_row("Campaign Name", campaign_name)
    summary_table.add_row("Companies Discovered", str(companies_found))
    summary_table.add_row("Contacts Found", str(contacts_found))
    summary_table.add_row("Emails Sent", str(emails_sent))
    summary_table.add_row("Emails Skipped", str(emails_skipped))
    summary_table.add_row("Duration", f"{duration_seconds:.1f}s")
    summary_table.add_row("Mode", mode_label)
    if report_path:
        summary_table.add_row("Report Saved To", report_path)

    console.print(Align.center(summary_table))
    console.print()

    if emails_sent > 0:
        print_success(
            f"Campaign '{campaign_name}' completed — "
            f"{emails_sent} email(s) dispatched."
        )
    elif dry_run:
        print_info(
            f"Dry-run preview for '{campaign_name}' finished — "
            f"no emails were sent."
        )
    else:
        print_warning("Campaign completed but no emails were sent.")

    console.print()


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="1.0.0", prog_name="VAIBHAV GROWTH ENGINE")
def cli() -> None:
    """VAIBHAV GROWTH ENGINE - AI-Powered Lead Discovery & Outreach Platform"""
    print_banner()


# ---------------------------------------------------------------------------
# run command
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--domain", "-d",
    required=True,
    help="Target company domain (e.g. hubspot.com)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview emails without sending",
)
@click.option(
    "--product", "-p",
    default="AI Solutions",
    show_default=True,
    help="Your product/service to promote",
)
@click.option(
    "--name", "-n",
    default=None,
    help="Campaign name (auto-generated if omitted)",
)
@click.option(
    "--output", "-o",
    default="data",
    show_default=True,
    help="Output directory for reports",
)
def run(
    domain: str,
    dry_run: bool,
    product: str,
    name: Optional[str],
    output: str,
) -> None:
    """Run the full growth pipeline for a target domain."""
    start_time = datetime.now()

    # ------------------------------------------------------------------
    # 1. Validate domain
    # ------------------------------------------------------------------
    console.rule("[bold blue]Step 1 · Domain Validation[/bold blue]", style="blue")
    try:
        domain = validate_domain(domain)
    except ValueError as e:
        print_error(f"Invalid domain: {e}")
        sys.exit(1)
    print_success(f"Domain validated: [bold cyan]{domain}[/bold cyan]")
    console.print()

    # ------------------------------------------------------------------
    # 2. Show run configuration
    # ------------------------------------------------------------------
    campaign_name: str = name or f"{domain.split('.')[0].title()}-{datetime.now().strftime('%Y%m%d-%H%M')}"

    config_table = Table(
        title="[bold]Run Configuration[/bold]",
        box=box.ROUNDED,
        border_style="blue",
        show_header=False,
        padding=(0, 2),
    )
    config_table.add_column("Key", style="bold cyan")
    config_table.add_column("Value", style="white")
    config_table.add_row("Domain", domain)
    config_table.add_row("Campaign Name", campaign_name)
    config_table.add_row("Product", product)
    config_table.add_row("Mode", "[yellow]DRY-RUN[/yellow]" if dry_run else "[green]LIVE[/green]")
    config_table.add_row("Output Directory", output)
    console.print(Align.center(config_table))
    console.print()

    # ------------------------------------------------------------------
    # 3. Run pipeline
    # ------------------------------------------------------------------
    console.rule("[bold blue]Step 2 · Running Growth Pipeline[/bold blue]", style="blue")

    try:
        pipeline = GrowthPipeline()
        campaign = pipeline.run(
            domain=domain,
            campaign_name=campaign_name,
            sender_product=product,
            dry_run=dry_run,
        )
    except Exception as exc:
        print_error(f"Pipeline failed: {escape(str(exc))}")
        logger.exception("Pipeline error")
        sys.exit(1)

    console.print()
    print_success("Pipeline completed successfully.")

    # ------------------------------------------------------------------
    # 4. Safety checkpoint
    # ------------------------------------------------------------------
    console.rule("[bold blue]Step 3 · Safety Checkpoint[/bold blue]", style="blue")

    ai_provider = getattr(pipeline.ai_router, "last_used_provider", "template")
    companies_count = campaign.companies_found
    contacts_count = campaign.contacts_found
    verified_emails = campaign.emails_found
    emails_ready = len(campaign.email_drafts)

    approved = show_safety_checkpoint(
        companies=companies_count,
        decision_makers=contacts_count,
        verified_emails=verified_emails,
        campaign_name=campaign_name,
        emails_ready=emails_ready,
        ai_provider=str(ai_provider),
        dry_run=dry_run,
    )

    if not approved:
        print_warning("Campaign cancelled by user. No emails were sent.")
        console.print()
        sys.exit(0)

    # ------------------------------------------------------------------
    # 5. Send campaign
    # ------------------------------------------------------------------
    console.rule("[bold blue]Step 4 · Sending Campaign[/bold blue]", style="blue")

    try:
        send_result = pipeline.send_campaign(campaign, dry_run=dry_run)
        emails_sent = campaign.emails_sent
        emails_skipped = emails_ready - emails_sent
    except Exception as exc:
        print_error(f"Send failed: {escape(str(exc))}")
        logger.exception("Send error")
        emails_sent = 0
        emails_skipped = emails_ready

    console.print()
    print_success(f"Sent {emails_sent} email(s).")

    # ------------------------------------------------------------------
    # 6. Save to CRM
    # ------------------------------------------------------------------
    try:
        crm = CRMManager()
        crm.save_campaign(campaign)
        print_success("Campaign data persisted to CRM.")
    except Exception as exc:
        print_warning(f"CRM save failed (non-fatal): {exc}")

    # ------------------------------------------------------------------
    # 7. Summary card
    # ------------------------------------------------------------------
    duration = (datetime.now() - start_time).total_seconds()
    show_summary_card(
        domain=domain,
        campaign_name=campaign_name,
        companies_found=companies_count,
        contacts_found=contacts_count,
        emails_sent=emails_sent,
        emails_skipped=emails_skipped,
        duration_seconds=duration,
        dry_run=dry_run,
        report_path=None,
    )


# ---------------------------------------------------------------------------
# preview command
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--domain", "-d",
    required=True,
    help="Target domain",
)
@click.option(
    "--product", "-p",
    default="AI Solutions",
    show_default=True,
    help="Product to promote",
)
def preview(domain: str, product: str) -> None:
    """Preview generated emails without sending."""
    try:
        domain = validate_domain(domain)
    except ValueError as e:
        print_error(f"Invalid domain: {e}")
        sys.exit(1)

    print_info(f"Generating email previews for [bold cyan]{domain}[/bold cyan] …")
    console.print()

    campaign_name = f"preview-{domain.split('.')[0]}-{datetime.now().strftime('%H%M%S')}"

    try:
        pipeline = GrowthPipeline()
        campaign = pipeline.run(
            domain=domain,
            campaign_name=campaign_name,
            sender_product=product,
            dry_run=True,
        )
        email_drafts = campaign.email_drafts
    except Exception as exc:
        print_error(f"Pipeline failed: {escape(str(exc))}")
        logger.exception("Preview pipeline error")
        sys.exit(1)

    if not email_drafts:
        print_warning("No email drafts were generated. Check your API keys and try again.")
        sys.exit(0)

    console.print()
    console.rule(
        f"[bold magenta]Email Previews — {len(email_drafts)} draft(s)[/bold magenta]",
        style="magenta",
    )
    console.print()

    for idx, draft in enumerate(email_drafts, start=1):
        to_email = draft.contact.email or "unknown@example.com"
        contact_name = draft.contact.full_name
        subject = draft.subject
        body = draft.body

        meta_table = Table.grid(padding=(0, 1))
        meta_table.add_column(style="bold dim")
        meta_table.add_column(style="white")
        meta_table.add_row("To:", f"{contact_name} <{to_email}>")
        meta_table.add_row("Subject:", subject)
        meta_table.add_row("AI Provider:", draft.ai_provider_used)
        meta_table.add_row("Score:", f"{draft.personalization_score:.0f}/100")

        console.print(
            Panel(
                Columns([meta_table]),
                title=f"[bold magenta]Email #{idx}[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            )
        )
        console.print(
            Panel(
                body,
                title="[dim]Message Body[/dim]",
                border_style="dim blue",
                padding=(1, 2),
            )
        )
        console.print()

    print_success(
        f"[bold]{len(email_drafts)}[/bold] email draft(s) previewed. "
        f"Use [cyan]python main.py run --domain {domain}[/cyan] to send."
    )
    console.print()


# ---------------------------------------------------------------------------
# analytics command
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--campaign-id",
    default=None,
    help="Specific campaign ID (shows all campaigns if omitted)",
)
def analytics(campaign_id: Optional[str]) -> None:
    """Show campaign analytics and performance metrics."""
    print_info("Loading analytics …")
    console.print()

    try:
        engine = AnalyticsEngine()

        if campaign_id:
            metrics = engine.get_campaign_metrics(campaign_id)
            campaigns = [metrics] if metrics else []
        else:
            campaigns = engine.get_all_metrics()
    except Exception as exc:
        print_error(f"Analytics error: {exc}")
        sys.exit(1)

    if not campaigns:
        print_warning("No analytics data found. Run a campaign first.")
        sys.exit(0)

    overall = engine.get_aggregate_summary()
    summary_table = Table(
        title="[bold cyan]Overall Performance Summary[/bold cyan]",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        show_header=True,
        header_style="bold white",
    )
    summary_table.add_column("Metric", style="bold cyan", min_width=24)
    summary_table.add_column("Value", style="bold white", justify="right", min_width=12)
    summary_table.add_column("Benchmark", style="dim", justify="right", min_width=12)

    summary_table.add_row("Total Campaigns", str(overall.get("total_campaigns", 0)), "—")
    summary_table.add_row("Total Emails Sent", str(overall.get("total_emails_sent", 0)), "—")
    summary_table.add_row("Avg. Open Rate", f"{overall.get('avg_open_rate', 0.0):.1f}%", "20–30%")
    summary_table.add_row("Avg. Click Rate", f"{overall.get('avg_click_rate', 0.0):.1f}%", "2–5%")
    summary_table.add_row("Avg. Reply Rate", f"{overall.get('avg_reply_rate', 0.0):.1f}%", "1–3%")
    summary_table.add_row("Avg. Bounce Rate", f"{overall.get('avg_bounce_rate', 0.0):.1f}%", "< 2%")

    console.print(Align.center(summary_table))
    console.print()

    console.rule("[bold]Campaign Breakdown[/bold]", style="cyan")
    console.print()

    detail_table = Table(
        box=box.ROUNDED,
        border_style="blue",
        show_header=True,
        header_style="bold blue",
        expand=True,
    )
    detail_table.add_column("#", style="dim", justify="right", width=4)
    detail_table.add_column("Campaign ID", style="bold white", min_width=18)
    detail_table.add_column("Domain", style="cyan")
    detail_table.add_column("Sent", justify="right", style="white")
    detail_table.add_column("Opens", justify="right", style="green")
    detail_table.add_column("Clicks", justify="right", style="blue")
    detail_table.add_column("Replies", justify="right", style="magenta")
    detail_table.add_column("Date", style="dim")

    for idx, c in enumerate(campaigns, start=1):
        detail_table.add_row(
            str(idx),
            c.get("campaign_id", "—"),
            c.get("domain", "—"),
            str(c.get("emails_sent", 0)),
            f"{c.get('open_rate', 0):.1f}%",
            f"{c.get('click_rate', 0):.1f}%",
            f"{c.get('reply_rate', 0):.1f}%",
            c.get("created_at", "—"),
        )

    console.print(detail_table)
    console.print()
    print_success(f"Analytics loaded for [bold]{len(campaigns)}[/bold] campaign(s).")
    console.print()


# ---------------------------------------------------------------------------
# history command
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--limit",
    default=20,
    show_default=True,
    help="Number of records to show",
)
def history(limit: int) -> None:
    """Show campaign and prospect history."""
    print_info(f"Loading last [bold]{limit}[/bold] records from CRM …")
    console.print()

    crm = CRMManager()

    campaigns = crm.get_campaign_history()[-limit:]

    camp_table = Table(
        title="[bold cyan]Campaign History[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    camp_table.add_column("#", style="dim", justify="right", width=4)
    camp_table.add_column("Campaign Name", style="bold white", min_width=22)
    camp_table.add_column("Domain", style="cyan")
    camp_table.add_column("Sent", justify="right", style="green")
    camp_table.add_column("Status", justify="center")
    camp_table.add_column("Created At", style="dim")

    for idx, camp in enumerate(campaigns, start=1):
        status_val = camp.get("status", "unknown")
        status_style = {
            "completed": "bold green",
            "sent": "bold green",
            "failed": "bold red",
            "cancelled": "bold yellow",
            "draft": "dim",
        }.get(status_val, "dim")
        camp_table.add_row(
            str(idx),
            camp.get("name", "—"),
            camp.get("target_domain", "—"),
            str(camp.get("emails_sent", 0)),
            Text(status_val.upper(), style=status_style),
            camp.get("created_at", "—"),
        )

    if campaigns:
        console.print(camp_table)
    else:
        print_warning("No campaign history found.")

    console.print()

    prospects = crm.get_prospect_history()[-limit:]

    pros_table = Table(
        title="[bold magenta]Prospect History[/bold magenta]",
        box=box.ROUNDED,
        border_style="magenta",
        show_header=True,
        header_style="bold magenta",
        expand=True,
    )
    pros_table.add_column("#", style="dim", justify="right", width=4)
    pros_table.add_column("Name", style="bold white", min_width=20)
    pros_table.add_column("Title", style="cyan")
    pros_table.add_column("Company", style="white")
    pros_table.add_column("Email", style="blue")
    pros_table.add_column("Status", style="dim")
    pros_table.add_column("Sent At", style="dim")

    for idx, p in enumerate(prospects, start=1):
        pros_table.add_row(
            str(idx),
            p.get("contact_name", "—"),
            p.get("contact_title", "—"),
            p.get("company_name", "—"),
            p.get("contact_email", "—"),
            p.get("status", "—"),
            p.get("sent_at", "—"),
        )

    if prospects:
        console.print(pros_table)
    else:
        print_warning("No prospect history found.")

    console.print()
    print_success("History loaded successfully.")
    console.print()


# ---------------------------------------------------------------------------
# status command
# ---------------------------------------------------------------------------

@cli.command()
def status() -> None:
    """Show API provider status and configuration health."""
    print_info("Checking API provider status ...")
    console.print()

    router = AIRouter()
    provider_status = router.get_status()

    ai_table = Table(
        title="[bold cyan]AI Providers[/bold cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
    )
    ai_table.add_column("Provider", style="bold white", min_width=16)
    ai_table.add_column("Status", justify="center", min_width=10)
    ai_table.add_column("Key Set?", justify="center", min_width=10)
    ai_table.add_column("Priority", justify="center", min_width=10)

    provider_info = [
        ("Gemini", "gemini", "1st"),
        ("Groq", "groq", "2nd"),
        ("OpenRouter", "openrouter", "3rd"),
        ("Template", "template", "Fallback"),
    ]
    for display_name, key, priority in provider_info:
        is_set = provider_status.get(key, False) if key != "template" else True
        status_text = Text("READY", style="bold green") if is_set else Text("NO KEY", style="bold red")
        key_text = Text("Yes", style="bold green") if is_set else Text("No", style="dim")
        ai_table.add_row(display_name, status_text, key_text, priority)

    console.print(Align.center(ai_table))
    console.print()

    ext_checks = [
        ("Apollo.io", "APOLLO_API_KEY", "Lead Discovery"),
        ("Prospeo", "PROSPEO_API_KEY", "Contact Enrichment"),
        ("Hunter.io", "HUNTER_API_KEY", "Email Enrichment"),
        ("Brevo", "BREVO_API_KEY", "Email Delivery"),
    ]

    ext_table = Table(
        title="[bold magenta]External Services[/bold magenta]",
        box=box.ROUNDED,
        border_style="magenta",
        show_header=True,
        header_style="bold magenta",
    )
    ext_table.add_column("Service", style="bold white", min_width=16)
    ext_table.add_column("Purpose", style="cyan", min_width=22)
    ext_table.add_column("API Key", justify="center", min_width=12)

    for svc_name, env_var, purpose in ext_checks:
        key_value = getattr(settings, env_var, "") or ""
        is_set = bool(key_value and len(key_value) > 10)
        key_text = Text("Configured", style="bold green") if is_set else Text("Missing", style="bold red")
        ext_table.add_row(svc_name, purpose, key_text)

    console.print(Align.center(ext_table))
    console.print()

    cfg_table = Table(
        title="[bold blue]Pipeline Configuration[/bold blue]",
        box=box.ROUNDED,
        border_style="blue",
        show_header=False,
        padding=(0, 2),
    )
    cfg_table.add_column("Setting", style="bold cyan", min_width=24)
    cfg_table.add_column("Value", style="white", min_width=16)
    cfg_table.add_row("Max Companies", str(settings.MAX_COMPANIES))
    cfg_table.add_row("Max Contacts / Company", str(settings.MAX_CONTACTS_PER_COMPANY))
    cfg_table.add_row("Max Retries", str(settings.MAX_RETRIES))
    cfg_table.add_row("Request Timeout (s)", str(settings.REQUEST_TIMEOUT))
    cfg_table.add_row("Sender Email", settings.SENDER_EMAIL or "Not configured")
    cfg_table.add_row("Sender Name", settings.SENDER_NAME or "Not configured")
    cfg_table.add_row("Dry Run Mode", "ON" if settings.DRY_RUN else "OFF")

    console.print(Align.center(cfg_table))
    console.print()

    print_success("Template AI always available. System is ready to run campaigns.")
    console.print()


# ---------------------------------------------------------------------------
# health command  (detailed integration health + credits)
# ---------------------------------------------------------------------------

@cli.command()
def health() -> None:
    """Show detailed integration health, API credits, and live connectivity."""
    print_info("Running integration health checks …")
    console.print()

    results = []

    # ── Hunter ──────────────────────────────────────────────────────────
    hunter = HunterService()
    hunter_status = {"name": "Hunter.io", "purpose": "Email Discovery", "configured": hunter.is_configured()}
    if hunter.is_configured():
        try:
            data = hunter._make_request("/account", params={})
            plan = data.get("data", {}).get("plan_name", "free") if data else "unknown"
            searches = data.get("data", {}).get("requests", {}).get("searches", {}) if data else {}
            used = searches.get("used", 0)
            available = searches.get("available", 0)
            hunter_status["credits_used"] = used
            hunter_status["credits_remaining"] = available
            hunter_status["plan"] = plan
            hunter_status["status"] = "READY"
        except Exception as e:
            hunter_status["status"] = f"LIVE (key set)"
            hunter_status["credits_remaining"] = "Unknown"
    else:
        hunter_status["status"] = "NO KEY"
    results.append(hunter_status)

    # ── Prospeo ──────────────────────────────────────────────────────────
    prospeo = ProspeoService()
    prospeo_status = {"name": "Prospeo", "purpose": "Contact Enrichment", "configured": prospeo.is_configured()}
    if prospeo.is_configured():
        try:
            data = prospeo.get_account_info()
            resp = data.get("response", {})
            prospeo_status["credits_remaining"] = resp.get("remaining_credits", "Unknown")
            prospeo_status["plan"] = resp.get("current_plan", "FREE")
            prospeo_status["credits_used"] = resp.get("used_credits", 0)
            prospeo_status["renewal"] = resp.get("next_quota_renewal_date", "")[:10]
            prospeo_status["status"] = "READY"
        except Exception as e:
            prospeo_status["status"] = "LIVE (key set)"
            prospeo_status["credits_remaining"] = "Unknown"
    else:
        prospeo_status["status"] = "NO KEY"
    results.append(prospeo_status)

    # ── Apollo ──────────────────────────────────────────────────────────
    apollo = ApolloService()
    apollo_status = {"name": "Apollo.io", "purpose": "Lead Discovery", "configured": apollo.is_configured()}
    apollo_status["status"] = "READY" if apollo.is_configured() else "NO KEY"
    apollo_status["credits_remaining"] = "N/A (master key)"
    results.append(apollo_status)

    # ── Brevo ──────────────────────────────────────────────────────────
    brevo = BrevoService()
    brevo_status = {"name": "Brevo", "purpose": "Email Delivery", "configured": brevo.is_configured()}
    brevo_status["status"] = "READY" if brevo.is_configured() else "NO KEY"
    brevo_status["credits_remaining"] = "300/day (free plan)"
    results.append(brevo_status)

    # ── AI Providers ────────────────────────────────────────────────────
    router = AIRouter()
    for provider_name, key_val in [
        ("Groq", settings.GROQ_API_KEY if hasattr(settings, 'GROQ_API_KEY') else ""),
        ("OpenRouter", settings.OPENROUTER_API_KEY if hasattr(settings, 'OPENROUTER_API_KEY') else ""),
    ]:
        configured = bool(key_val and len(key_val) > 10)
        results.append({
            "name": provider_name,
            "purpose": "AI Email Generation",
            "configured": configured,
            "status": "READY" if configured else "NO KEY",
            "credits_remaining": "Free tier",
        })

    # ── Render table ─────────────────────────────────────────────────────
    health_table = Table(
        title="[bold cyan]Integration Health Report[/bold cyan]",
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    health_table.add_column("Service", style="bold white", min_width=14)
    health_table.add_column("Purpose", style="cyan", min_width=22)
    health_table.add_column("Status", justify="center", min_width=10)
    health_table.add_column("Credits/Limit", justify="right", min_width=16)
    health_table.add_column("Plan", style="dim", min_width=12)

    for r in results:
        st = r.get("status", "?")
        if st == "READY":
            st_text = Text("● READY", style="bold green")
        elif "LIVE" in st:
            st_text = Text("● LIVE", style="bold green")
        elif st == "NO KEY":
            st_text = Text("✗ NO KEY", style="bold red")
        else:
            st_text = Text(f"⚠ {st}", style="bold yellow")

        credits = str(r.get("credits_remaining", "N/A"))
        plan = str(r.get("plan", "—"))
        health_table.add_row(
            r["name"], r["purpose"], st_text, credits, plan
        )

    console.print(Align.center(health_table))
    console.print()

    ready = sum(1 for r in results if "READY" in r.get("status", "") or "LIVE" in r.get("status", ""))
    total = len(results)
    if ready == total:
        print_success(f"All {total} integrations operational.")
    elif ready >= total // 2:
        print_warning(f"{ready}/{total} integrations ready. Some keys missing.")
    else:
        print_error(f"Only {ready}/{total} integrations configured. Check your .env file.")

    console.print()
    console.print(Text(f"  Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim"))
    console.print()


# ---------------------------------------------------------------------------
# export command  (CSV export of all leads)
# ---------------------------------------------------------------------------

@cli.command()
@click.option(
    "--output", "-o",
    default="leads_export.csv",
    show_default=True,
    help="Output CSV file path",
)
@click.option(
    "--domain", "-d",
    default=None,
    help="Filter by target domain (optional)",
)
def export(output: str, domain: Optional[str]) -> None:
    """Export all leads and campaign data to CSV."""
    print_info(f"Exporting lead data to [bold cyan]{output}[/bold cyan] …")
    console.print()

    crm = CRMManager()
    prospects = crm.get_prospect_history()
    campaigns = {c.get("id"): c for c in crm.get_campaign_history()}

    if domain:
        prospects = [p for p in prospects if domain.lower() in p.get("company_domain", "").lower()]

    if not prospects:
        print_warning("No prospect records found. Run a campaign first.")
        return

    EXPORT_COLUMNS = [
        "company_name",
        "company_domain",
        "contact_name",
        "contact_title",
        "contact_email",
        "source",
        "campaign_id",
        "campaign_status",
        "sent_at",
        "status",
        "notes",
    ]

    out_path = Path(output)
    try:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            for p in prospects:
                # Merge campaign status into prospect record
                camp_id = p.get("campaign_id", "")
                campaign = campaigns.get(camp_id, {})
                row = {
                    "company_name": p.get("company_name", ""),
                    "company_domain": p.get("company_domain", ""),
                    "contact_name": p.get("contact_name", ""),
                    "contact_title": p.get("contact_title", ""),
                    "contact_email": p.get("contact_email", ""),
                    "source": p.get("source", "hunter"),
                    "campaign_id": camp_id,
                    "campaign_status": campaign.get("status", p.get("status", "")),
                    "sent_at": p.get("sent_at", ""),
                    "status": p.get("status", ""),
                    "notes": p.get("notes", ""),
                }
                writer.writerow(row)
        print_success(f"Exported [bold]{len(prospects)}[/bold] leads to [bold cyan]{out_path}[/bold cyan]")
    except Exception as e:
        print_error(f"Export failed: {e}")
        return

    # Show preview table
    preview = prospects[:5]
    preview_table = Table(
        title="[bold]Export Preview (first 5 records)[/bold]",
        box=box.ROUNDED,
        border_style="green",
        show_header=True,
        header_style="bold green",
    )
    preview_table.add_column("Name", style="bold white")
    preview_table.add_column("Company", style="cyan")
    preview_table.add_column("Email", style="blue")
    preview_table.add_column("Status", style="dim")
    for p in preview:
        preview_table.add_row(
            p.get("contact_name", "—"),
            p.get("company_name", "—"),
            p.get("contact_email", "—"),
            p.get("status", "—"),
        )
    console.print(Align.center(preview_table))
    console.print()



if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(f"\n[red]✗ Fatal error: {escape(str(exc))}[/red]")
        logger.exception("Unhandled fatal error in CLI")
        sys.exit(1)
