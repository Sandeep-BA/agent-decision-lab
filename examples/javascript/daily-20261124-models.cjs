/* Author: Sandeep Belgavi. Original offline teaching models; no provider calls. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.Daily1124=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  function integer(x,min,max,name){if(!Number.isInteger(x)||x<min||x>max)throw Error(name+' outside '+min+'..'+max);return x;}
  function real(x,min,max,name){if(!Number.isFinite(x)||x<min||x>max)throw Error(name+' outside '+min+'..'+max);return x;}
  function rng(seed){let a=seed>>>0;return function(){a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};}
  function signP(w,l){const n=w+l;if(!n)return 1;let term=2**(-n),sum=term;for(let i=1;i<=Math.min(w,l);i++){term*=((n-i+1)/i);sum+=term;}return Math.min(1,2*sum);}
  function judge(p){
    const pairs=integer(p.pairs,1,200,'pairs'),seed=integer(p.seed,0,4294967295,'seed');
    const bias=real(p.bias,-4,4,'bias'),gap=real(p.gap,0,5,'gap'),share=real(p.share,0,1,'share');
    const random=rng(seed),rows=[];let a=0,b=0,first=0,second=0,single=0;
    for(let i=0;i<pairs;i++){
      const d=random()<share?gap:-gap,pAB=1/(1+Math.exp(-(d+bias))),pBA=1/(1+Math.exp(-(-d+bias)));
      const ab=random()<pAB?'A':'B',ba=random()<pBA?'B':'A';let outcome;
      if(ab===ba){outcome='consistent '+ab;if(ab==='A')a++;else b++;}
      else if(ab==='A'){outcome='first in both';first++;}else{outcome='second in both';second++;}
      if(ab==='A')single++;
      rows.push({pair:i+1,qualityDifference:d,pFirstAB:pAB,pFirstBA:pBA,pickAB:ab,pickBA:ba,outcome});
    }
    return {kind:'judge',inputs:{pairs,bias,gap,share,seed},metrics:{pairs,calls:2*pairs,singleA:single,consistentA:a,consistentB:b,firstBoth:first,secondBoth:second,flips:first+second,signP:signP(a,b)},rows,
      trace:rows.map(r=>`Pair ${r.pair}: assumed A-minus-B quality ${r.qualityDifference}; P(first | A,B)=${r.pFirstAB.toFixed(3)}, P(first | B,A)=${r.pFirstBA.toFixed(3)}. Normalized picks ${r.pickAB}, ${r.pickBA}: ${r.outcome}.`),
      limits:['Synthetic independent draws; not model accuracy or a provider benchmark.','The sign test is conditional on consistent winners; flips are excluded and reported.','No explicit judge ties, refusals or malformed outputs are simulated.']};
  }
  function rollout(p){
    const workers=integer(p.workers,2,8,'workers'),old=integer(p.old,0,workers,'old readers'),sessions=integer(p.sessions,1,6,'sessions'),turns=integer(p.turns,2,24,'turns');
    if(!['mixed','readers_first','rollback'].includes(p.strategy))throw Error('unknown strategy');
    if(typeof p.route!=='boolean')throw Error('route must be boolean');
    const state=Array(sessions).fill('1.22'),rows=[];let rejected=0,completed=0,rerouted=0;
    for(let i=0;i<turns;i++){
      const sid=i%sessions,requested=i%workers;
      let fleet=Array.from({length:workers},(_,j)=>j<old?'old':'new');
      if(p.strategy==='readers_first')fleet.fill('new');
      if(p.strategy==='rollback')fleet.fill(i<Math.max(sessions,workers)?'new':'old');
      const incoming=state[sid];let selected=requested;
      const canRead=j=>fleet[j]==='new'||incoming==='1.22';
      if(p.route&&!canRead(selected)){selected=fleet.findIndex((_,j)=>canRead(j));if(selected>=0)rerouted++;}
      let outcome,output=incoming;
      if(selected<0){outcome='no compatible reader; held';rejected++;}
      else if(!canRead(selected)){outcome='unsupported format; no write';rejected++;}
      else {output=fleet[selected]==='new'?'1.24':'1.22';state[sid]=output;outcome='read and wrote checkpoint';completed++;}
      rows.push({turn:i+1,session:'S'+(sid+1),requested:'W'+(requested+1),selected:selected<0?'none':'W'+(selected+1),reader:selected<0?'none':fleet[selected],incoming,outgoing:output,outcome});
    }
    return {kind:'rollout',inputs:{workers,old,sessions,turns,strategy:p.strategy,route:p.route},metrics:{completed,rejected,rerouted,newCheckpoints:state.filter(f=>f==='1.24').length},rows,
      trace:rows.map(r=>`Turn ${r.turn}, ${r.session}: ${r.requested} requested; selected ${r.selected} (${r.reader}). Read format ${r.incoming}: ${r.outcome}; stored format ${r.outgoing}.`),
      limits:['Compatibility model only; no actual SDK checkpoint is serialized.','Readers-first means all eligible workers upgraded before processing; alpha.2 has no assumed old-format write toggle.','No storage races, approvals, native-process recovery or external effects are modeled.']};
  }
  return {judge,rollout,signP};
});
