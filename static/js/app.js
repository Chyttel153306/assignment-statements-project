/* Browser state and API communication. All validation comes from Python. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const names={dashboard:'Dashboard',validator:'Validator',diagram:'DFA Diagram',steps:'Validation Steps',laboratory:'Test Laboratory',help:'Grammar & Help'};
  const state={ready:false,pending:false,labPending:false,result:null,position:0,cases:[],lab:null,accepted:0,rejected:0};
  const visualizer=new window.DFAVisualizer($('dfa-svg'));
  let toastTimer;
  let renderedResult=null, renderedMode='';
  function toast(text){clearTimeout(toastTimer);$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,2800);}
  function node(tag,text,className){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;}
  function badge(text,kind){
    const item=node('span',text,`badge ${kind}`);
    item.tabIndex=0;
    item.setAttribute('role','button');
    item.dataset.tooltip=text==='PASS'?'The actual result matches the expected result.':text==='FAIL'?'The actual result differs from the expected result.':'Run the tests to see the actual results.';
    item.dataset.tooltipTap='';
    return item;
  }
  function excerpt(text){return text.replaceAll('\t','\\t').replaceAll('\n','\\n').replaceAll('\r','\\r').slice(0,180)+(text.length>180?'…':'');}
  function importantStep(step){return !['SPACE','EOF'].includes(step.category)||step.next_state==='DEAD';}
  function shownTrace(){return (state.result?.trace||[]).filter(step=>$('show-trace-details').checked||importantStep(step));}
  function navigate(){
    const page=location.hash.slice(1) || 'validator';
    const chosen=names[page]?page:page==='main'?(document.querySelector('.page:not([hidden])')?.id.slice(5)||'validator'):'validator';
    document.querySelectorAll('.page').forEach(section=>section.hidden=section.id!==`page-${chosen}`);
    document.querySelectorAll('nav a').forEach(link=>{if(link.hash===`#${chosen}`)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
    $('breadcrumb').textContent=names[chosen];document.title=`${names[chosen]} · DFA Studio`;
    closeMenu();
  }
  function closeMenu(){document.querySelector('.sidebar').classList.remove('nav-open');$('menu-toggle').setAttribute('aria-expanded','false');}
  $('menu-toggle').addEventListener('click',()=>{
    const open=document.querySelector('.sidebar').classList.toggle('nav-open');
    $('menu-toggle').setAttribute('aria-expanded',String(open));
    if(!open)window.DFAHelp.close();
  });
  $('workspace-nav').addEventListener('click',event=>{if(event.target.closest('a'))closeMenu();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&document.querySelector('.sidebar').classList.contains('nav-open')){closeMenu();$('menu-toggle').focus();}});
  window.addEventListener('hashchange',()=>{navigate();$('main').focus({preventScroll:true});});navigate();
  async function api(path,body){
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
    try{
      const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});
      const result=await response.json();
      if(!response.ok)throw new Error(result.error||'The server could not complete this request.');
      return result;
    }catch(error){
      if(error.name==='AbortError')throw new Error('The check took too long. Please try again. Your input is still here.');
      if(error instanceof TypeError || error instanceof SyntaxError)throw new Error('We could not reach the local server. Make sure Python is still running, then try again.');
      throw error;
    }finally{clearTimeout(timeout);}
  }
  function controls(){
    const empty=!$('statement').value.trim();
    $('check-button').disabled=!state.ready||state.pending||empty;
    $('clear-input').disabled=state.pending||(!state.result&&!$('statement').value);
    document.querySelectorAll('[data-example]').forEach(button=>button.disabled=!state.ready||state.pending);
    $('run-tests').disabled=!state.ready||state.labPending;
    $('check-button').classList.toggle('is-loading',state.pending);
    $('check-label').textContent=state.pending?'Checking…':'Check Statement';
    $('run-tests').classList.toggle('is-loading',state.labPending);
    $('run-label').textContent=state.labPending?'Running tests…':'Run All Tests';
    $('validator-form').setAttribute('aria-busy',String(state.pending));
    $('result-panel').setAttribute('aria-busy',String(state.pending));
    $('empty-guidance').hidden=!empty;
    const current=state.pending?2:state.result&&state.result.input===$('statement').value?3:empty?1:2;
    [1,2,3].forEach(number=>{
      const step=$(`workflow-${number}`);step.classList.toggle('complete',number<current);
      if(number===current)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');
    });
  }
  function inputChanged(){
    $('char-count').textContent=`${Array.from($('statement').value).length.toLocaleString()} characters`;
    if(!state.result||state.result.input!==$('statement').value)$('statement').removeAttribute('aria-invalid');
    renderResult();controls();
  }
  function loadSource(source){$('statement').value=source;inputChanged();$('request-error').hidden=true;location.hash='validator';$('statement').focus();toast('Statement loaded. Click Check Statement.');}
  $('statement').addEventListener('input',inputChanged);
  $('clear-input').addEventListener('click',()=>{
    if(state.pending)return;
    state.result=null;state.position=0;
    loadSource('');
    $('trace-body').replaceChildren();
    const row=node('tr'),cell=node('td','No steps yet. Check a statement to start.','empty-state');cell.colSpan=7;row.append(cell);$('trace-body').append(row);
    $('diagram-input').textContent='No statement checked yet. You can inspect the machine now.';
    $('trace-input').textContent='Check a statement to see its steps.';
    syncPlayback();toast('Input, result, and highlighted path cleared.');
  });
  document.querySelectorAll('[data-example]').forEach(button=>button.addEventListener('click',()=>{
    const expected=button.dataset.example==='valid';const example=state.cases.find(item=>item.expected===expected);if(example)loadSource(example.source);
  }));
  function renderResult(){
    const result=state.result;
    const stale=!!result&&result.input!==$('statement').value;
    $('stat-accepted').textContent=state.accepted;$('stat-rejected').textContent=state.rejected;
    const mode=state.pending?'pending':!result?'ready':stale?'stale':'checked';
    // Avoid repeating live-region announcements on every editor keystroke.
    if(renderedResult===result&&renderedMode===mode)return;
    renderedResult=result;renderedMode=mode;window.DFAHelp.close();
    $('result-details').hidden=true;$('result-path').hidden=true;$('focus-error').hidden=true;
    $('stale-notice').hidden=!stale;
    if(!result||stale||state.pending){
      $('result-panel').className=`card result-card${stale?' stale':''}`;
      $('result-title').textContent=state.pending?'Checking your statement…':stale?'Ready for another check':'Start with a statement';
      $('result-message').textContent=state.pending?'The validator is reading your input. Your statement will stay in the editor.':'Enter a statement or load an example, then click Check Statement.';
      $('result-badge').className='badge neutral';$('result-badge').textContent=state.pending?'CHECKING':stale?'INPUT CHANGED':'READY';
      $('result-badge').dataset.tooltip='Check the current input to receive an actual validation result.';
      $('result-symbol').textContent=state.pending?'…':'↗';
      return;
    }
    const kind=result.accepted?'success':'error';
    $('result-panel').className=`card result-card ${kind}`;
    $('result-title').textContent=result.accepted?'Valid Statement':'Invalid Statement';
    $('result-badge').className=`badge ${kind}`;$('result-badge').textContent=result.accepted?'ACCEPTED':'REJECTED';
    $('result-badge').dataset.tooltip=result.accepted?'The statement passed the defined syntax and semantic checks.':'The statement did not pass validation. Read the explanation below.';
    $('result-symbol').textContent=result.accepted?'✓':'!';$('result-message').textContent=result.message;
    const details=$('result-details');details.replaceChildren();details.hidden=false;
    details.append(node('div',`Syntax check: ${result.syntax_accepted?'passed':'rejected'} · Final state: ${result.final_state}`));
    details.append(node('div',`Division-by-zero check: ${result.semantic_accepted===null?'not run (fix the syntax first)':result.semantic_accepted?'passed':'rejected'}`));
    if(result.error){
      const location=node('div',`${result.error.type==='semantic'?'Semantic':'Syntax'} error · Character ${result.error.character} · Engine token ${result.error.token_index}`);
      const help=node('button','?','help-tip');help.type='button';help.setAttribute('aria-label','About the error location');help.dataset.tooltip='Where the validator found the problem. Character and token positions start at 1; spaces and the end of input count too.';location.append(help);details.append(location);
      if(result.error.start===result.input.length)details.append(node('div','The error is at the end of your input.'));
      $('focus-error').hidden=false;
    }
    if(result.error&&result.input===$('statement').value)$('statement').setAttribute('aria-invalid','true');
    const chips=$('path-chips');chips.replaceChildren();
    const path=[result.state_path[0],...result.trace.filter(importantStep).map(step=>step.next_state)];
    path.slice(0,9).forEach((id,index)=>{if(index)chips.append(node('span','→','path-separator'));chips.append(node('span',id,'path-chip'));});
    if(path.length>9){const more=node('a',`+ ${path.length-9} states · See all steps`,'path-more');more.href='#steps';chips.append(more);}
    $('result-path').hidden=false;
  }
  $('focus-error').addEventListener('click',()=>{
    const result=state.result;if(!result?.error||result.input!==$('statement').value)return;
    const characters=Array.from(result.input);
    const start=characters.slice(0,result.error.start).join('').length;
    const end=characters.slice(0,result.error.end).join('').length;
    $('statement').focus();$('statement').setSelectionRange(start,end);toast('Cursor moved to the error location.');
  });
  document.querySelectorAll('[data-workflow]').forEach(button=>button.addEventListener('click',()=>{
    if(button.dataset.workflow==='3'){location.hash='diagram';return;}
    if(button.dataset.workflow==='2'&&!$('check-button').disabled){$('validator-form').requestSubmit();return;}
    $('statement').focus();
  }));
  $('validator-form').addEventListener('submit',async event=>{
    event.preventDefault();if(state.pending||!state.ready)return;
    if(!$('statement').value.trim()){$('statement').focus();toast('Enter a statement or load an example first.');return;}
    state.pending=true;controls();renderResult();$('request-error').hidden=true;
    const source=$('statement').value;
    try{
      const result=await api('/api/validate',{statement:source});state.result=result;state.position=result.trace.length;
      if(result.accepted)state.accepted++;else state.rejected++;
      renderTrace();syncPlayback();
    }catch(error){$('request-error').textContent=error.message;$('request-error').hidden=false;}
    finally{state.pending=false;controls();renderResult();}
  });
  document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key==='Enter'){event.preventDefault();if(!$('check-button').disabled)$('validator-form').requestSubmit();else if(!state.pending)$('statement').focus();}});
  function renderTrace(){
    const body=$('trace-body');body.replaceChildren();
    if(!state.result)return;
    const details=$('show-trace-details').checked;
    for(const [index,step] of shownTrace().entries()){
      const row=node('tr');row.dataset.step=step.step;const cell=node('td');const button=node('button',String(index+1),'step-button');
      button.type='button';button.dataset.step=step.step;button.setAttribute('aria-label',`Highlight step ${index+1}`);cell.append(button);row.append(cell);
      const token=!details&&step.category==='INT'?step.token.trim():!details&&step.category==='WORD_GAP'?'(invalid gap)':step.display;
      [token,step.category,step.previous_state,step.transition,step.next_state,step.explanation].forEach(text=>row.append(node('td',text)));
      body.append(row);
    }
    const input=`Last checked: ${excerpt(state.result.input)||'(empty input)'}`;
    const semantic=state.result.syntax_accepted&&!state.result.accepted?' · Syntax passed. Division by zero was rejected separately.':'';
    $('diagram-input').textContent=input+semantic;$('trace-input').textContent=input+semantic;
  }
  function syncPlayback(){
    const trace=state.result?.trace||[],steps=shownTrace();
    if(!$('show-trace-details').checked&&state.position){
      state.position=steps.filter(step=>step.step<=state.position).at(-1)?.step||0;
    }
    const position=state.position;
    const displayPosition=steps.filter(step=>step.step<=position).length;
    visualizer.setExecution(trace,position);
    $('full-path').disabled=!trace.length;$('highlight-step').disabled=!position;
    $('reset-trace').disabled=!position;$('reset-diagram').disabled=!position;
    document.querySelectorAll('[data-move]').forEach(button=>button.disabled=Number(button.dataset.move)<0?position===0:displayPosition>=steps.length);
    $('step-progress').textContent=`${displayPosition} / ${steps.length} steps`;
    const current=position?trace[position-1].next_state:visualizer.model?.initial_state||'A';
    $('diagram-step-status').textContent=`${position?'Step '+displayPosition+' of '+steps.length:'Start state'} · ${current}`;
    $('step-explanation').textContent=position?`${trace[position-1].transition}\n${trace[position-1].explanation}`:`The machine starts in ${current}. No input has been read yet.`;
    $('trace-body').querySelectorAll('tr[data-step]').forEach(row=>{
      const selected=Number(row.dataset.step)===position;row.classList.toggle('current-step',selected);
      const button=row.querySelector('button');if(selected)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');
    });
  }
  document.querySelectorAll('[data-move]').forEach(button=>button.addEventListener('click',()=>{
    const steps=shownTrace();
    state.position=Number(button.dataset.move)>0?steps.find(step=>step.step>state.position)?.step||state.position:
      steps.filter(step=>step.step<state.position).at(-1)?.step||0;
    syncPlayback();
  }));
  $('show-trace-details').addEventListener('change',()=>{if(state.result)renderTrace();syncPlayback();});
  $('trace-body').addEventListener('click',event=>{const button=event.target.closest('button[data-step]');if(button){state.position=Number(button.dataset.step);syncPlayback();}});
  function reset(){state.position=0;syncPlayback();toast('Playback reset to the start state.');}
  $('reset-diagram').addEventListener('click',reset);$('reset-trace').addEventListener('click',reset);
  $('full-path').addEventListener('click',()=>{state.position=state.result?.trace.length||0;syncPlayback();});
  $('highlight-step').addEventListener('click',()=>{
    const row=$('trace-body').querySelector(`tr[data-step="${state.position}"]`);if(row){row.scrollIntoView({block:'center',inline:'nearest'});row.querySelector('button').focus({preventScroll:true});}
  });
  $('fit-diagram').addEventListener('click',()=>$('zoom-label').textContent=visualizer.fit());
  for(const [id,amount] of [['zoom-out',-1],['zoom-in',1]])$(id).addEventListener('click',()=>$('zoom-label').textContent=visualizer.changeZoom(amount));
  $('show-rejections').addEventListener('change',()=>{visualizer.allRejections=$('show-rejections').checked;visualizer.render();});
  for(const [id,mode] of [['view-input-path','input'],['view-full-dfa','full']])$(id).addEventListener('click',()=>{
    window.DFAHelp.close();visualizer.setMode(mode);
    $('view-input-path').setAttribute('aria-pressed',String(mode==='input'));
    $('view-full-dfa').setAttribute('aria-pressed',String(mode==='full'));
    $('show-rejections').disabled=mode==='input';
    $('diagram-view-help').textContent=mode==='input'?'Follow the arrows in order. Longer statements create longer paths using the same A–H states.':'The complete machine. Loops reuse states; visited arrows show the input read so far.';
    $('zoom-label').textContent='Fit';
  });
  $('show-rejections').disabled=true;
  $('path-part-prev').addEventListener('click',()=>visualizer.changePart(-1));
  $('path-part-next').addEventListener('click',()=>visualizer.changePart(1));
  function renderLab(){
    const body=$('lab-body');body.replaceChildren();
    const filter=$('lab-filter').value,query=$('lab-search').value.toLowerCase();
    const cases=state.lab?.cases||state.cases;
    const filtered=cases.filter(item=>{
      if(filter==='Valid'&&!item.expected||filter==='Invalid'&&item.expected||filter==='Passed'&&item.passed!==true||filter==='Failed'&&item.passed!==false)return false;
      return (item.source+' '+item.purpose).toLowerCase().includes(query);
    });
    for(const item of filtered){
      const row=node('tr'),description=node('td');
      description.append(node('code',excerpt(item.source)||'(empty input)','lab-statement'),node('span',item.purpose,'lab-purpose'));
      if(item.passed===false)description.append(node('span',`Expected ${item.expected?'acceptance':'rejection'} but got ${item.actual?'acceptance':'rejection'}. ${item.message}`,'lab-failure'));
      row.append(description,node('td',item.expected?'Valid':'Invalid'),node('td',item.actual===undefined?'—':item.actual?'Valid':'Invalid'));
      const status=node('td');status.append(badge(item.passed===undefined?'NOT RUN':item.passed?'PASS':'FAIL',item.passed===undefined?'neutral':item.passed?'success':'error'));row.append(status);
      const action=node('td'),load=node('button','Load →','button small');load.type='button';load.dataset.case=item.id;load.setAttribute('aria-label',`Load test case ${item.id+1} into Validator`);action.append(load);row.append(action);body.append(row);
      load.dataset.tooltip='Load this test statement into the Validator so you can inspect its path.';
    }
    if(!filtered.length){const row=node('tr'),cell=node('td','No cases match this filter.','empty-state');cell.colSpan=5;row.append(cell);body.append(row);}
    $('lab-total').textContent=cases.length;$('lab-passed').textContent=state.lab?.passed||0;$('lab-failed').textContent=state.lab?.failed||0;
    $('lab-not-run').textContent=state.lab?'All cases checked':`${cases.length} not run yet`;
    $('lab-visible').textContent=`Showing ${filtered.length} of ${cases.length} cases`;
  }
  $('lab-search').addEventListener('input',renderLab);$('lab-filter').addEventListener('change',renderLab);
  $('lab-body').addEventListener('click',event=>{const button=event.target.closest('button[data-case]');if(button){const item=state.cases.find(item=>item.id===Number(button.dataset.case));if(item)loadSource(item.source);}});
  $('run-tests').addEventListener('click',async()=>{
    if(state.labPending||!state.ready)return;state.labPending=true;controls();$('lab-error').hidden=true;
    try{state.lab=await api('/api/test-cases/run',{});renderLab();$('stat-tests').textContent=state.lab.passed;toast(`${state.lab.passed} of ${state.lab.total} tests passed.`);}
    catch(error){$('lab-error').textContent=error.message;$('lab-error').hidden=false;}
    finally{state.labPending=false;controls();}
  });
  function renderHelp(model){
    const descriptions=$('state-descriptions');descriptions.replaceChildren();
    model.states.forEach(state=>{const row=node('div',undefined,'state-item');row.append(node('code',state.id),node('p',state.description));descriptions.append(row);});
    const table=$('transition-table'),head=table.querySelector('thead'),body=table.querySelector('tbody');head.replaceChildren();body.replaceChildren();
    const header=node('tr');['State',...model.alphabet].forEach(text=>{const th=node('th',text);th.scope='col';header.append(th);});head.append(header);
    const moves=new Map(model.transitions.map(edge=>[`${edge.from}|${edge.symbol}`,edge.to]));
    model.states.forEach(state=>{const row=node('tr');const th=node('th',state.id);th.scope='row';row.append(th);model.alphabet.forEach(symbol=>row.append(node('td',moves.get(`${state.id}|${symbol}`))));body.append(row);});
  }
  function renderExamples(){
    const container=$('dashboard-examples');container.replaceChildren();
    const examples=[state.cases.find(item=>item.expected),state.cases.find(item=>item.purpose.includes('All arithmetic')),state.cases.find(item=>!item.expected)];
    examples.filter(Boolean).forEach(item=>{const row=node('div',undefined,'example-item');const code=node('div');code.append(node('code',item.source),node('small',item.expected?'Valid example':'Invalid example',`lab-purpose ${item.expected?'success-text':'error-text'}`));const button=node('button','Try →','text-button');button.type='button';button.addEventListener('click',()=>loadSource(item.source));row.append(code,button);container.append(row);});
    const help=$('help-examples');help.replaceChildren();
    [true,false].forEach(expected=>{
      const column=node('div',undefined,'example-list');column.append(node('h3',expected?'Valid examples':'Invalid examples',expected?'success-text':'error-text'));
      state.cases.filter(item=>item.expected===expected).slice(0,3).forEach(item=>{
        const row=node('div',undefined,'example-item'),code=node('code',item.source),button=node('button','Try →','text-button');button.type='button';
        button.setAttribute('aria-label',`Load example: ${item.source}`);button.addEventListener('click',()=>loadSource(item.source));row.append(code,button);column.append(row);
      });help.append(column);
    });
  }
  document.querySelectorAll('[data-scroll-target]').forEach(button=>button.addEventListener('click',()=>{
    const target=$(button.dataset.scrollTarget);target.scrollIntoView({block:'start'});target.focus({preventScroll:true});
  }));
  async function initialize(){
    $('retry-connection').disabled=true;
    try{
      const [health,model,examples]=await Promise.all([api('/api/health'),api('/api/dfa'),api('/api/examples')]);
      if(health.status!=='ok')throw new Error('The local server is not ready. Please try again.');
      state.ready=true;state.cases=examples.cases;visualizer.load(model);renderHelp(model);renderExamples();renderLab();syncPlayback();
      $('zoom-label').textContent=visualizer.zoom?`${Math.round(visualizer.zoom/visualizer.width*100)}%`:'Fit';
      $('connection').classList.remove('offline');$('connection').replaceChildren(node('span',undefined,'status-dot'),document.createTextNode('Local server connected'));
      $('connection-error').hidden=true;
    }catch(error){state.ready=false;$('connection-error').hidden=false;$('connection-error-text').textContent=error.message;$('connection').classList.add('offline');$('connection').textContent='Server unavailable';}
    finally{$('retry-connection').disabled=false;controls();}
  }
  $('retry-connection').addEventListener('click',initialize);inputChanged();syncPlayback();initialize();
})();
