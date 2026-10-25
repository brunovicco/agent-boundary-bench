# ADR 0001: Keep deterministic rules outside protocol adapters

Status: accepted. Date: 2026-10-25.

Context: independent business implementations would confound a boundary comparison.

Decision: use frozen standard-library domain contracts, one kernel, application Delegate/Probe ports, and Pydantic/SDK translation at adapters. Validate every completed business result against the same oracle, including hashes and evidence.

Consequences: transport objects never enter the kernel. Some conversion work is intrinsic to remote scenarios and is measured. The supervisor's validation hash work occurs in every scenario. This is pragmatic dependency separation, not one abstraction per function.
