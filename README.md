Proposed Idea: UK Household Support Navigator ("Benefit & Bill Guardian")
One-line purpose
Help low-income UK households discover and safely claim unclaimed benefits, grants, and bill-reduction schemes they are entitled to — without giving financial advice or submitting anything on their behalf.

Why this fits your pattern (and research.md)
Directly extends Section 1.1: Cost of Living is the #1 concern (88%) — nothing in your portfolio touches this.
Mirrors the AI trust gap in Section 1.2: people don't trust AI with money/government decisions (4–5% trust) — so this MVP must be advisory-only, radically transparent, human-approved — same governance model as Appointment Guardian and Career Navigator.
Known real-world problem: DWP/Policy in Practice estimate £23bn+ in unclaimed benefits annually in the UK (Pension Credit, Council Tax Reduction, Housing Benefit, Healthy Start, Warm Home Discount). This is a legitimate, high-impact social cause.
Agentic loop (same shape as your other MVPs)
Phase	What the agent does
Plan	Given household profile (income, benefits received, household size, region), determine which entitlement checks to run
Execute	Query eligibility rules (via GOV.UK benefit calculators / Turn2us API / entitledto-style logic)
Adapt	If data is incomplete or conflicting (e.g., self-employed income), ask targeted clarifying questions instead of guessing
Follow-up	Produce a prioritized "claim checklist" with deadlines, required documents, and the exact official application link