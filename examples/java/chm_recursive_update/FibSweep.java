// Author: Sandeep Belgavi. Which n first fails for a memoised fib on a fresh ConcurrentHashMap (JDK 23)?
import java.util.*; import java.util.concurrent.*;
public class FibSweep {
  static Map<Integer, Long> m;
  static long fib(int n){ if(n<2) return n; return m.computeIfAbsent(n, k -> fib(k-1)+fib(k-2)); }
  public static void main(String[] a){
    for(int cap : new int[]{16, 64}){
      StringBuilder sb=new StringBuilder("initialCapacity "+cap+":");
      for(int n=2;n<=40;n++){ m=new ConcurrentHashMap<>(cap); try{ fib(n); sb.append(" ").append(n).append("=ok"); }catch(IllegalStateException e){ sb.append(" ").append(n).append("=ISE"); } }
      System.out.println(sb);
    }
  }
}
