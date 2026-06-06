"""
Brevo (formerly Sendinblue) email service integration.

Provides transactional email sending, campaign management,
and contact management via the sib_api_v3_sdk library.
"""

import textwrap
from datetime import datetime
from typing import Dict, List, Optional

import sib_api_v3_sdk
from loguru import logger
from sib_api_v3_sdk.rest import ApiException

from src.config.settings import settings
from src.models.campaign import Campaign, CampaignResult, EmailDraft


class BrevoService:
    """
    Service class for all Brevo (Sendinblue) API interactions.

    Handles transactional emails, campaign sends, contact upserts,
    and delivery-stat lookups. Configuration is pulled from the
    application settings object at construction time.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.BREVO_API_KEY

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = self.api_key

        self.client = sib_api_v3_sdk.ApiClient(configuration)
        self.transactional_api = sib_api_v3_sdk.TransactionalEmailsApi(self.client)
        self.campaigns_api = sib_api_v3_sdk.EmailCampaignsApi(self.client)
        self.contacts_api = sib_api_v3_sdk.ContactsApi(self.client)

        logger.info(
            "BrevoService initialised (configured={configured})",
            configured=self.is_configured(),
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """Return True when a non-trivial API key is present."""
        return bool(self.api_key and len(self.api_key) > 10)

    # ------------------------------------------------------------------
    # Transactional email
    # ------------------------------------------------------------------

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        reply_to: Optional[str] = None,
    ) -> Dict:
        """
        Send a single transactional email via Brevo.

        Parameters
        ----------
        to_email:
            Recipient email address.
        to_name:
            Recipient display name.
        subject:
            Email subject line.
        html_body:
            HTML content. Plain-text bodies are automatically wrapped
            in a styled HTML template via :meth:`_format_email_body`.
        reply_to:
            Optional reply-to address. Falls back to sender address.

        Returns
        -------
        dict
            ``{success: bool, message_id: str | None, error: str | None}``
        """
        if not self.is_configured():
            logger.warning("Brevo API key not configured – email not sent")
            return {"success": False, "message_id": None, "error": "API key not configured"}

        # Auto-wrap plain text bodies
        if html_body and not html_body.strip().startswith("<"):
            html_body = self._format_email_body(html_body)

        sender = {
            "name": getattr(settings, "SENDER_NAME", "Vaibhav Growth Engine"),
            "email": getattr(settings, "SENDER_EMAIL", "noreply@example.com"),
        }

        to_list = [{"email": to_email, "name": to_name}]

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to_list,
            sender=sender,
            reply_to={"email": reply_to or sender["email"]},
            subject=subject,
            html_content=html_body,
        )

        try:
            response = self.transactional_api.send_transac_email(send_smtp_email)
            message_id = getattr(response, "message_id", None)
            logger.info(
                "Email sent to {email} | message_id={mid}",
                email=to_email,
                mid=message_id,
            )
            return {"success": True, "message_id": message_id, "error": None}
        except ApiException as exc:
            logger.error(
                "Brevo API error sending to {email}: {status} – {body}",
                email=to_email,
                status=exc.status,
                body=exc.body,
            )
            return {"success": False, "message_id": None, "error": str(exc.body)}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error sending email to {email}", email=to_email)
            return {"success": False, "message_id": None, "error": str(exc)}

    # ------------------------------------------------------------------
    # Campaign sending
    # ------------------------------------------------------------------

    def send_campaign_emails(
        self,
        drafts: List[EmailDraft],
        campaign: Campaign,
        dry_run: bool = False,
    ) -> CampaignResult:
        """
        Send personalised outreach emails for an entire campaign.

        Parameters
        ----------
        drafts:
            List of :class:`~src.models.campaign.EmailDraft` objects,
            each containing a recipient, subject, and rendered body.
        campaign:
            The parent :class:`~src.models.campaign.Campaign` instance.
            ``campaign.emails_sent`` is updated in-place.
        dry_run:
            When *True* no emails are dispatched; all drafts are logged
            and a mock :class:`~src.models.campaign.CampaignResult` is
            returned.

        Returns
        -------
        CampaignResult
            Aggregated outcome for the batch.
        """
        sent: List[Dict] = []
        failed: List[Dict] = []
        start_time = datetime.utcnow()

        # Free-tier safety: never send more than 300 emails/day
        BREVO_FREE_DAILY_LIMIT = 300
        if len(drafts) > BREVO_FREE_DAILY_LIMIT:
            logger.warning(
                "Draft count ({n}) exceeds Brevo free-tier daily limit (300). "
                "Capping to {limit} emails.",
                n=len(drafts),
                limit=BREVO_FREE_DAILY_LIMIT,
            )
            drafts = drafts[:BREVO_FREE_DAILY_LIMIT]

        # Skip drafts with no email address
        valid_drafts = [d for d in drafts if d.contact.email and "@" in d.contact.email]
        skipped_no_email = len(drafts) - len(valid_drafts)
        if skipped_no_email:
            logger.warning(
                "Skipping {n} draft(s) with no email address.", n=skipped_no_email
            )
        drafts = valid_drafts

        if dry_run:
            logger.info(
                "[DRY-RUN] Campaign '{name}' — would send {n} emails",
                name=campaign.name,
                n=len(drafts),
            )
            for draft in drafts:
                to_email = draft.contact.email or ""
                logger.debug("[DRY-RUN] To: {email} | Subject: {subject}", email=to_email, subject=draft.subject)
                sent.append({"email": to_email, "message_id": f"dry-run-{to_email}", "success": True})

            return CampaignResult(
                campaign=campaign,
                success=True,
                message=f"[DRY-RUN] Would have sent {len(drafts)} emails",
                brevo_message_ids=[s["message_id"] for s in sent],
                errors=[],
            )

        logger.info("Starting campaign '{name}' – {n} recipients", name=campaign.name, n=len(drafts))
        errors = []
        for draft in drafts:
            to_email = draft.contact.email or ""
            to_name = draft.contact.full_name
            html_body = self._format_email_body(draft.body)
            result = self.send_email(to_email=to_email, to_name=to_name, subject=draft.subject, html_body=html_body)
            if result["success"]:
                campaign.emails_sent += 1
                sent.append({"email": to_email, "message_id": result["message_id"], "success": True})
            else:
                errors.append(f"{to_email}: {result['error']}")
                failed.append({"email": to_email, "error": result["error"], "success": False})

        logger.info("Campaign '{name}' complete – sent={sent}, failed={failed}", name=campaign.name, sent=len(sent), failed=len(failed))

        return CampaignResult(
            campaign=campaign,
            success=len(sent) > 0,
            message=f"Sent {len(sent)}/{len(drafts)} emails",
            brevo_message_ids=[s["message_id"] for s in sent if s.get("message_id")],
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def create_contact(
        self,
        email: str,
        first_name: str,
        last_name: str,
        attributes: Optional[Dict] = None,
    ) -> bool:
        """
        Create or update a contact in Brevo.

        Parameters
        ----------
        email:
            Contact email (used as the unique identifier).
        first_name:
            Contact first name.
        last_name:
            Contact last name.
        attributes:
            Optional extra attributes dict accepted by Brevo
            (e.g. ``{"COMPANY": "Acme", "PHONE": "+1…"}``).

        Returns
        -------
        bool
            *True* on success, *False* on any error.
        """
        if not self.is_configured():
            logger.warning("Brevo API key not configured – contact not created")
            return False

        contact_attributes: Dict = {"FIRSTNAME": first_name, "LASTNAME": last_name}
        if attributes:
            contact_attributes.update(attributes)

        create_contact_payload = sib_api_v3_sdk.CreateContact(
            email=email,
            attributes=contact_attributes,
            update_enabled=True,
        )

        try:
            self.contacts_api.create_contact(create_contact_payload)
            logger.info("Contact created/updated: {email}", email=email)
            return True
        except ApiException as exc:
            logger.error(
                "Brevo API error creating contact {email}: {status} – {body}",
                email=email,
                status=exc.status,
                body=exc.body,
            )
            return False
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error creating contact {email}", email=email)
            return False

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_email_stats(self, message_id: str) -> Dict:
        """
        Retrieve delivery statistics for a previously sent transactional email.

        Brevo exposes stats via ``get_transac_email_content``; the raw
        event list is parsed into a normalised dict.

        Parameters
        ----------
        message_id:
            The ``message_id`` returned by :meth:`send_email`.

        Returns
        -------
        dict
            ``{message_id, delivered, opened, clicked, bounced, events: [...]}``
        """
        if not self.is_configured():
            logger.warning("Brevo API key not configured – cannot fetch stats")
            return {
                "message_id": message_id,
                "delivered": False,
                "opened": False,
                "clicked": False,
                "bounced": False,
                "events": [],
                "error": "API key not configured",
            }

        try:
            response = self.transactional_api.get_transac_email_content(message_id)
            events = getattr(response, "events", []) or []
            event_names = [
                getattr(ev, "name", "").lower() for ev in events if hasattr(ev, "name")
            ]
            stats = {
                "message_id": message_id,
                "delivered": any(e in ("delivered",) for e in event_names),
                "opened": any(e in ("opened", "unique_opened") for e in event_names),
                "clicked": any(e in ("clicks", "clicked") for e in event_names),
                "bounced": any(e in ("hardBounce", "softBounce", "bounce") for e in event_names),
                "events": event_names,
                "error": None,
            }
            logger.debug("Stats for {mid}: {stats}", mid=message_id, stats=stats)
            return stats
        except ApiException as exc:
            logger.error(
                "Brevo API error fetching stats for {mid}: {status} – {body}",
                mid=message_id,
                status=exc.status,
                body=exc.body,
            )
            return {
                "message_id": message_id,
                "delivered": False,
                "opened": False,
                "clicked": False,
                "bounced": False,
                "events": [],
                "error": str(exc.body),
            }
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error fetching stats for {mid}", mid=message_id)
            return {
                "message_id": message_id,
                "delivered": False,
                "opened": False,
                "clicked": False,
                "bounced": False,
                "events": [],
                "error": "Unexpected error",
            }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _format_email_body(self, body: str) -> str:
        """
        Wrap a plain-text body in an email-safe, inline-CSS HTML template.

        Paragraphs are split on double newlines; single newlines within a
        paragraph become ``<br>`` tags. The result is suitable for direct
        injection into Brevo's ``html_content`` field.

        Parameters
        ----------
        body:
            Raw plain-text email body.

        Returns
        -------
        str
            Fully formed HTML document.
        """
        paragraphs = body.strip().split("\n\n")
        html_paragraphs: List[str] = []
        for para in paragraphs:
            lines = para.strip().replace("\n", "<br>\n")
            html_paragraphs.append(f"<p style='margin:0 0 16px 0;'>{lines}</p>")

        body_html = "\n".join(html_paragraphs)

        return textwrap.dedent(
            f"""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Email</title>
            </head>
            <body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                     style="background-color:#f5f5f5;">
                <tr>
                  <td align="center" style="padding:40px 16px;">
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0"
                           style="background-color:#ffffff;border-radius:8px;
                                  box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                      <tr>
                        <td style="padding:40px 48px;color:#1a1a1a;font-size:15px;
                                   line-height:1.7;">
                          {body_html}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:24px 48px;border-top:1px solid #eeeeee;
                                   font-size:12px;color:#999999;text-align:center;">
                          You are receiving this email because you were identified as a
                          relevant contact. To unsubscribe, reply with "Unsubscribe".
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """
        )
