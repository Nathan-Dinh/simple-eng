# Legal and compliance standards (owner: Legal and compliance)

Tags: `[all]` applies at every stage and is never skipped; `[pre-production]` and `[production]` apply from that stage on. See `${CLAUDE_PLUGIN_ROOT}/reference/policies/specialist-review.md`.

These checks flag risks and explain requirements. They are not legal advice. Anything binding, such as contracts, published terms, privacy notices, or regulatory filings, goes to a human lawyer.

## Dependencies and third parties

- [all] Every new dependency's license is identified, and it is compatible with how the project is distributed. Copyleft licenses (GPL, AGPL, LGPL) and unlicensed code are flagged before adoption.
- [all] Every third-party service has its terms checked for data use, data location, and limits, with the source link and the date checked.
- [pre-production] The personal data sent to each third-party service is listed, with the agreement that covers it (for example a data processing agreement).

## Personal data

- [all] Every category of personal data the project collects, stores, or shares is listed in the Backend Schema with its purpose.
- [pre-production] The laws that apply are named, based on where users are and what data is collected (for example GDPR for people in the EU, CCPA for California residents).
- [pre-production] Each category of personal data has a retention period and a deletion path.
- [pre-production] Where GDPR or CCPA applies, users can access, export, and delete their data, and the project records the lawful basis for each processing purpose.
- [production] A privacy notice that matches what the project actually does is published, reviewed by a lawyer.

## Accessibility law

- [pre-production] The accessibility laws that apply (for example the ADA, the European Accessibility Act) and the conformance level they imply (for example WCAG 2.2 AA) are named in the UI/UX Design Brief. ui-ux-design implements them.
