// Author: Sandeep Belgavi. A standalone model of how ADK Java 1.15.0 decides how much session
// history an LlmAgent sees when it runs as a workflow node. It does NOT use ADK: it restates the
// rule from commit 8e56693 (Contents.includeContents) so the decision can be tested and audited
// as an explicit input contract. Synthetic help-desk turns from the fictional Belgavi's Book Store.
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public final class HistoryContract {
    enum IncludeContents { DEFAULT, NONE }
    enum Mode { SINGLE_TURN }

    /** includeContents is null when the builder never set it; that is the distinction 1.15.0 adds. */
    record Agent(String name, Optional<Mode> mode, IncludeContents includeContents, List<String> allowedTools) {
        IncludeContents configured() { return includeContents == null ? IncludeContents.DEFAULT : includeContents; }
        boolean explicit() { return includeContents != null; }
    }

    /** Same shape as the 1.15.0 rule: a SINGLE_TURN node with an unset setting runs with NONE. */
    static IncludeContents effective(Agent agent, boolean runningAsSingleTurnNode, boolean v115) {
        if (!v115) return agent.configured();
        return runningAsSingleTurnNode && !agent.explicit() ? IncludeContents.NONE : agent.configured();
    }

    /** What the model request contains: the node input, plus earlier turns when history is on. */
    static List<String> requestContents(Agent agent, boolean singleTurnNode, boolean v115, List<String> history, String nodeInput) {
        List<String> out = new ArrayList<>();
        if (effective(agent, singleTurnNode, v115) == IncludeContents.DEFAULT) out.addAll(history);
        out.add(nodeInput);
        return out;
    }

    /** A pinned expectation per node, checked at startup so an upgrade cannot silently change it. */
    record Expectation(String node, IncludeContents expected) {}

    static List<String> checkContract(List<Agent> nodes, List<Expectation> expectations, boolean v115) {
        List<String> problems = new ArrayList<>();
        for (Expectation e : expectations) {
            Agent a = nodes.stream().filter(n -> n.name().equals(e.node())).findFirst().orElse(null);
            if (a == null) { problems.add(e.node() + ": no such node"); continue; }
            boolean single = a.mode().isPresent();
            IncludeContents got = effective(a, single, v115);
            if (got != e.expected()) problems.add(e.node() + ": expected " + e.expected() + " but runs with " + got
                    + (a.explicit() ? "" : " (setting left unset)"));
        }
        return problems;
    }

    static final List<String> HISTORY = List.of(
            "user: My order 4417 arrived damaged. I am Jenya, account J-208.",
            "triage: Damaged item; refund path.");
    static final String NODE_INPUT = "Draft a reply confirming a refund of 499 rupees for order 4417.";

    static final Agent CLASSIFIER = new Agent("classify", Optional.of(Mode.SINGLE_TURN), null, List.of());
    static final Agent DRAFTER_UNSET = new Agent("draft_reply", Optional.of(Mode.SINGLE_TURN), null, List.of());
    static final Agent DRAFTER_PINNED = new Agent("draft_reply", Optional.of(Mode.SINGLE_TURN), IncludeContents.DEFAULT, List.of());
    static final Agent REFUNDER = new Agent("issue_refund", Optional.empty(), null, List.of("refund.issue"));

    public static void main(String[] args) {
        System.out.println("draft_reply unset, rule before 8e56693: " + requestContents(DRAFTER_UNSET, true, false, HISTORY, NODE_INPUT).size() + " contents");
        System.out.println("draft_reply unset, 1.15.0 rule: " + requestContents(DRAFTER_UNSET, true, true, HISTORY, NODE_INPUT));
        System.out.println("draft_reply pinned DEFAULT, 1.15.0 rule: " + requestContents(DRAFTER_PINNED, true, true, HISTORY, NODE_INPUT).size() + " contents");
        System.out.println("issue_refund (no mode), 1.15.0 rule: " + effective(REFUNDER, false, true));
        List<Expectation> pins = List.of(new Expectation("classify", IncludeContents.NONE), new Expectation("draft_reply", IncludeContents.DEFAULT));
        System.out.println("contract on rule before 8e56693, unset drafter: " + checkContract(List.of(CLASSIFIER, DRAFTER_UNSET), pins, false));
        System.out.println("contract on 1.15.0 rule, unset drafter: " + checkContract(List.of(CLASSIFIER, DRAFTER_UNSET), pins, true));
        System.out.println("contract on 1.15.0 rule, pinned drafter: " + checkContract(List.of(CLASSIFIER, DRAFTER_PINNED), pins, true));
        System.out.println("NONE hides history but not tools: issue_refund tools=" + REFUNDER.allowedTools());
    }
}
