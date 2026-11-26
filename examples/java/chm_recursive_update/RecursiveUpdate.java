// Author: Sandeep Belgavi. Probe: what JDK 23 does when a computeIfAbsent function touches the same map.
import java.util.*;
import java.util.concurrent.*;

public class RecursiveUpdate {
    static final Map<Integer, Long> CHM = new ConcurrentHashMap<>();
    static final Map<Integer, Long> HM = new HashMap<>();

    static long fibChm(int n) {
        if (n < 2) return n;
        return CHM.computeIfAbsent(n, k -> fibChm(k - 1) + fibChm(k - 2));
    }

    static long fibHm(int n) {
        if (n < 2) return n;
        return HM.computeIfAbsent(n, k -> fibHm(k - 1) + fibHm(k - 2));
    }

    static long fibLoop(int n, Map<Integer, Long> memo) {
        long a = 0, b = 1;
        for (int i = 0; i < n; i++) { long t = a + b; a = b; b = t; }
        memo.putIfAbsent(n, a);
        return a;
    }

    static final Map<Integer, Long> MEMO = new ConcurrentHashMap<>();
    static long fibGetThenPut(int n) {
        if (n < 2) return n;
        Long hit = MEMO.get(n);
        if (hit != null) return hit;
        long v = fibGetThenPut(n - 1) + fibGetThenPut(n - 2);
        Long prev = MEMO.putIfAbsent(n, v);
        return prev != null ? prev : v;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("java.version=" + System.getProperty("java.version"));
        try { System.out.println("chm fib(20)=" + fibChm(20)); }
        catch (Throwable t) { System.out.println("chm fib(20) threw " + t); }
        System.out.println("chm size after failure=" + CHM.size());
        try { System.out.println("hashmap fib(20)=" + fibHm(20)); }
        catch (Throwable t) { System.out.println("hashmap fib(20) threw " + t); }
        System.out.println("loop fib(90)=" + fibLoop(90, new ConcurrentHashMap<>()));
        System.out.println("get-then-put fib(90)=" + fibGetThenPut(90) + " memo size=" + MEMO.size());
        // Different keys, other map: safe.
        Map<String, Integer> lengths = new ConcurrentHashMap<>();
        Map<String, String> other = new ConcurrentHashMap<>(Map.of("k", "value"));
        System.out.println("other-map lookup=" + lengths.computeIfAbsent("k", k -> other.get(k).length()));
        // Same-bin collision probe: does touching a different key that hashes elsewhere also fail?
        Map<Integer, Integer> m = new ConcurrentHashMap<>();
        int far = 1 << 20;
        try { m.computeIfAbsent(1, k -> m.computeIfAbsent(far, j -> 7)); System.out.println("different-bin nested=ok size=" + m.size()); }
        catch (Throwable t) { System.out.println("different-bin nested threw " + t); }
        Map<Integer, Integer> m2 = new ConcurrentHashMap<>();
        try { m2.computeIfAbsent(1, k -> m2.computeIfAbsent(1, j -> 7)); System.out.println("same-key nested=ok"); }
        catch (Throwable t) { System.out.println("same-key nested threw " + t); }
        // Timeout-guarded threaded nesting to look for deadlock between two threads
        Map<Integer, Integer> m3 = new ConcurrentHashMap<>();
        CountDownLatch inside = new CountDownLatch(2);
        ExecutorService ex = Executors.newFixedThreadPool(2);
        Future<?> f1 = ex.submit(() -> m3.computeIfAbsent(1, k -> { inside.countDown(); await(inside); return m3.computeIfAbsent(2, j -> 20); }));
        Future<?> f2 = ex.submit(() -> m3.computeIfAbsent(2, k -> { inside.countDown(); await(inside); return m3.computeIfAbsent(1, j -> 10); }));
        try { f1.get(3, TimeUnit.SECONDS); f2.get(3, TimeUnit.SECONDS); System.out.println("two-thread cross nesting=completed"); }
        catch (TimeoutException te) { System.out.println("two-thread cross nesting=no progress after 3 s (deadlock)"); }
        catch (ExecutionException ee) { System.out.println("two-thread cross nesting threw " + ee.getCause()); }
        ex.shutdownNow();
        System.exit(0);
    }
    static void await(CountDownLatch l) { try { l.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }
}
