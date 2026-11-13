"""Measure what ParentBased(AlwaysOn) does with an unsampled inbound traceparent.

Author: Sandeep Belgavi. Uses the real OpenTelemetry Python SDK with an
in-memory exporter; no network, no collector, no web framework. Four ways a
server can treat a traceparent header that a platform (not the caller) set:

  continue  - make it the parent (what a framework's server span does by default)
  ignore    - start a new root trace
  link      - start a new root trace and add a span link to the platform context
  dedicated - continue only a separate, caller-owned header if present
"""
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import ParentBased, ALWAYS_ON
from opentelemetry.trace import Link
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

PLATFORM_UNSAMPLED = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-00"
PLATFORM_SAMPLED = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
CALLER = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

exporter = InMemorySpanExporter()
provider = TracerProvider(sampler=ParentBased(root=ALWAYS_ON))
provider.add_span_processor(SimpleSpanProcessor(exporter))
tracer = provider.get_tracer("belgavi.bookstore.agent")
prop = TraceContextTextMapPropagator()


def handle(headers, mode):
    """Simulate one agent request: a server span, a model call and a tool call."""
    exporter.clear()
    platform_ctx = prop.extract({"traceparent": headers["traceparent"]}) if "traceparent" in headers else Context()
    links = []
    if mode == "continue":
        parent = platform_ctx
    elif mode == "ignore":
        parent = Context()
    elif mode == "link":
        parent = Context()
        sc = trace.get_current_span(platform_ctx).get_span_context()
        if sc.is_valid:
            links = [Link(sc, {"link.reason": "platform traceparent"})]
    elif mode == "dedicated":
        h = headers.get("x-caller-traceparent")
        parent = prop.extract({"traceparent": h}) if h else Context()
    else:
        raise ValueError(mode)
    with tracer.start_as_current_span("POST /run CASE-8040", context=parent, links=links) as server:
        with tracer.start_as_current_span("model.generate"):
            pass
        with tracer.start_as_current_span("tool.lookup_order"):
            pass
        recording = server.is_recording()
        trace_id = format(server.get_span_context().trace_id, "032x")
    spans = exporter.get_finished_spans()
    return {"mode": mode, "exported": len(spans), "server_recording": recording,
            "trace_id": trace_id, "links": sum(len(s.links) for s in spans)}


SCENARIOS = [
    ("platform unsampled", {"traceparent": PLATFORM_UNSAMPLED}),
    ("platform sampled", {"traceparent": PLATFORM_SAMPLED}),
    ("platform unsampled + caller header", {"traceparent": PLATFORM_UNSAMPLED, "x-caller-traceparent": CALLER}),
    ("no header", {}),
]


def table():
    rows = []
    for name, headers in SCENARIOS:
        for mode in ("continue", "ignore", "link", "dedicated"):
            r = handle(headers, mode)
            r["scenario"] = name
            rows.append(r)
    return rows


if __name__ == "__main__":
    import importlib.metadata as md
    print("opentelemetry-sdk", md.version("opentelemetry-sdk"))
    print(f"{'scenario':38} {'mode':10} exported recording links trace_id")
    for r in table():
        print(f"{r['scenario']:38} {r['mode']:10} {r['exported']:8} {str(r['server_recording']):9} {r['links']:5} {r['trace_id']}")
