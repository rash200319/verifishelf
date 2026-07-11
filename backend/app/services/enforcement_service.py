from app.repositories.enforcement_letter_repository import EnforcementLetterRepository
from app.services import llm_client
from app.services.pdf_render import render_enforcement_letter_pdf
from app.services.screenshot_service import capture_listing_screenshot


class EnforcementService:
    PROVIDER_TEMPLATE = "template"
    PROVIDER_CLAUDE = "claude"
    PROVIDER_GROQ = "groq"
    PROVIDER_GPT4O = "gpt4o"  # legacy alias, also routes to the LLM chain -- see generate_for_violation
    LLM_PROVIDERS = {PROVIDER_CLAUDE, PROVIDER_GROQ, PROVIDER_GPT4O}

    LETTER_SYSTEM_PROMPT = (
        "You are a brand protection compliance officer drafting a formal MAP "
        "(Minimum Advertised Price) violation notice to a third-party reseller. "
        "Write a professional, firm, but courteous business letter (Subject line "
        "plus body). Reference only the facts given in the violation context -- "
        "do not invent product details, legal claims, or numbers not provided. "
        "Ask for the price to be corrected within 48 hours and note that "
        "continued non-compliance may lead to further enforcement action. "
        "Output only the letter text, no preamble or commentary."
    )

    @staticmethod
    def _build_claude_letter_prompt(context: dict) -> str:
        return (
            f"Brand: {context['brand_name']}\n"
            f"Product: {context['product_name']}\n"
            f"Seller: {context['seller_name']}\n"
            f"Storefront/listing: {context['listing_title']} ({context['listing_url']})\n"
            f"MAP price: {context['map_price']} {context.get('currency_code') or 'USD'}\n"
            f"Advertised price: {context['advertised_price']} {context.get('currency_code') or 'USD'}\n"
            f"Price delta: {float(context['price_delta_pct'] or 0):.2f}% below MAP\n"
            f"Detected at: {context['detected_at']}\n"
            f"Violation status: {context['status']}\n"
        )

    @staticmethod
    def build_template_letter(context: dict) -> str:
        map_price = float(context["map_price"])
        advertised_price = float(context["advertised_price"])
        delta = float(context["price_delta_pct"] or 0)
        currency = context.get("currency_code") or "USD"

        return (
            f"Subject: MAP Violation Notice - {context['product_name']}\n\n"
            f"Dear {context['seller_name']},\n\n"
            f"Our MAP monitoring system detected that your listing \"{context['listing_title']}\" "
            f"({context['listing_url']}) is advertised at {advertised_price:.2f} {currency}, "
            f"which is below the Minimum Advertised Price (MAP) of {map_price:.2f} {currency} "
            f"for {context['brand_name']} products.\n\n"
            f"Violation details:\n"
            f"- Detected at: {context['detected_at']}\n"
            f"- Price delta: {delta:.2f}%\n"
            f"- Current status: {context['status']}\n\n"
            f"Please update the advertised price to at least the MAP threshold within 48 hours. "
            f"Continued non-compliance may result in further enforcement action.\n\n"
            f"Regards,\n"
            f"{context['brand_name']} Brand Protection Team"
        )

    @classmethod
    async def generate_for_violation(
        cls,
        violation_id: int,
        brand_id: int,
        provider: str = PROVIDER_TEMPLATE,
        force_regenerate: bool = False,
    ) -> dict:
        if not force_regenerate:
            existing = await EnforcementLetterRepository.get_latest_for_violation(violation_id)
            if existing is not None:
                return existing

        context = await EnforcementLetterRepository.get_violation_context(violation_id, brand_id)
        if context is None:
            raise ValueError(f"Violation {violation_id} not found for brand {brand_id}")

        letter_content = None
        generated_by = cls.PROVIDER_TEMPLATE

        if provider in cls.LLM_PROVIDERS:
            result = llm_client.generate_text(
                cls.LETTER_SYSTEM_PROMPT,
                cls._build_claude_letter_prompt(context),
                max_tokens=600,
            )
            if result is not None:
                letter_content, generated_by = result

        if letter_content is None:
            letter_content = cls.build_template_letter(context)
            generated_by = cls.PROVIDER_TEMPLATE

        screenshot_base64 = await capture_listing_screenshot(
            listing_url=context.get("listing_url"),
            country_code=context.get("country_code"),
            brand_sub_id=context.get("torch_sub_id"),
        )

        return await EnforcementLetterRepository.create_letter(
            violation_id=violation_id,
            letter_content=letter_content,
            generated_by=generated_by,
            screenshot_base64=screenshot_base64,
        )

    @classmethod
    async def get_for_violation(cls, violation_id: int, brand_id: int) -> dict | None:
        context = await EnforcementLetterRepository.get_violation_context(violation_id, brand_id)
        if context is None:
            return None
        return await EnforcementLetterRepository.get_latest_for_violation(violation_id)

    @classmethod
    async def mark_sent(cls, violation_id: int, brand_id: int) -> dict:
        """
        Record that a brand admin has actually transmitted the drafted
        letter (there's no real seller contact address to email
        automatically, so this is the brand's own record of having actioned
        it elsewhere). Raises ValueError if the violation doesn't belong to
        this brand or no letter has been generated yet.
        """
        context = await EnforcementLetterRepository.get_violation_context(violation_id, brand_id)
        if context is None:
            raise ValueError(f"Violation {violation_id} not found for brand {brand_id}")

        letter = await EnforcementLetterRepository.get_latest_for_violation(violation_id)
        if letter is None:
            raise ValueError(f"No enforcement letter has been generated yet for violation {violation_id}")

        return await EnforcementLetterRepository.mark_sent(letter["id"])

    @classmethod
    async def get_pdf_for_violation(cls, violation_id: int, brand_id: int) -> bytes:
        context = await EnforcementLetterRepository.get_violation_context(violation_id, brand_id)
        if context is None:
            raise ValueError(f"Violation {violation_id} not found for brand {brand_id}")

        letter = await EnforcementLetterRepository.get_latest_for_violation(violation_id)
        if letter is None:
            raise ValueError(f"No enforcement letter has been generated yet for violation {violation_id}")

        return render_enforcement_letter_pdf(context, letter)
