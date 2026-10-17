# Build and test a bounded Jev adapter in Java

Author: Sandeep Belgavi · Reviewed 18 October 2026

A Java application does not need to represent every provider feature to make one useful, testable decision. Start with a narrow adapter for a Choice question. Keep HTTP transport, response parsing and application policy separate so each failure can be reproduced without a live API key.

<!-- diagram:Java recipe|Request builder|Bounded HTTPS|Response parser|Policy engine -->

## Define the boundary in Java

Agent Decision Lab exposes an `Engine.Model` interface. The interface receives a recipe and minimized state, then returns a decision. The engine remains responsible for checking the option set, probability ranges, approval and the final recommendation status. That prevents the provider adapter from becoming a second, inconsistent policy engine.

`JevClient` implements that interface using the [documented TypeSafe endpoint](https://docs.typesafe.ai/api). It constructs a request from the recipe's task and criteria, with one question named `decision`. The implementation supports Choice, not every provider primitive. A source comment and the README state that it is an independent HTTP adapter, not an official Java SDK.

## Keep secrets and destinations controlled

The live constructor obtains its key from the caller and sends it in an authorization header to a fixed HTTPS destination. It does not accept a model-generated base URL or follow redirects. This matters because an otherwise correct HTTP client can leak credentials if it sends an authorization header to an attacker-selected endpoint.

The CLI reads `TYPESAFE_API_KEY` from the process environment. Do not paste the real value into shell history, source files or screenshots. Environment variables are a convenient local mechanism, not a complete secret-management system: a deployed service should use its platform's secret facilities and access controls.

## Bound failure, not only successful output

The adapter caps both request and response bodies at 64 KiB. Its response subscriber counts bytes before accepting additional chunks, so it does not first allocate an unlimited response and only then discover that it was too large. The HTTP request has a timeout and redirects are disabled. Provider errors become a generic unavailable status rather than exposing raw response bodies.

There are no automatic retries in the example. A caller can later add a bounded retry policy for transient failures, but it should account for repeated costs, request deadlines and provider rate limits. Retrying a decision call is different from retrying a business effect; neither should be hidden behind an unlimited loop.

## Run the code locally

Clone [Agent Decision Lab](https://github.com/Sandeep-BA/agent-decision-lab), install Java 17 or newer and Maven, then run `mvn verify`. Start with `java -jar target/agent-decision-lab.jar ticket-triage`. This uses a fixed fixture and makes no provider call. It is useful for seeing the trace and approval behavior, but it does not classify the example evidence.

For an authorized live test, prepare a small input file with the exact evidence fields declared by the recipe. Set the key and a versioned model identifier in the environment, then use `--live --state /path/to/input.json`. That command sends the selected fields to the provider and may incur charges. Initial repository validation did not perform a paid live call.

## Test transport and semantics separately

The contract test injects a fake transport, inspects the generated request and supplies a controlled provider response. Engine tests then reject unknown options, invalid probabilities, missing evidence and low-confidence results. These checks are repeatable without a network and should run on every change.

Add a small live smoke test only after credentials and data handling are configured. Record the model returned by the provider and compare response shape with the contract. A passing live smoke test establishes connectivity and a sample response; it does not establish accuracy, calibration or production reliability.

The architecture diagram shows the adapter's application layers. It intentionally stops before a business action: a valid Java object is a recommendation input, not authorization to deploy infrastructure, send money or change an account.
