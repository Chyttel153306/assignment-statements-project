/* A readable view of the backend DFA. Formatting moves are not drawn. */
(() => {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const FORMATTING = new Set(['SPACE', 'EOF']);
  const LABELS = {INT:'int', LETTER:'letter', UNDERSCORE:'_', DIGIT:'digit',
    OPERATOR:'+ - * /', '=':'=', ';':';'};
  function element(tag, attrs = {}, text) {
    const item = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([key, value]) => item.setAttribute(key, value));
    if (text !== undefined) item.textContent = text;
    return item;
  }
  function inputText(step) {
    if(step.category==='EOF')return '(end)';
    if(step.category==='SPACE'||step.category==='WORD_GAP')return '(gap)';
    return step.category==='INT'?step.token.trim():step.display;
  }
  function setLabel(text,lines,x,y) {
    text.replaceChildren();text.setAttribute('y',y-(lines.length-1)*11);
    lines.forEach((line,index)=>text.append(element('tspan',{x,dy:index?22:0},line)));
  }
  class DFAVisualizer {
    constructor(svg) {
      this.svg=svg; this.model=null; this.trace=[]; this.position=0;
      this.allRejections=false; this.zoom=0; this.nodes=[]; this.edges=[];
      this.width=1420;
      this.mode='input';this.part=0;this.partSize=24;
    }
    load(model) {
      this.model=model;
      this.svg.classList.add('diagram-simple');
      this.svg.querySelectorAll('g,defs').forEach(item=>item.remove());
      this.nodes=[];this.edges=[];
      const defs=element('defs');
      for(const [name,color] of [['neutral','#748aa7'],['visited','#85dfb0'],['rejected','#ffa0ac'],['start','#91baff']]) {
        const marker=element('marker',{id:`arrow-${name}`,viewBox:'0 0 10 10',refX:9,refY:5,
          markerWidth:7,markerHeight:7,orient:'auto-start-reverse'});
        marker.append(element('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:color}));defs.append(marker);
      }
      this.svg.append(defs);
      const ordinary=model.states.filter(state=>!state.dead);
      const spacing=(this.width-180)/Math.max(ordinary.length-1,1);
      const positions=new Map(ordinary.map((state,index)=>[state.id,{x:90+index*spacing,y:185}]));
      model.states.filter(state=>state.dead).forEach(state=>positions.set(state.id,{x:710,y:420}));
      const edgesGroup=element('g',{'aria-label':'Meaningful transitions'});
      for(const edge of model.edges) {
        const reject=edge.to===model.dead_state;
        const symbols=edge.symbols.filter(symbol=>!FORMATTING.has(symbol));
        if(!symbols.length)continue; // No SPACE/EOF loops or labels in this view.
        const start=positions.get(edge.from),end=positions.get(edge.to);
        const exact=`${edge.from} → ${edge.to}: ${reject?'invalid input':symbols.map(s=>LABELS[s]||s).join(', ')}`;
        const group=element('g',{class:`edge${reject?' reject':''}`,tabindex:0,role:'button',
          'data-from':edge.from,'data-to':edge.to,'aria-label':exact,'data-tooltip':exact,'data-tooltip-tap':''});
        let d,tx,ty;
        if(edge.from===edge.to) {
          d=`M ${start.x-22} ${start.y-25} C ${start.x-86} ${start.y-119}, ${start.x+86} ${start.y-119}, ${start.x+22} ${start.y-25}`;
          tx=start.x;ty=start.y-124;
        } else if(!reject&&end.x<start.x) {
          // The arithmetic return goes below the straight left-to-right flow.
          d=`M ${start.x-22} ${start.y+26} C ${start.x-50} ${start.y+135}, ${end.x+50} ${end.y+135}, ${end.x+22} ${end.y+26}`;
          tx=(start.x+end.x)/2;ty=start.y+126;
        } else {
          const dx=end.x-start.x,dy=end.y-start.y,distance=Math.hypot(dx,dy);
          const sx=start.x+34*dx/distance,sy=start.y+34*dy/distance;
          const ex=end.x-38*dx/distance,ey=end.y-38*dy/distance;
          d=`M ${sx} ${sy} L ${ex} ${ey}`;
          tx=reject?sx*.25+ex*.75:(sx+ex)/2;
          ty=reject?sy*.25+ey*.75:(sy+ey)/2-18;
        }
        const path=element('path',{d,'marker-end':'url(#arrow-neutral)'});
        const words=reject?['invalid']:symbols.map(symbol=>LABELS[symbol]||symbol);
        const lines=[];
        words.forEach(word=>{
          const last=lines.length-1;
          if(last>=0&&(lines[last]+' / '+word).length<=16)lines[last]+=' / '+word;
          else lines.push(word);
        });
        const text=element('text',{x:tx,y:ty});
        setLabel(text,lines,tx,ty);
        group.append(path,text);edgesGroup.append(group);
        this.edges.push({edge,symbols,group,path,reject,text,x:tx,y:ty,baseLines:lines,baseHelp:exact,
          labelLimit:edge.from===edge.to||end.x<start.x?16:10});
      }
      this.svg.append(edgesGroup);
      const start=positions.get(model.initial_state),incoming=element('g');
      incoming.append(element('path',{class:'start-arrow',d:`M 15 ${start.y} L ${start.x-39} ${start.y}`,'marker-end':'url(#arrow-start)'}));
      this.svg.append(incoming);
      const nodesGroup=element('g',{'aria-label':'States'});
      for(const state of model.states) {
        const pos=positions.get(state.id);
        const description=`${state.id}: ${state.description}${state.accepting?'. Syntax acceptance requires completed input; semantic checks are separate.':''}`;
        const group=element('g',{class:`node${state.dead?' dead':''}`,'data-state':state.id,tabindex:0,role:'button',
          'aria-label':description,'data-tooltip':description,'data-tooltip-tap':''});
        group.append(element('circle',{class:'state-circle',cx:pos.x,cy:pos.y,r:34}));
        if(state.accepting)group.append(element('circle',{class:'state-circle',cx:pos.x,cy:pos.y,r:27}));
        group.append(element('text',{class:'node-label',x:pos.x,y:pos.y},state.id));
        const caption=state.dead?'Rejected':state.accepting?'Accept':state.id===model.initial_state?'Start':'';
        if(caption)group.append(element('text',{class:'node-caption',x:pos.x,y:pos.y+62},caption));
        nodesGroup.append(group);this.nodes.push({state,group});
      }
      this.svg.append(nodesGroup);
      this.fit();this.render();
    }
    setExecution(trace,position=trace.length){
      if(this.trace!==trace||this.position!==position)this.part=null;
      this.trace=trace;this.position=position;this.render();
    }
    setMode(mode){this.mode=mode;if(this.model)this.load(this.model);}
    changePart(delta){this.part=(this.part||0)+delta;this.render();}
    renderInputPath(){
      this.svg.querySelectorAll('g').forEach(item=>item.remove());
      const moves=this.trace.filter(step=>!FORMATTING.has(step.category)||step.next_state===this.model.dead_state);
      const reached=moves.filter(step=>step.step<=this.position).length;
      const parts=Math.max(1,Math.ceil(moves.length/this.partSize));
      if(this.part===null)this.part=Math.max(0,Math.ceil(reached/this.partSize)-1);
      this.part=Math.max(0,Math.min(parts-1,this.part));
      const offset=this.part*this.partSize,shown=moves.slice(offset,offset+this.partSize);
      const states=[offset?moves[offset-1].next_state:this.model.initial_state,...shown.map(step=>step.next_state)];
      const columns=6,width=1240;
      const point=index=>{const row=Math.floor(index/columns),col=index%columns;return {x:100+(row%2?columns-1-col:col)*208,y:100+row*170};};
      this.svg.setAttribute('viewBox',`0 0 ${width} ${Math.ceil(states.length/columns)*170+35}`);
      const group=element('g',{'aria-label':'Your input path'});
      shown.forEach((step,index)=>{
        const a=point(index),b=point(index+1),dx=b.x-a.x,dy=b.y-a.y,length=Math.hypot(dx,dy);
        const active=step.step<=this.position,rejected=step.next_state===this.model.dead_state;
        const actual=inputText(step),help=`Step ${offset+index+1}: ${step.previous_state} → ${step.next_state} · Read: ${actual}`;
        const edge=element('g',{class:`edge${active?(rejected?' rejected':' visited'):''}`,
          'data-from':step.previous_state,'data-to':step.next_state,'data-step':step.step,
          'data-inputs':JSON.stringify([actual]),tabindex:0,role:'button','aria-label':help,'data-tooltip':help,'data-tooltip-tap':''});
        edge.append(element('path',{d:`M ${a.x+35*dx/length} ${a.y+35*dy/length} L ${b.x-39*dx/length} ${b.y-39*dy/length}`,
          'marker-end':`url(#arrow-${active?(rejected?'rejected':'visited'):'neutral'})`}));
        edge.append(element('text',{x:(a.x+b.x)/2+(dy?58:0),y:(a.y+b.y)/2-(dy?0:18)},actual.length>16?actual.slice(0,15)+'…':actual));
        group.append(edge);
      });
      states.forEach((id,index)=>{
        const state=this.model.states.find(item=>item.id===id),pos=point(index),number=offset+index;
        const current=number===reached,visited=number<=reached;
        const help=`${id} · Path position ${number}. ${state.description}`;
        const item=element('g',{class:`node${state.dead?' dead':''}${visited?' visited':''}${current?' current':''}`,
          'data-state':id,'data-path-index':number,tabindex:0,role:'button','aria-label':help,'data-tooltip':help,'data-tooltip-tap':''});
        if(current)item.setAttribute('aria-current','true');
        item.append(element('circle',{class:'state-circle',cx:pos.x,cy:pos.y,r:34}));
        if(state.accepting)item.append(element('circle',{class:'state-circle',cx:pos.x,cy:pos.y,r:27}));
        item.append(element('text',{class:'node-label',x:pos.x,y:pos.y},id));
        const caption=number===0?'Start':state.dead?'Rejected':state.accepting?'Syntax final':`Move ${number}`;
        item.append(element('text',{class:'node-caption',x:pos.x,y:pos.y+61},caption));group.append(item);
      });
      const start=point(0);
      group.append(element('path',{class:'start-arrow',d:`M 20 ${start.y} L ${start.x-39} ${start.y}`,'marker-end':'url(#arrow-start)'}));
      this.svg.append(group);
      document.getElementById('path-part-status').textContent=moves.length?`Moves ${offset+1}–${offset+shown.length} of ${moves.length} · Read rows in arrow order`:'Check a statement to see your input path.';
      document.getElementById('path-part-prev').disabled=this.part===0;
      document.getElementById('path-part-next').disabled=this.part>=parts-1;
    }
    render(){
      if(!this.model)return;
      document.getElementById('path-parts').hidden=this.mode!=='input';
      if(this.mode==='input'){this.renderInputPath();return;}
      const prefix=this.trace.slice(0,this.position);
      // An actual rejection is always important, including missing input/gaps.
      const meaningful=prefix.filter(step=>!FORMATTING.has(step.category)||step.next_state===this.model.dead_state);
      const current=prefix.length?prefix[prefix.length-1].next_state:this.model.initial_state;
      const visited=new Set([this.model.initial_state,...meaningful.map(step=>step.next_state)]);
      const showDead=this.allRejections||visited.has(this.model.dead_state);
      this.svg.setAttribute('viewBox',`0 0 ${this.width} ${showDead?510:340}`);
      for(const {state,group} of this.nodes){
        group.style.display=state.dead&&!showDead?'none':'';
        group.classList.toggle('visited',visited.has(state.id));group.classList.toggle('current',state.id===current);
        if(state.id===current)group.setAttribute('aria-current','true');else group.removeAttribute('aria-current');
      }
      const reads=new Map();
      meaningful.forEach(step=>{
        const key=`${step.previous_state}|${step.next_state}`;
        if(!reads.has(key))reads.set(key,[]);
        reads.get(key).push(inputText(step));
      });
      for(const {edge,group,path,reject,text,x,y,baseLines,baseHelp,labelLimit} of this.edges){
        const inputs=reads.get(`${edge.from}|${edge.to}`)||[];
        const active=inputs.length>0;
        group.style.display=reject&&!this.allRejections&&!active?'none':'';
        group.classList.toggle('visited',active&&!reject);group.classList.toggle('rejected',active&&reject);
        path.setAttribute('marker-end',`url(#arrow-${active?(reject?'rejected':'visited'):'neutral'})`);
        if(active){
          // Preserve order and repeated values: every value came from this edge's
          // real executed trace, not from the transition's generic category.
          const actual=inputs.join(', ');
          setLabel(text,[actual.length>labelLimit?actual.slice(0,labelLimit-1)+'…':actual],x,y);
          group.setAttribute('data-inputs',JSON.stringify(inputs));
          const help=`${edge.from} → ${edge.to} · Read: ${actual.length>500?actual.slice(0,500)+'…':actual}`;
          group.setAttribute('data-tooltip',help);group.setAttribute('aria-label',help);
        }else{
          setLabel(text,baseLines,x,y);group.removeAttribute('data-inputs');
          group.setAttribute('data-tooltip',baseHelp);group.setAttribute('aria-label',baseHelp);
        }
      }
    }
    fit(){this.zoom=0;this.svg.style.width='100%';this.svg.parentElement.scrollTo(0,0);return 'Fit';}
    changeZoom(amount){
      const base=this.zoom||Math.max(850,this.svg.parentElement.clientWidth||0);
      this.zoom=Math.min(2600,Math.max(850,base+amount*180));this.svg.style.width=`${this.zoom}px`;
      return `${Math.round(this.zoom/this.width*100)}%`;
    }
  }
  window.DFAVisualizer=DFAVisualizer;
})();
