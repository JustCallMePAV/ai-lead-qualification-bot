from datetime import datetime, timezone

from app.schemas.lead import LeadCreate, Priority, QualificationResult


class DemoQualificationClient:
    """Deterministic, offline qualifier for demonstrations and tests."""

    def qualify(self, lead: LeadCreate) -> QualificationResult:
        text = " ".join(filter(None, [lead.message, lead.job_title, lead.budget, lead.timeline])).lower()
        authority = any(x in text for x in ("director", "head of", "founder", "owner"))
        urgent = any(x in text for x in ("30 days", "immediately", "this month", "urgent"))
        budget = bool(lead.budget and any(char.isdigit() for char in lead.budget))
        relevant = any(x in text for x in ("ai", "automat", "lead", "crm", "assistant"))
        clear = len(lead.message) >= 80
        score = min(20 + 15 * authority + 15 * urgent + 15 * budget + 10 * clear + 15 * relevant, 100)
        priority = Priority.high if score >= 75 else Priority.medium if score >= 45 else Priority.low
        missing = []
        if not authority:
            missing.append("Who will approve this project and participate in the buying decision?")
        if not budget:
            missing.append("What budget range has been allocated?")
        if not urgent:
            missing.append("When do you need the solution operating?")
        action = ("Schedule a discovery call within one business day." if priority == Priority.high else
                  "Send a short discovery questionnaire and offer a call." if priority == Priority.medium else
                  "Add to nurture and request the missing qualification details.")
        company = lead.company or "your organization"
        return QualificationResult(
            category="AI automation opportunity" if relevant else "General inquiry",
            score=score,
            priority=priority,
            intent="Evaluate an automation solution" if relevant else "Explore available services",
            estimated_fit=(
                "Strong"
                if priority == Priority.high
                else "Potential"
                if priority == Priority.medium
                else "Unclear"
            ),
            summary=f"{lead.name} from {company} submitted a {priority.value}-priority inquiry.",
            reasoning=("Demo-generated from explicit need, role, timing, budget, clarity, "
                       "and service relevance signals only."),
            recommended_action=action,
            suggested_owner=("Senior solutions consultant" if priority == Priority.high
                             else "Sales development representative"),
            follow_up_questions=missing,
            draft_response=(f"Hi {lead.name}, thank you for sharing your goals. I would be happy to clarify "
                            "the scope and next steps with you."),
            tags=["demo-generated", priority.value, "ai-automation" if relevant else "general"],
            model_used="demo-rules-v1", qualified_at=datetime.now(timezone.utc),
        )
