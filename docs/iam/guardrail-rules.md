# IAM guardrail rules

`IamGuardrailAspect` adds a synthesis error when it finds:

1. An Allow statement with action `*` or `<service>:*`.
2. An Allow statement on Resource `*` for any action except those in `utilities/iam_actions.py` (X-Ray only).
3. A role whose trust policy allows principal `*`.

Fix the policy; do not disable the flag. If AWS truly needs a new wildcard-resource action, add it to
`ALLOWED_WILDCARD_RESOURCE_ACTIONS` in a reviewed pull request.
