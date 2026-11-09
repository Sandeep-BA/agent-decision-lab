// Author: Sandeep Belgavi. Synthetic HotSpot diagnostic fixture.
public class TraceProbe {
    static int length(String value) { return value.length(); }

    public static void main(String[] args) {
        int rounds = Integer.parseInt(args[0]);
        if (rounds < 1) throw new IllegalArgumentException("positive rounds");
        int empty = 0;
        int first = -1;
        for (int i = 0; i < rounds; i++) {
            try {
                length(null);
            } catch (NullPointerException failure) {
                if (failure.getStackTrace().length == 0) {
                    empty++;
                    if (first < 0) first = i;
                }
            }
        }
        System.out.printf("rounds=%d empty=%d first=%d%n", rounds, empty, first);
    }
}
