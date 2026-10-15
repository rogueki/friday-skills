# F.R.I.D.A.Y. plugin boundary

RogueKI supplies callable local functions in `shared/hooks.py` for input inspection and action preflight. No Hermes plugin is registered by this repository. A future trusted adapter must call the policy function synchronously **before** every external action and fail closed on timeout, exception, missing capability, or missing approval. A post-action audit hook alone cannot enforce approval.

The local lifecycle format is `shared/schemas/event.schema.json`. It is not a `rogue-friday` AsyncAPI event. `dashboard_mapping` returns an intended task/activity operation with `publishable: false`; no network publishing occurs here.

Mock adapter methods only read synthetic fixtures or record proposals in memory. They cannot send mail, book travel, pay invoices, change home devices, submit tax forms, or mutate archive files.
