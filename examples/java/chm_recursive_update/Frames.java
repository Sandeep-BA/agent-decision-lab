// Author: Sandeep Belgavi. Which ConcurrentHashMap method throws Recursive update for each failing case (JDK 23).
import java.util.*; import java.util.concurrent.*;
public class Frames {
  static Map<Integer, Long> m;
  static long fib(int n){ if(n<2) return n; return m.computeIfAbsent(n, k -> fib(k-1)+fib(k-2)); }
  static void show(String label, Map<Integer,Long> map, int n){
    m = map;
    try { fib(n); System.out.println(label + ": ok"); }
    catch (IllegalStateException e) {
      StackTraceElement[] st = e.getStackTrace();
      long depth = Arrays.stream(st).filter(f -> f.getMethodName().equals("computeIfAbsent")).count();
      StringBuilder top = new StringBuilder();
      for (int i = 0; i < 3 && i < st.length; i++) top.append(st[i].getMethodName()).append(i < 2 ? " < " : "");
      System.out.println(label + ": " + e.getMessage() + "; top frames " + top + "; computeIfAbsent frames " + depth + "; map size " + map.size());
    }
  }
  public static void main(String[] a){
    show("default map, fib(20)", new ConcurrentHashMap<>(), 20);
    show("initialCapacity 16, fib(26)", new ConcurrentHashMap<>(16), 26);
    show("initialCapacity 16, fib(25)", new ConcurrentHashMap<>(16), 25);
  }
}
