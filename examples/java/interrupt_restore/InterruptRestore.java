// Author: Sandeep Belgavi. What swallowing InterruptedException does to executor shutdown.
// Synthetic workers for the fictional Belgavi's Book Store; plain Java, no dependencies.
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

public final class InterruptRestore {
    static final AtomicBoolean HARD_STOP = new AtomicBoolean();  // test cleanup only

    /** Polls for new help-desk cases; catches the interrupt, logs it and keeps going. */
    static Runnable swallowing(AtomicInteger swallowed) {
        return () -> {
            while (!HARD_STOP.get()) {
                try {
                    Thread.sleep(20);
                } catch (InterruptedException e) {
                    swallowed.incrementAndGet();  // "log and retry": the interrupt status is now clear
                }
            }
        };
    }

    /** Same loop, but an interrupt ends the task. */
    static Runnable propagating() {
        return () -> {
            try {
                while (true) Thread.sleep(20);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();  // restore, then leave
            }
        };
    }

    /** A helper that cannot throw InterruptedException restores the flag; the caller's loop checks it. */
    static boolean pauseQuietly(long ms) {
        try {
            Thread.sleep(ms);
            return true;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }

    static Runnable restoringHelperLoop(AtomicInteger iterations) {
        return () -> {
            while (!Thread.currentThread().isInterrupted()) {
                pauseQuietly(20);
                iterations.incrementAndGet();
            }
        };
    }

    /** Blocks on a queue; swallowing here hides the interrupt from the next take() too. */
    static Runnable queueSwallowing(BlockingQueue<String> q, AtomicInteger swallowed) {
        return () -> {
            while (!HARD_STOP.get()) {
                try {
                    q.poll(20, TimeUnit.MILLISECONDS);
                } catch (InterruptedException e) {
                    swallowed.incrementAndGet();
                }
            }
        };
    }

    static boolean stopsWithin(Runnable task, long millis) throws InterruptedException {
        ExecutorService pool = Executors.newSingleThreadExecutor();
        pool.submit(task);
        Thread.sleep(60);
        pool.shutdownNow();
        boolean stopped = pool.awaitTermination(millis, TimeUnit.MILLISECONDS);
        return stopped;
    }

    public static Map<String, Object> run() throws InterruptedException {
        Map<String, Object> out = new LinkedHashMap<>();
        HARD_STOP.set(false);
        AtomicInteger swallowed = new AtomicInteger();
        out.put("swallowing_stopped_in_500ms", stopsWithin(swallowing(swallowed), 500));
        out.put("swallowing_interrupts_caught", swallowed.get());
        AtomicInteger qSwallowed = new AtomicInteger();
        out.put("queue_swallowing_stopped_in_500ms", stopsWithin(queueSwallowing(new LinkedBlockingQueue<>(), qSwallowed), 500));
        out.put("queue_interrupts_caught", qSwallowed.get());
        HARD_STOP.set(true);  // release the stuck threads so the JVM can exit
        out.put("propagating_stopped_in_500ms", stopsWithin(propagating(), 500));
        AtomicInteger loops = new AtomicInteger();
        out.put("restoring_helper_stopped_in_500ms", stopsWithin(restoringHelperLoop(loops), 500));
        Thread.interrupted();
        out.put("interrupted_clears_flag", demoInterruptedClears());
        return out;
    }

    static String demoInterruptedClears() {
        Thread.currentThread().interrupt();
        boolean first = Thread.interrupted();
        boolean second = Thread.interrupted();
        return first + "," + second;
    }

    public static void main(String[] args) throws Exception {
        run().forEach((k, v) -> System.out.println(k + "=" + v));
    }
}
