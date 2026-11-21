// Author: Sandeep Belgavi. Comparator overflow and the Comparator contract, on synthetic orders
// from the fictional Belgavi's Book Store. Standard library only.
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Random;
import java.util.TreeSet;

public final class ComparatorContract {
    public record Order(String id, long createdAtMillis, int adjustmentPaise) {}

    static final long DAY = 86_400_000L;
    static final long BASE = 1_793_000_000_000L; // a fixed synthetic epoch-millisecond origin

    /** Truncates a long difference to int: wrong once two orders are more than about 24.8 days apart. */
    static final Comparator<Order> TRUNCATED_LONG = (a, b) -> (int) (a.createdAtMillis() - b.createdAtMillis());
    /** Subtracts ints: overflows when the operands have opposite signs and large magnitudes. */
    static final Comparator<Order> SUBTRACTED_INT = (a, b) -> a.adjustmentPaise() - b.adjustmentPaise();
    /** Correct: compares without arithmetic, then breaks ties by id so compare()==0 only for the same id. */
    static final Comparator<Order> TOTAL_ORDER =
            Comparator.comparingLong(Order::createdAtMillis).thenComparing(Order::id);
    static final Comparator<Order> TIME_ONLY = Comparator.comparingLong(Order::createdAtMillis);

    static List<Order> fixture() {
        return List.of(
                new Order("ORD-1001", BASE, 0),
                new Order("ORD-1002", BASE + 10 * DAY, 25_000),
                new Order("ORD-1003", BASE + 30 * DAY, -25_000),
                new Order("ORD-1004", BASE + 30 * DAY, Integer.MAX_VALUE),
                new Order("ORD-1005", BASE + 60 * DAY, Integer.MIN_VALUE + 1));
    }

    /** Pairs where signum(compare(x, y)) != -signum(compare(y, x)). */
    static int symmetryViolations(List<Order> xs, Comparator<Order> c) {
        int bad = 0;
        for (Order x : xs) for (Order y : xs)
            if (Integer.signum(c.compare(x, y)) != -Integer.signum(c.compare(y, x))) bad++;
        return bad;
    }

    /** Triples where x > y and y > z but not x > z. */
    static int transitivityViolations(List<Order> xs, Comparator<Order> c) {
        int bad = 0;
        for (Order x : xs) for (Order y : xs) for (Order z : xs)
            if (c.compare(x, y) > 0 && c.compare(y, z) > 0 && !(c.compare(x, z) > 0)) bad++;
        return bad;
    }

    static List<String> sortedIds(List<Order> xs, Comparator<Order> c) {
        List<Order> copy = new ArrayList<>(xs);
        copy.sort(c);
        return copy.stream().map(Order::id).toList();
    }

    /** Sorts many random orders over 120 days; returns the exception message, or "sorted". */
    static String bulkSort(Comparator<Order> c, int n, long seed) {
        Random r = new Random(seed);
        Order[] xs = new Order[n];
        for (int i = 0; i < n; i++)
            xs[i] = new Order("ORD-" + (5000 + i), BASE + (long) (r.nextDouble() * 120 * DAY), 0);
        try {
            Arrays.sort(xs, c);
        } catch (IllegalArgumentException e) {
            return "IllegalArgumentException: " + e.getMessage();
        }
        for (int i = 1; i < n; i++)
            if (xs[i - 1].createdAtMillis() > xs[i].createdAtMillis()) return "sorted out of order at index " + i;
        return "sorted";
    }

    public static void main(String[] args) {
        List<Order> xs = fixture();
        Order a = xs.get(0), c = xs.get(2);
        System.out.println("30 days apart, truncated compare(ORD-1001, ORD-1003) = " + TRUNCATED_LONG.compare(a, c));
        System.out.println("truncated sort  " + sortedIds(xs, TRUNCATED_LONG));
        System.out.println("total-order sort " + sortedIds(xs, TOTAL_ORDER));
        System.out.println("symmetry violations: truncated=" + symmetryViolations(xs, TRUNCATED_LONG)
                + " subtracted=" + symmetryViolations(xs, SUBTRACTED_INT) + " total=" + symmetryViolations(xs, TOTAL_ORDER));
        System.out.println("transitivity violations: truncated=" + transitivityViolations(xs, TRUNCATED_LONG)
                + " subtracted=" + transitivityViolations(xs, SUBTRACTED_INT) + " total=" + transitivityViolations(xs, TOTAL_ORDER));
        System.out.println("subtracted compare(MAX, MIN+1) = " + SUBTRACTED_INT.compare(xs.get(3), xs.get(4)));
        TreeSet<Order> byTime = new TreeSet<>(TIME_ONLY);
        byTime.addAll(xs);
        TreeSet<Order> total = new TreeSet<>(TOTAL_ORDER);
        total.addAll(xs);
        System.out.println("TreeSet sizes: time-only=" + byTime.size() + " total-order=" + total.size());
        System.out.println("bulk sort 2000 orders, truncated: " + bulkSort(TRUNCATED_LONG, 2000, 42));
        System.out.println("bulk sort 2000 orders, total: " + bulkSort(TOTAL_ORDER, 2000, 42));
        int threw = 0, silent = 0;
        for (long seed = 1; seed <= 50; seed++) {
            String r = bulkSort(TRUNCATED_LONG, 2000, seed);
            if (r.startsWith("IllegalArgumentException")) threw++;
            else if (!r.equals("sorted")) silent++;
        }
        System.out.println("truncated, seeds 1-50: threw=" + threw + " silently-misordered=" + silent);
    }
}
