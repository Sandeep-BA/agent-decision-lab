// Author: Sandeep Belgavi. Plain-Java checks for the numbers quoted in the article and README.
import java.util.List;
import java.util.TreeSet;

public final class ComparatorContractTest {
    static int passed = 0;

    static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError("FAILED: " + what);
        passed++;
    }

    public static void main(String[] args) {
        var xs = ComparatorContract.fixture();
        check(ComparatorContract.TRUNCATED_LONG.compare(xs.get(0), xs.get(2)) > 0,
                "an order 30 days older compares as later after truncation");
        check(ComparatorContract.sortedIds(xs, ComparatorContract.TRUNCATED_LONG)
                .equals(List.of("ORD-1001", "ORD-1002", "ORD-1005", "ORD-1003", "ORD-1004")), "truncated sort order");
        check(ComparatorContract.sortedIds(xs, ComparatorContract.TOTAL_ORDER)
                .equals(List.of("ORD-1001", "ORD-1002", "ORD-1003", "ORD-1004", "ORD-1005")), "total-order sort");
        check(ComparatorContract.transitivityViolations(xs, ComparatorContract.TRUNCATED_LONG) == 12, "12 truncated violations");
        check(ComparatorContract.transitivityViolations(xs, ComparatorContract.SUBTRACTED_INT) == 15, "15 subtracted violations");
        check(ComparatorContract.transitivityViolations(xs, ComparatorContract.TOTAL_ORDER) == 0, "total order is transitive");
        check(ComparatorContract.symmetryViolations(xs, ComparatorContract.TOTAL_ORDER) == 0, "total order is symmetric");
        check(ComparatorContract.SUBTRACTED_INT.compare(xs.get(3), xs.get(4)) < 0, "MAX - (MIN+1) wraps negative");
        TreeSet<ComparatorContract.Order> byTime = new TreeSet<>(ComparatorContract.TIME_ONLY);
        byTime.addAll(xs);
        check(byTime.size() == 4, "time-only TreeSet drops one of two same-time orders");
        check(ComparatorContract.bulkSort(ComparatorContract.TOTAL_ORDER, 2000, 42).equals("sorted"), "total order sorts");
        String r = ComparatorContract.bulkSort(ComparatorContract.TRUNCATED_LONG, 2000, 42);
        check(!r.equals("sorted"), "truncated comparator fails on seed 42: " + r);
        boolean sawThrow = false;
        for (long seed = 1; seed <= 50 && !sawThrow; seed++)
            sawThrow = ComparatorContract.bulkSort(ComparatorContract.TRUNCATED_LONG, 2000, seed)
                    .equals("IllegalArgumentException: Comparison method violates its general contract!");
        check(sawThrow, "TimSort detects the violation on at least one seed");
        System.out.println(passed + " checks passed");
    }
}
