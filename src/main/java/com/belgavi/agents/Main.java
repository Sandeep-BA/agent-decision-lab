// Author: Sandeep Belgavi
package com.belgavi.agents;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.*;
import java.util.*;

public final class Main {
    static final ObjectMapper JSON=new ObjectMapper();
    public static List<Engine.Recipe> recipes() throws Exception {
        try(var stream=Main.class.getResourceAsStream("/agents.json")) {
            return Arrays.asList(JSON.readValue(stream,Engine.Recipe[].class));
        }
    }
    public static void main(String[] args) throws Exception {
        var recipes=recipes();
        if(args.length==0 || args[0].equals("--list")) { for(var r:recipes) System.out.println(r.id()+" | "+r.name()); return; }
        String id=args[0]; var recipe=recipes.stream().filter(r->r.id().equals(id)).findFirst().orElseThrow(()->new IllegalArgumentException("Unknown recipe; use --list"));
        boolean live=Arrays.asList(args).contains("--live");
        Map<String,Object> state=new LinkedHashMap<>();
        if(live) {
            int at=Arrays.asList(args).indexOf("--state");
            if(at<0 || at+1>=args.length) throw new IllegalArgumentException("Live mode requires --state path to your approved input JSON");
            var path=Path.of(args[at+1]); if(Files.size(path)>65536) throw new IllegalArgumentException("State too large");
            state=JSON.readValue(Files.readString(path),JSON.getTypeFactory().constructMapType(LinkedHashMap.class,String.class,Object.class));
        } else for(String field:recipe.requiredEvidence()) state.put(field,"Synthetic example for "+recipe.name()+": "+field);
        Engine.Model provider=live ? JevClient.live(System.getenv().getOrDefault("TYPESAFE_MODEL","jev-1.13.0"),System.getenv("TYPESAFE_API_KEY"))
            : (r,s)->new Engine.Decision("proceed",Map.of("proceed",0.95,"review",0.04,"block",0.01),0.925,"fixture-no-inference");
        var context=new Engine.Context(recipe.scope(),1,state,Arrays.asList(args).contains("--approve-recommendation"));
        var result=new Engine().run(recipe,context,provider);
        System.out.println(JSON.writerWithDefaultPrettyPrinter().writeValueAsString(result));
    }
}
