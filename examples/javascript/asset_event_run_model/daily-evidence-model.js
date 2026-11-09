/* Author: Sandeep Belgavi. Original synthetic models; no network calls. */
(function (scope) {
  'use strict';
  const bounded=(v,min,max,integer=false)=>{
    if(!Number.isFinite(v)||v<min||v>max||(integer&&!Number.isInteger(v))) throw new RangeError(`Expected ${integer?'integer ':''}${min} to ${max}`);
    return v;
  };
  function binomialTail(losses,discordant){
    bounded(discordant,0,5000,true); bounded(losses,0,discordant,true);
    if(discordant===0||losses===0)return 1;
    const f=[0];for(let i=1;i<=discordant;i++)f[i]=f[i-1]+Math.log(i);
    let sum=0;for(let k=losses;k<=discordant;k++)sum+=Math.exp(f[discordant]-f[k]-f[discordant-k]-discordant*Math.LN2);
    return Math.min(1,Math.max(0,sum));
  }
  function normalCdf(x){
    // Polynomial approximation; numerical model, not an exact-power calculation.
    const z=Math.abs(x),t=1/(1+.2316419*z);
    const tail=Math.exp(-z*z/2)/Math.sqrt(2*Math.PI)*t*(.319381530+t*(-.356563782+t*(1.781477937+t*(-1.821255978+t*1.330274429))));
    return x>=0?1-tail:tail;
  }
  function evalgate(input){
    const n=bounded(Number(input.n),20,5000,true),q=bounded(Number(input.q),.01,.8),d=bounded(Number(input.d),0,.2),alpha=Number(input.alpha);
    if(d>q)throw new RangeError('Degradation cannot exceed disagreement probability.');
    const z=({'.01':2.326347874,'.05':1.644853627,'.1':1.281551566})[String(alpha).replace(/^0/,'')];
    if(z===undefined)throw new RangeError('Choose a supported significance level.');
    const discordant=Math.round(n*q),losses=Math.min(discordant,Math.round(n*(q+d)/2)),wins=discordant-losses,agreement=n-discordant;
    const p=binomialTail(losses,discordant),power=normalCdf(d*Math.sqrt(n/q)-z),required=d===0?null:Math.ceil((z+.841621234)**2*q/(d*d));
    const trace=[
      `Plan ${n} independent paired cases, disagreement ${q}, and true degradation ${d}. These are assumptions.`,
      `Construct a deterministic rounded fixture: ${losses} losses, ${wins} wins, ${agreement} agreements. This is not a random sample.`,
      `Condition on ${discordant} disagreements. Under equal directions, losses follow Binomial(${discordant}, 0.5).`,
      `Sum the upper tail from ${losses} losses: p=${p.toPrecision(5)}. Compare with preselected alpha=${alpha}.`,
      `Fixture decision: ${p<alpha?'detect degradation':'do not detect degradation'}. Non-rejection does not establish noninferiority.`,
      `Normal planning approximation gives ${(power*100).toFixed(1)}% power and ${required===null?'no finite sample target for zero effect':required+' pairs for approximately 80% power'}. Exact discrete power is not computed.`
    ];
    return {kind:'evalgate',inputs:{n,q,d,alpha},losses,wins,agreement,discordant,p,power,required,detected:p<alpha,observedDrop:(losses-wins)/n,warning:n*q<30?'Fewer than 30 expected disagreements: the normal planning approximation may be poor.':'Independent pairs and a frozen test are assumed.',trace};
  }
  function assetevents(input){
    const count=bounded(Number(input.count),1,40,true),spacing=bounded(Number(input.spacing),0,5,true),period=bounded(Number(input.period),1,10,true),duration=bounded(Number(input.duration),1,20,true),slots=bounded(Number(input.slots),1,8,true),mode=input.mode;
    if(!['per-event','batch'].includes(mode))throw new RangeError('Unknown grouping policy.');
    const events=Array.from({length:count},(_,i)=>({id:'E'+(i+1),arrival:i*spacing}));
    const groups=[];
    for(const event of events){
      const eligible=Math.ceil(event.arrival/period)*period;
      let group=mode==='batch'?groups.find(g=>g.eligible===eligible):null;
      if(!group){group={id:'R'+(groups.length+1),eligible,events:[]};groups.push(group);}
      group.events.push(event.id);
    }
    const available=Array(slots).fill(0),timeline=events.map(e=>({at:e.arrival,order:0,text:`t=${e.arrival}: ${e.id} arrives.`}));
    const runs=groups.map(group=>{
      const slot=available.indexOf(Math.min(...available)),start=Math.max(group.eligible,available[slot]),end=start+duration;
      available[slot]=end;
      timeline.push({at:group.eligible,order:1,text:`t=${group.eligible}: ${group.id} becomes eligible with [${group.events.join(', ')}].`});
      timeline.push({at:start,order:3,text:`t=${start}: ${group.id} starts in slot ${slot+1}; queue wait ${start-group.eligible}.`});
      timeline.push({at:end,order:2,text:`t=${end}: ${group.id} finishes; slot ${slot+1} is available.`});
      return {...group,slot:slot+1,start,end,wait:start-group.eligible};
    });
    timeline.sort((a,b)=>a.at-b.at||a.order-b.order);
    return {kind:'assetevents',inputs:{count,spacing,period,duration,slots,mode},events,runs,covered:runs.reduce((n,r)=>n+r.events.length,0),finish:Math.max(...runs.map(r=>r.end)),maxWait:Math.max(...runs.map(r=>r.wait)),trace:timeline.map(t=>t.text),warning:'Fixed run duration ignores batch size. This is a queue model, not the Airflow scheduler.'};
  }
  const api={binomialTail,normalCdf,evalgate,assetevents};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  scope.DailyEvidenceModel=api;
})(typeof globalThis!=='undefined'?globalThis:this);
