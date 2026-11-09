// Author: Sandeep Belgavi. Portable checks; an empty trace is never required.
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;

public class TraceProbeCheck {
    public static void main(String[] args) {
        try {
            TraceProbe.main(new String[] {"0"});
            throw new AssertionError("nonpositive rounds must be rejected");
        } catch (IllegalArgumentException expected) {
            // rejected as intended
        }
        PrintStream original = System.out;
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        System.setOut(new PrintStream(buffer));
        TraceProbe.main(new String[] {"1000"});
        System.setOut(original);
        String line = buffer.toString().trim();
        if (!line.matches("rounds=1000 empty=\\d+ first=-?\\d+")) throw new AssertionError(line);
        int empty = Integer.parseInt(line.replaceAll(".*empty=(\\d+).*", "$1"));
        if (empty > 1000) throw new AssertionError("counter out of range: " + line);
        System.out.println("checks passed: " + line);
    }
}
