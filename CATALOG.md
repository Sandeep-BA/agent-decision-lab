# 100 agent recipes

Author: **Sandeep Belgavi**

Runnable definitions using the shared Java runtime. These are review and recommendation agents, not 100 deployed business integrations. Offline fixtures test code boundaries, not model quality.

| Recipe | Category | Evidence fields |
| --- | --- | --- |
| `ticket-triage` | Support | ticket, queue_policy |
| `refund-evidence-reviewer` | Support | order_evidence, refund_policy |
| `incident-update-reviewer` | Support | draft_update, incident_record |
| `escalation-router` | Support | case_summary, escalation_policy |
| `duplicate-ticket-checker` | Support | ticket_pair, duplicate_rules |
| `knowledge-answer-reviewer` | Support | draft_answer, help_article |
| `handoff-completeness-checker` | Support | handoff, handoff_checklist |
| `sla-evidence-assessor` | Support | milestone_summary, sla_review_criteria |
| `customer-sentiment-router` | Support | conversation, service_rubric |
| `resolution-verifier` | Support | verification_record, resolution_criteria |
| `prompt-injection-reviewer` | Security | retrieved_text, authorized_task |
| `tool-permission-reviewer` | Security | proposed_operation, permission_summary |
| `secret-exposure-reviewer` | Security | redacted_sample, handling_policy |
| `phishing-evidence-triage` | Security | message_summary, indicator_rubric |
| `access-review-assistant` | Security | role_request, review_policy |
| `audit-gap-finder` | Security | audit_summary, control_checklist |
| `dependency-alert-router` | Security | advisory_summary, component_context |
| `data-egress-reviewer` | Security | transfer_summary, classification_rules |
| `abuse-report-triage` | Security | abuse_report, moderation_policy |
| `fraud-case-prioritizer` | Security | indicator_summary, review_rubric |
| `cloud-run-rollout-reviewer` | Cloud | release_evidence, rollout_checklist |
| `kubernetes-change-reviewer` | Cloud | change_summary, operational_constraints |
| `terraform-plan-reviewer` | Cloud | plan_summary, infrastructure_policy |
| `cost-anomaly-explainer` | Cloud | cost_facts, usage_changes |
| `capacity-review-assistant` | Cloud | capacity_proposal, workload_assumptions |
| `failover-readiness-checker` | Cloud | readiness_evidence, failover_prerequisites |
| `backup-evidence-reviewer` | Cloud | backup_report, recovery_criteria |
| `network-rule-reviewer` | Cloud | rule_summary, traffic_scope |
| `service-ownership-router` | Cloud | incident_summary, ownership_map |
| `deployment-rollback-advisor` | Cloud | rollout_symptoms, rollback_criteria |
| `schema-migration-reviewer` | Data | migration_summary, compatibility_rules |
| `cassandra-partition-reviewer` | Data | access_pattern, partition_design |
| `data-quality-triage` | Data | quality_summary, data_contract |
| `pii-minimization-planner` | Data | field_descriptions, task_scope |
| `retention-review-assistant` | Data | retention_proposal, retention_policy |
| `lineage-gap-reviewer` | Data | lineage_record, lineage_requirements |
| `query-intent-router` | Data | analysis_request, query_inventory |
| `index-recommendation-reviewer` | Data | index_proposal, query_evidence |
| `streaming-contract-reviewer` | Data | event_schema, consumer_requirements |
| `data-export-reviewer` | Data | export_request, export_policy |
| `pull-request-scope-reviewer` | Development | patch_summary, issue_scope |
| `test-gap-reviewer` | Development | change_summary, test_inventory |
| `api-compatibility-reviewer` | Development | api_change, client_contracts |
| `build-failure-router` | Development | build_failure, build_routing_policy |
| `release-note-reviewer` | Development | release_notes, merged_changes |
| `documentation-drift-checker` | Development | documentation_excerpt, code_contract |
| `code-review-prioritizer` | Development | patch_areas, review_rubric |
| `feature-flag-reviewer` | Development | flag_plan, lifecycle_checklist |
| `dependency-upgrade-reviewer` | Development | upgrade_proposal, migration_requirements |
| `reproducibility-checker` | Development | bug_report, reproduction_checklist |
| `citation-support-checker` | Research | claim, source_passages |
| `source-relevance-scorer` | Research | research_question, source_excerpt |
| `conflicting-evidence-router` | Research | evidence_set, claim_scope |
| `experiment-design-reviewer` | Research | experiment_plan, evaluation_objective |
| `benchmark-comparability-checker` | Research | benchmark_pair, comparison_rules |
| `paper-limitation-reviewer` | Research | paper_summary, limitations_excerpt |
| `research-question-decomposer` | Research | research_question, subquestion_plan |
| `evidence-freshness-reviewer` | Research | freshness_facts, update_policy |
| `dataset-documentation-reviewer` | Research | dataset_documentation, disclosure_checklist |
| `editorial-claim-reviewer` | Research | draft_claims, evidence_ledger |
| `feature-request-router` | Product | feature_request, product_areas |
| `user-story-readiness-checker` | Product | user_story, readiness_checklist |
| `experiment-rollout-reviewer` | Product | experiment_brief, stop_condition_policy |
| `accessibility-issue-triage` | Product | finding, severity_rubric |
| `onboarding-friction-reviewer` | Product | journey_summary, onboarding_requirements |
| `pricing-copy-consistency-checker` | Product | pricing_copy, plan_entitlements |
| `subscription-entitlement-reviewer` | Product | experience_summary, entitlement_specification |
| `checkout-failure-router` | Product | checkout_error, routing_playbook |
| `cancellation-flow-reviewer` | Product | journey_description, cancellation_policy |
| `feedback-clustering-reviewer` | Product | feedback_examples, proposed_groups |
| `runbook-readiness-checker` | Operations | runbook, readiness_standard |
| `change-approval-reviewer` | Operations | change_request, approval_checklist |
| `incident-timeline-reviewer` | Operations | ordered_timeline, timeline_requirements |
| `postmortem-action-reviewer` | Operations | action_items, contributing_factors |
| `alert-deduplication-reviewer` | Operations | alert_group, correlation_evidence |
| `maintenance-notice-reviewer` | Operations | notice, maintenance_plan |
| `vendor-incident-router` | Operations | disruption_summary, dependency_inventory |
| `service-health-reviewer` | Operations | service_summary, health_indicators |
| `recovery-validation-reviewer` | Operations | recovery_tests, failure_record |
| `operational-handoff-router` | Operations | operational_question, ownership_policy |
| `career-skill-gap-coach` | Learning | self_assessment, learning_goal |
| `system-design-feedback-agent` | Learning | learner_architecture, workload_requirements |
| `agent-design-feedback-agent` | Learning | agent_design, exercise_rubric |
| `fine-tuning-readiness-coach` | Learning | dataset_plan, training_rubric |
| `interview-practice-reviewer` | Learning | practice_answer, exercise_rubric |
| `debugging-hint-selector` | Learning | debugging_evidence, hint_policy |
| `lab-submission-reviewer` | Learning | lab_report, assignment_requirements |
| `study-plan-feasibility-reviewer` | Learning | study_plan, learner_constraints |
| `concept-misconception-checker` | Learning | learner_explanation, reference_definition |
| `learning-resource-router` | Learning | resource_summary, learner_goal |
| `model-routing-reviewer` | Agent systems | model_choice, workload_constraints |
| `memory-write-reviewer` | Agent systems | memory_candidate, memory_policy |
| `retrieval-sufficiency-gate` | Agent systems | user_question, retrieved_passages |
| `tool-result-verifier` | Agent systems | tool_result, observation_contract |
| `human-approval-packet-reviewer` | Agent systems | approval_packet, effect_specification |
| `agent-loop-stop-reviewer` | Agent systems | progress_summary, stop_policy |
| `context-pruning-reviewer` | Agent systems | pruning_proposal, task_evidence_requirements |
| `multi-agent-handoff-reviewer` | Agent systems | handoff_packet, receiver_contract |
| `output-delivery-reviewer` | Agent systems | candidate_answer, output_contract |
| `release-evaluation-reviewer` | Agent systems | evaluation_report, release_gate |
