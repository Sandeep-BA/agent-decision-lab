# Upgrade Checkpoint Readers Before Writers When a State Format Changes

Author: **Sandeep Belgavi**.

Companion for https://aicassindra.com/blogs/agents/openai_agents_alpha2_checkpoint_readers_first.html (publication pending). Prerequisites: Node.js; the tested exact version is recorded in `.node-version`. No package dependencies or installation required.

Run `node example.cjs`; test `node test.cjs`. Inputs are in `fixture.json`; successful local execution saves `expected.json`. Both labs share `../daily-20261124-models.cjs`, the original browser model, so the demonstration and UI use identical arithmetic.

The output includes all decision rows and explicit limitations. This is an offline synthetic experiment, not a real model evaluation, SDK checkpoint or recovery test. The site's model suite adds boundary tests and invalid-input checks. Views are my own and do not represent any employer, past or present.
