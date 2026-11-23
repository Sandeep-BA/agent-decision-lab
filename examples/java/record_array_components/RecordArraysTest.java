// Author: Sandeep Belgavi. Plain-Java checks (no test framework) for RecordArrays.
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class RecordArraysTest {
    static int passed = 0;

    static void check(String name, boolean ok) {
        if (!ok) throw new AssertionError(name);
        passed++;
        System.out.println("ok " + passed + " " + name);
    }

    public static void main(String[] args) {
        String[] shared = RecordArrays.sample();
        var a = new RecordArrays.ReturnBatch("CASE-6101", shared);
        var b = new RecordArrays.ReturnBatch("CASE-6101", RecordArrays.sample());
        check("generated equals compares the array by reference", !a.equals(b));
        check("same array instance makes them equal", a.equals(new RecordArrays.ReturnBatch("CASE-6101", shared)));
        Set<RecordArrays.ReturnBatch> set = new HashSet<>(List.of(a));
        check("a HashSet does not deduplicate equal contents", !set.contains(b));
        check("generated toString prints an identity string", a.toString().matches(".*isbns=\\[Ljava\\.lang\\.String;@[0-9a-f]+\\]"));
        shared[0] = "changed";
        check("mutating the caller's array changes the record", a.isbns()[0].equals("changed"));

        String[] input = RecordArrays.sample();
        var s = new RecordArrays.SafeReturnBatch("CASE-6101", input);
        input[0] = "changed";
        check("compact constructor copies the input", s.isbns()[0].equals("9780000000017"));
        s.isbns()[1] = "changed";
        check("accessor returns a copy", s.isbns()[1].equals("9780000000024"));
        var s2 = new RecordArrays.SafeReturnBatch("CASE-6101", RecordArrays.sample());
        check("safe equals and hashCode use contents", s.equals(s2) && s.hashCode() == s2.hashCode());
        check("safe toString lists the elements", s.toString().endsWith("[9780000000017, 9780000000024]]"));

        var l = new RecordArrays.ListReturnBatch("CASE-6101", Arrays.asList(RecordArrays.sample()));
        check("List component compares contents", l.equals(new RecordArrays.ListReturnBatch("CASE-6101", List.of(RecordArrays.sample()))));
        boolean threw = false;
        try { l.isbns().set(0, "x"); } catch (UnsupportedOperationException e) { threw = true; }
        check("List.copyOf makes the component unmodifiable", threw);
        System.out.println(passed + " checks passed");
    }
}
