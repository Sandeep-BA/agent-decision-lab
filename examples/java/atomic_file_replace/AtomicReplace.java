// Author: Sandeep Belgavi. Original disposable-directory atomic-move experiment.
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import static java.nio.file.StandardCopyOption.ATOMIC_MOVE;
import static java.nio.file.StandardOpenOption.WRITE;

public final class AtomicReplace {
    interface Mover { void move(Path from, Path to) throws IOException; }
    static void publish(Path target, String value, Mover mover) throws IOException {
        if (!value.matches("generation:[0-9]+\\n")) throw new IllegalArgumentException("invalid complete document");
        Path absolute=target.toAbsolutePath();
        Path temporary=Files.createTempFile(absolute.getParent(), ".config-", ".tmp");
        Throwable failure=null;
        try {
            try(FileChannel ch=FileChannel.open(temporary,WRITE)) {
                ByteBuffer bytes=ByteBuffer.wrap(value.getBytes(StandardCharsets.UTF_8));
                while(bytes.hasRemaining()) ch.write(bytes);
                ch.force(true);
            }
            mover.move(temporary,absolute);
        } catch(IOException|RuntimeException|Error error) {
            failure=error;throw error;
        } finally {
            try { Files.deleteIfExists(temporary); }
            catch(IOException cleanup) { if(failure!=null) failure.addSuppressed(cleanup); else throw cleanup; }
        }
    }
    static final Mover ATOMIC=(from,to)->Files.move(from,to,ATOMIC_MOVE);
    static void check(boolean condition,String label) {if(!condition)throw new AssertionError(label);}
    public static void main(String[] args) throws Exception {
        if(args.length!=1) throw new IllegalArgumentException("Supply a new disposable directory path");
        Path dir=Path.of(args[0]).toAbsolutePath();Files.createDirectory(dir);
        Path target=dir.resolve("configuration.txt");
        publish(target,"generation:0\n",ATOMIC);
        check(Files.readString(target).equals("generation:0\n"),"first publish");
        try {publish(target,"bad",ATOMIC);throw new AssertionError("accepted invalid input");}
        catch(IllegalArgumentException expected) {}
        check(Files.readString(target).equals("generation:0\n"),"invalid input changed old file");
        try {publish(target,"generation:1\n",(a,b)->{throw new AtomicMoveNotSupportedException(a.toString(),b.toString(),"injected");});throw new AssertionError("silent fallback");}
        catch(AtomicMoveNotSupportedException expected) {}
        check(Files.readString(target).equals("generation:0\n"),"failed move changed old file");
        try(var entries=Files.list(dir)){check(entries.count()==1,"temporary file leaked");}
        // Existing-target replacement is provider specific. Refusal is an explicit result.
        try {publish(target,"generation:1\n",ATOMIC);}
        catch(IOException unsupported){System.out.println("Provider refused existing-target atomic replacement: "+unsupported.getClass().getSimpleName());return;}
        AtomicBoolean running=new AtomicBoolean(true);AtomicReference<Throwable> error=new AtomicReference<>();
        Thread reader=new Thread(()->{while(running.get()){try{check(Files.readString(target).matches("generation:[0-9]+\\n"),"partial generation");}catch(Throwable t){error.set(t);return;}}});
        reader.start();
        int completed=0;
        IOException refusal=null;
        try {
            for(int i=2;i<102;i++) {
                try {publish(target,"generation:"+i+"\n",ATOMIC);completed++;}
                catch(IOException failedMove) {refusal=failedMove;break;}
            }
        }
        finally {running.set(false);reader.join();}
        if(error.get()!=null)throw new AssertionError("reader failed",error.get());
        String finalDocument=Files.readString(target);
        check(finalDocument.matches("generation:[0-9]+\\n"),"final document is incomplete");
        try(var entries=Files.list(dir)){check(entries.count()==1,"temporary file leaked after concurrent run");}
        if(refusal==null)check(finalDocument.equals("generation:101\n"),"final generation");
        System.out.println("PASS: input rejection, injected failed move preserves target, cleanup, complete reader observations.");
        System.out.println("Concurrent replacements completed: "+completed+" / 100; result: "+(refusal==null?"SUPPORTED IN THIS RUN":"REFUSED: "+refusal.getClass().getSimpleName()));
        System.out.println("No fallback or retry was attempted. Not a crash-durability test.");
    }
}
