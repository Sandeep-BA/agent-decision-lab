// Author: Sandeep Belgavi. Plain-Java checks; mirrors the four cases in ADK Java's own
// LlmAgentAsNodeTest additions in commit 8e56693, restated against this standalone model.
import java.util.List;

public final class HistoryContractTest {
    static int passed = 0;

    static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError("FAILED: " + what);
        passed++;
    }

    public static void main(String[] args) {
        var H = HistoryContract.HISTORY;
        var in = HistoryContract.NODE_INPUT;
        check(HistoryContract.requestContents(HistoryContract.DRAFTER_UNSET, true, true, H, in).equals(List.of(in)),
                "unset SINGLE_TURN node sees only its input");
        check(HistoryContract.requestContents(HistoryContract.DRAFTER_PINNED, true, true, H, in).size() == 3,
                "explicit DEFAULT keeps the history");
        check(HistoryContract.effective(HistoryContract.REFUNDER, false, true) == HistoryContract.IncludeContents.DEFAULT,
                "agent without a mode keeps the history");
        check(HistoryContract.requestContents(HistoryContract.DRAFTER_UNSET, true, false, H, in).size() == 3,
                "before the change an unset node saw the history");
        var pins = List.of(new HistoryContract.Expectation("classify", HistoryContract.IncludeContents.NONE),
                new HistoryContract.Expectation("draft_reply", HistoryContract.IncludeContents.DEFAULT));
        check(HistoryContract.checkContract(List.of(HistoryContract.CLASSIFIER, HistoryContract.DRAFTER_UNSET), pins, true)
                .equals(List.of("draft_reply: expected DEFAULT but runs with NONE (setting left unset)")), "upgrade flags the drafter");
        check(HistoryContract.checkContract(List.of(HistoryContract.CLASSIFIER, HistoryContract.DRAFTER_PINNED), pins, true).isEmpty(),
                "pinned drafter passes");
        check(HistoryContract.checkContract(List.of(HistoryContract.CLASSIFIER), pins, true)
                .equals(List.of("draft_reply: no such node")), "missing node is reported");
        check(HistoryContract.REFUNDER.allowedTools().equals(List.of("refund.issue")), "history setting does not change tools");
        System.out.println(passed + " checks passed");
    }
}
