// Author: Sandeep Belgavi. Synthetic initialization/body/cleanup failure matrix.
import java.util.*;
public class TestCleanup {
    static final List<String> events=new ArrayList<>();
    static class R implements AutoCloseable {
        final String id;final boolean fail;
        R(String id,boolean initFail,boolean closeFail){this.id=id;fail=closeFail;events.add("open:"+id);if(initFail)throw new IllegalStateException("init:"+id);}
        public void close(){events.add("close:"+id);if(fail)throw new IllegalStateException("close:"+id);}
    }
    static RuntimeException scenario(boolean initB,boolean body,boolean closeA,boolean closeB){
        events.clear();try(R a=new R("a",false,closeA);R b=new R("b",initB,closeB)){events.add("body");if(body)throw new IllegalArgumentException("body");}catch(RuntimeException e){return e;}return null;
    }
    static void check(boolean value){if(!value)throw new AssertionError(events.toString());}
    public static void main(String[] args){
        var e=scenario(false,true,true,true);check(e.getMessage().equals("body"));check(Arrays.stream(e.getSuppressed()).map(Throwable::getMessage).toList().equals(List.of("close:b","close:a")));check(events.equals(List.of("open:a","open:b","body","close:b","close:a")));
        e=scenario(false,false,true,true);check(e.getMessage().equals("close:b"));check(e.getSuppressed().length==1&&e.getSuppressed()[0].getMessage().equals("close:a"));
        e=scenario(true,false,true,true);check(e.getMessage().equals("init:b"));check(e.getSuppressed().length==1);check(events.equals(List.of("open:a","open:b","close:a")));
        check(scenario(false,false,false,false)==null);
        e=scenario(false,true,false,false);check(e.getMessage().equals("body")&&e.getSuppressed().length==0);
        events.clear();try(R nothing=null){events.add("body");}check(events.equals(List.of("body")));
        System.out.println("6 cleanup scenarios passed");
    }
}
