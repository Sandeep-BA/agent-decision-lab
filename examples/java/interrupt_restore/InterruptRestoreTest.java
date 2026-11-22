// Author: Sandeep Belgavi. Plain-Java checks of the outcomes quoted in the article and README.
import java.util.Map;

public final class InterruptRestoreTest {
    static int passed = 0;

    static void check(String name, boolean ok) {
        if (!ok) throw new AssertionError(name);
        passed++;
        System.out.println("ok " + name);
    }

    public static void main(String[] args) throws Exception {
        Map<String, Object> r = InterruptRestore.run();
        check("swallowing worker survives shutdownNow", r.get("swallowing_stopped_in_500ms").equals(false));
        check("swallowing worker caught exactly one interrupt", r.get("swallowing_interrupts_caught").equals(1));
        check("queue worker survives shutdownNow", r.get("queue_swallowing_stopped_in_500ms").equals(false));
        check("queue worker caught exactly one interrupt", r.get("queue_interrupts_caught").equals(1));
        check("propagating worker stops", r.get("propagating_stopped_in_500ms").equals(true));
        check("restoring helper lets the loop stop", r.get("restoring_helper_stopped_in_500ms").equals(true));
        check("Thread.interrupted clears the flag", r.get("interrupted_clears_flag").equals("true,false"));
        System.out.println(passed + " checks passed");
    }
}
