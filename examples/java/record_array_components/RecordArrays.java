// Author: Sandeep Belgavi. Records with array components: what the generated members do, and three fixes.
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public final class RecordArrays {

    /** Generated equals, hashCode and toString; the array is compared by reference. */
    public record ReturnBatch(String caseId, String[] isbns) {}

    /** Defensive copies plus content-based equals, hashCode and toString. */
    public record SafeReturnBatch(String caseId, String[] isbns) {
        public SafeReturnBatch {
            Objects.requireNonNull(caseId, "caseId");
            isbns = isbns.clone();                 // the caller's array can change later
        }
        @Override public String[] isbns() { return isbns.clone(); }
        @Override public boolean equals(Object o) {
            return o instanceof SafeReturnBatch other && caseId.equals(other.caseId) && Arrays.equals(isbns, other.isbns);
        }
        @Override public int hashCode() { return 31 * caseId.hashCode() + Arrays.hashCode(isbns); }
        @Override public String toString() { return "SafeReturnBatch[caseId=" + caseId + ", isbns=" + Arrays.toString(isbns) + "]"; }
    }

    /** An unmodifiable List component: the generated members already compare contents. */
    public record ListReturnBatch(String caseId, List<String> isbns) {
        public ListReturnBatch { isbns = List.copyOf(isbns); }
    }

    static String[] sample() { return new String[] {"9780000000017", "9780000000024"}; }

    public static void main(String[] args) {
        ReturnBatch a = new ReturnBatch("CASE-6101", sample());
        ReturnBatch b = new ReturnBatch("CASE-6101", sample());
        System.out.println("generated equals on equal contents: " + a.equals(b));
        System.out.println("generated hashCode equal: " + (a.hashCode() == b.hashCode()));
        Set<ReturnBatch> seen = new HashSet<>(List.of(a));
        System.out.println("HashSet.contains(b): " + seen.contains(b));
        System.out.println("toString: " + a);
        a.isbns()[0] = "9789999999999";
        System.out.println("after writing through the accessor: " + a.isbns()[0]);

        SafeReturnBatch s1 = new SafeReturnBatch("CASE-6101", sample());
        SafeReturnBatch s2 = new SafeReturnBatch("CASE-6101", sample());
        System.out.println("safe equals: " + s1.equals(s2) + ", safe hash equal: " + (s1.hashCode() == s2.hashCode()));
        s1.isbns()[0] = "9789999999999";
        System.out.println("safe after writing through the accessor: " + s1.isbns()[0]);
        System.out.println("safe toString: " + s1);

        ListReturnBatch l1 = new ListReturnBatch("CASE-6101", Arrays.asList(sample()));
        ListReturnBatch l2 = new ListReturnBatch("CASE-6101", List.of(sample()));
        System.out.println("list equals: " + l1.equals(l2) + ", list toString: " + l1);
    }
}
