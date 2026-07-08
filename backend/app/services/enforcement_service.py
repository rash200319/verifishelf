from app.repositories.enforcement_letter_repository import EnforcementLetterRepository


class EnforcementService:
    PROVIDER_TEMPLATE = "template"
    PROVIDER_GPT4O = "gpt4o"

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

        if provider == cls.PROVIDER_GPT4O:
            # Keep the interface ready for a future GPT-4o integration.
            letter_content = cls.build_template_letter(context)
            generated_by = cls.PROVIDER_GPT4O
        else:
            letter_content = cls.build_template_letter(context)
            generated_by = cls.PROVIDER_TEMPLATE

        return await EnforcementLetterRepository.create_letter(
            violation_id=violation_id,
            letter_content=letter_content,
            generated_by=generated_by,
        )

    @classmethod
    async def get_for_violation(cls, violation_id: int, brand_id: int) -> dict | None:
        context = await EnforcementLetterRepository.get_violation_context(violation_id, brand_id)
        if context is None:
            return None
        return await EnforcementLetterRepository.get_latest_for_violation(violation_id)
