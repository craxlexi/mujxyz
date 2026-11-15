// Production-only visual regression review. All API responses are synthetic and browser-local.
// Run from frontend after `npm run build` and `npm start -- -p 4400`.
const {createRequire} = require('node:module');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const req = createRequire(path.resolve('package.json'));
const {chromium} = req('playwright');
const out = path.resolve('../design-concepts', process.argv[3] || 'phase2', process.argv[2] || 'pass1');
fs.mkdirSync(out, {recursive:true});
const now = Math.floor(Date.now()/1000);
const fixture = {
  user:{email:'student@example.test',is_admin:true,is_demo:false},
  account:{semester:3,paused:0,next_check:now+3600,last_check:now-120,last_success:now-120,status:'Connected',failures:0},
  snapshot:{courses:['Engineering Mathematics III','Data Structures and Algorithms','Digital Systems','Object Oriented Programming','Computer Organization','Communication Skills'].map((name,i)=>({code:`CS${2101+i}`,name,marks:{'MTE 1':String(17+i),'MTE 2':null,CWS:'18','RE-SESSION':null,PRS:null},grade:null,credits:3})),official_sgpa:null,attendance:null,timetable:null},
  snapshot_at:now-120,events:[{id:'sample-change',semester:3,created:now-1800,changes:[{course:'Engineering Mathematics III',field:'MTE 1',old:null,new:'17'}]}],
  polling:{interval_minutes:60,paused:false,boost_until:0},push:{configured:false,public_key:'',subscriptions:0,delivery:{sent:0,pending:0,failed:0}},portal_verified:true,
};

(async()=>{
  const cache=path.join(process.env.LOCALAPPDATA || '', 'ms-playwright');
  const cached=fs.existsSync(cache) ? fs.readdirSync(cache).filter(n=>/^chromium-\d+$/.test(n)).sort().reverse().map(n=>path.join(cache,n,'chrome-win64/chrome.exe')).find(p=>fs.existsSync(p)) : undefined;
  const executablePath=process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || cached;
  const browser = await chromium.launch({headless:true,...(executablePath?{executablePath}:{})});
  const context = await browser.newContext();
  await context.addInitScript(()=>{
    localStorage.setItem('mujheky-theme-choice','light');
    window.__vitals={lcp:0,cls:0,shifts:[]};
    new PerformanceObserver(list=>{for(const entry of list.getEntries())window.__vitals.lcp=entry.startTime;}).observe({type:'largest-contentful-paint',buffered:true});
    new PerformanceObserver(list=>{for(const entry of list.getEntries())if(!entry.hadRecentInput){window.__vitals.cls+=entry.value;window.__vitals.shifts.push({value:entry.value,sources:entry.sources.map(s=>({node:s.node?.className,previous:s.previousRect.toJSON(),current:s.currentRect.toJSON()}))});}}).observe({type:'layout-shift',buffered:true});
  });
  const page = await context.newPage();
  const errors=[],expectedConsole=[],requests=[],checks=[],frames=[],homeAxe=[],hoverEvidence=[],axeCoverage=[];
  let signedIn=true, admin=true, scenario='full';
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',msg=>{if(msg.type()==='error') {
    if(!signedIn && msg.text().includes('401 (Unauthorized)')) expectedConsole.push(msg.text());
    else errors.push(msg.text());
  }});
  await page.route('**/api/**',async route=>{
    const request=route.request(); const url=new URL(request.url());
    requests.push({path:url.pathname,method:request.method(),body:request.postData()});
    if(url.pathname==='/api/dashboard') {
      let snapshot=fixture.snapshot;
      if(['mte2','resession','zero','zero-resession','pending'].includes(scenario)) snapshot={...snapshot,courses:snapshot.courses.map((course,i)=>({...course,marks:scenario==='pending'?{'MTE 1':null,'MTE 2':null,CWS:null,'RE-SESSION':null,PRS:null}:scenario==='zero-resession'?{'MTE 1':null,'MTE 2':null,CWS:null,'RE-SESSION':'0',PRS:null}:scenario==='resession'?{'MTE 1':null,'MTE 2':null,CWS:'18','RE-SESSION':'32',PRS:null}:{...course.marks,'MTE 2':i===0?(scenario==='zero'?'0':'10.5'):null}}))};
      return route.fulfill({status:signedIn?200:401,json:signedIn?{...fixture,snapshot,...(scenario==='unconnected'?{account:null,snapshot:null,events:[]}:scenario==='paused'?{account:{...fixture.account,paused:1}}:{}),user:{...fixture.user,is_admin:admin}}:{detail:'Please sign in'}});
    }
    if(url.pathname==='/api/auth/logout') signedIn=false;
    if(url.pathname.startsWith('/api/auth/') && request.method()==='POST' && !url.pathname.endsWith('/logout')) signedIn=true;
    if(url.pathname==='/api/admin/settings') return route.fulfill({json:{interval_minutes:60,boost_minutes:10,boost_until:0,paused:false}});
    return route.fulfill({json:{}});
  });
  const check=(name,value)=>{assert.ok(value,name);checks.push(name);};
  async function scanAxe(label){
    if(!await page.evaluate(()=>!!window.axe))await page.addScriptTag({path:req.resolve('axe-core/axe.min.js')});
    homeAxe.push(...await page.evaluate(async label=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({page:label,id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));},label));
    axeCoverage.push(label);
  }
  const nav=label=>page.locator((page.viewportSize().width<=700?'.mobile-bottom-nav':'.workspace-nav')+' button').filter({hasText:new RegExp('^'+label+'$')});
  async function snap(name,fullPage=false){
    await page.evaluate(()=>document.fonts.ready); await page.waitForTimeout(440);
    const metrics=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth,background:getComputedStyle(document.querySelector('.workspace-root')).backgroundColor,mainCount:document.querySelectorAll('main').length,h1Count:document.querySelectorAll('h1').length,smallTargets:[...document.querySelectorAll('button,a,input,select')].filter(el=>{const target=el.matches('input[type=checkbox]')?el.closest('label')||el:el;const r=target.getBoundingClientRect();return r.width&&r.height&&(r.width<24||r.height<24);}).map(el=>el.textContent||el.getAttribute('aria-label'))}));
    check(name+` has no page overflow (${metrics.scroll}/${metrics.width})`,metrics.scroll<=metrics.width && metrics.body<=metrics.width);
    check(name+' stays pitch black despite light landing preference',metrics.background==='rgb(0, 0, 0)');
    check(name+' has one main and heading',metrics.mainCount===1&&metrics.h1Count===1);
    check(name+' controls meet 24px minimum: '+JSON.stringify(metrics.smallTargets),metrics.smallTargets.length===0);
    await page.screenshot({path:path.join(out,name+'.png'),fullPage});
    frames.push({name,...metrics});
  }
  for(const width of [390,1440,1024,768]){
    await page.setViewportSize({width,height:width===390?844:1000});
    await page.goto('http://127.0.0.1:4400/app?keep=1');
    await page.locator('.workspace-profile-trigger').waitFor();
    await snap(`${width}-home`); if(width===390||width===1440)await scanAxe(`${width} Home`);
    check(`${width} Home uses one marks table`,await page.locator('.marks-table').count()===1&&await page.locator('.marks-table tbody tr').count()===6);
    check(`${width} Total sums published marks`,await page.locator('.marks-total strong').first().innerText()==='35.00');
    check(`${width} empty optional columns stay hidden`,await page.getByRole('columnheader',{name:'MTE 2',exact:true}).count()===0&&await page.getByRole('columnheader',{name:'Re-session',exact:true}).count()===0);
    check(`${width} campus keeps original color`,await page.locator('.semester-campus img').evaluate(el=>getComputedStyle(el).filter)==='none');
    check(`${width} official SGPA stays unpublished`,await page.locator('.semester-unpublished').isVisible());
    if(width===1440){
      await page.addScriptTag({path:req.resolve('axe-core/axe.min.js')});
      homeAxe.push(...await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}));}));
      await page.locator('.marks-course-link').first().focus();
      check('Course link has keyboard focus',await page.locator('.marks-course-link').first().evaluate(el=>el===document.activeElement));
      await snap('1440-table-focus');
      await page.locator('.marks-course-link').first().hover(); await snap('1440-table-hover');
      await page.mouse.move(1400,950); await page.locator('.workspace-profile-trigger').focus();
    }
    await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight)); await snap(`${width}-home-end`);
    check(`${width} main nav Home selected`,await nav('Home').getAttribute('aria-current')==='page');
    await nav('Results').click();
    check(`${width} tab query preserved`,new URL(page.url()).searchParams.get('tab')==='results'&&new URL(page.url()).searchParams.get('keep')==='1');
    await snap(`${width}-results`); if(width===390||width===1440)await scanAxe(`${width} Results`);
    check(`${width} Results is table-only`,await page.locator('.marks-switch').count()===0&&await page.locator('.marks-table').count()===1);
    check(`${width} six marks table rows`,await page.locator('.marks-table tbody tr').count()===6);
    await snap(`${width}-table`);
    if(width===390){
      await page.locator('.marks-table-scroll').evaluate(el=>{el.scrollLeft=el.scrollWidth;});
      check('Mobile table scroll stays internal',await page.locator('.marks-table-scroll').evaluate(el=>el.scrollLeft>0));
      check('Frozen course column leaves room for marks',await page.locator('.marks-table tbody th').first().evaluate(el=>{const r=el.getBoundingClientRect();return r.x>=19&&r.width<=180;}));
      await snap('390-table-scrolled');
    }
    if(width>800){
      await page.getByRole('button',{name:'Collapse results sidebar'}).click();
      check(`${width} sidebar collapsed`,await page.locator('.workspace-root').evaluate(el=>el.classList.contains('context-collapsed')));
      if(width===1440) await snap('1440-collapsed');
      await page.getByRole('button',{name:'Expand results sidebar'}).click();
      await page.getByRole('button',{name:'Attendance',exact:true}).click();
    } else await page.getByLabel('Results',{exact:true}).selectOption('attendance');
    check(`${width} honest attendance empty state`,await page.getByText('Attendance is unavailable from SLCM right now. Saved marks are unaffected.').isVisible());
    await snap(`${width}-attendance`);
    if(width>800) await page.getByRole('button',{name:'Timetable',exact:true}).click();
    else await page.getByLabel('Results',{exact:true}).selectOption('timetable');
    check(`${width} timetable wired`,await page.getByText('Timetable is unavailable from SLCM right now.').isVisible());
    await nav('Activity').click(); await snap(`${width}-activity`); if(width===390||width===1440)await scanAxe(`${width} Activity`);
    await nav('You').click(); await snap(`${width}-account`); if(width===390||width===1440)await scanAxe(`${width} Account`);
    if(width===390){
      await page.getByRole('button',{name:'Permanently delete my account'}).scrollIntoViewIfNeeded();
      await snap('390-account-end');
      check('Mobile last action clears bottom nav',await page.getByRole('button',{name:'Permanently delete my account'}).evaluate(el=>el.getBoundingClientRect().bottom<document.querySelector('.mobile-bottom-nav').getBoundingClientRect().top));
      check('Mobile header remains sticky',await page.locator('.workspace-header').evaluate(el=>el.getBoundingClientRect().top===0));
    }
    await nav('Admin').click(); await snap(`${width}-admin`); if(width===390||width===1440)await scanAxe(`${width} Admin`);
    await page.goBack(); await page.waitForTimeout(440); check(`${width} Back restores account`,await nav('You').getAttribute('aria-current')==='page');
    await page.goForward(); await page.waitForTimeout(440); check(`${width} Forward restores admin`,await nav('Admin').getAttribute('aria-current')==='page');
    await page.getByRole('button',{name:'Your profile',exact:true}).click();
    check(`${width} profile first action focused`,await page.getByRole('button',{name:'Account settings'}).evaluate(el=>el===document.activeElement));
    await snap(`${width}-profile`);
    await page.keyboard.press('Escape');
    check(`${width} Escape restores profile trigger`,await page.getByRole('button',{name:'Your profile',exact:true}).evaluate(el=>el===document.activeElement));
    await page.getByRole('button',{name:'Your profile',exact:true}).click();
    await page.mouse.click(5,350); check(`${width} outside click closes profile`,await page.locator('#workspace-profile-panel').count()===0);
  }
  // Focus, reduced motion, hover and polling on the same production app.
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:4400/app?tab=results');
  await page.locator('.workspace-profile-trigger').waitFor();
  await page.keyboard.press('Tab');
  check('Skip link first focus stop',await page.locator('.workspace-skip').evaluate(el=>el===document.activeElement));
  await snap('1440-keyboard-skip'); await page.keyboard.press('Enter');
  check('Skip link lands on main',await page.locator('main').evaluate(el=>el===document.activeElement));
  await nav('Activity').focus(); await snap('1440-keyboard-nav');
  await page.getByRole('button',{name:'Your profile',exact:true}).focus(); await page.keyboard.press('Enter');
  await snap('1440-keyboard-profile'); await page.keyboard.press('Escape');
  await page.mouse.move(1400,950); await snap('1440-hover-rest');
  await nav('Activity').hover(); await snap('1440-hover-active');
  await page.emulateMedia({reducedMotion:'reduce'}); await snap('1440-reduced-motion');
  const moving=await page.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length);
  check('Reduced motion has no running animations',moving===0);
  const pollingBefore=requests.filter(r=>r.path==='/api/dashboard').length;
  await page.waitForTimeout(10200);
  check('Ten second dashboard polling preserved',requests.filter(r=>r.path==='/api/dashboard').length>pollingBefore);
  await page.addScriptTag({path:req.resolve('axe-core/axe.min.js')});
  const resultsAxe=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));});
  const axe=[...homeAxe,...resultsAxe];
  fs.writeFileSync(path.join(out,'axe.json'),JSON.stringify(axe,null,2));
  await page.getByRole('button',{name:'Collapse results sidebar'}).focus();
  await page.keyboard.press('Enter'); await page.getByRole('button',{name:'Attendance',exact:true}).focus();
  await snap('1440-keyboard-collapsed'); await page.keyboard.press('Enter');
  check('Collapsed rail keyboard selects Attendance',await page.getByRole('heading',{name:'Attendance',exact:true}).isVisible());
  await page.setViewportSize({width:768,height:1000});
  await page.getByLabel('Results',{exact:true}).selectOption('marks');
  await page.getByLabel('Results',{exact:true}).focus(); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter');
  check('Native selector keyboard selects Attendance',await page.getByLabel('Results',{exact:true}).inputValue()==='attendance');
  await snap('768-keyboard-selector');
  await page.setViewportSize({width:390,height:844}); await nav('Activity').focus();
  await snap('390-keyboard-navigation'); await page.keyboard.press('Enter');
  check('Mobile keyboard navigation selects Activity',await nav('Activity').getAttribute('aria-current')==='page');
  // Primary interaction roles: clipped rest/hover pairs and measured style changes.
  async function hoverPair(name, locator){
    await locator.scrollIntoViewIfNeeded(); await page.mouse.move(1,950); await page.waitForTimeout(250);
    const state=()=>locator.evaluate(el=>{const s=getComputedStyle(el);return {background:s.backgroundColor,color:s.color,border:s.borderColor,transform:s.transform,before:getComputedStyle(el,'::before').opacity,icons:[...el.querySelectorAll('svg')].map(n=>getComputedStyle(n).transform)};});
    const rest=await state(); await locator.screenshot({path:path.join(out,`hover-${name}-rest.png`)});
    await locator.hover(); await page.waitForTimeout(300); const hovered=await state();
    await locator.screenshot({path:path.join(out,`hover-${name}-active.png`)});
    check(`${name} hover responds`,JSON.stringify(rest)!==JSON.stringify(hovered)); hoverEvidence.push({name,rest,hovered});
  }
  await page.emulateMedia({reducedMotion:'no-preference'}); await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:4400/app'); await page.locator('.workspace-profile-trigger').waitFor();
  await hoverPair('global-nav',nav('Activity')); await hoverPair('record-link',page.getByRole('button',{name:'Open academic record',exact:true}));
  await hoverPair('refresh',page.getByRole('button',{name:'Refresh view',exact:true}));
  await hoverPair('profile',page.getByRole('button',{name:'Your profile',exact:true}));
  await hoverPair('course',page.locator('.marks-course-link').first());
  await page.mouse.move(1,950); await nav('Results').click();
  await page.screenshot({path:path.join(out,'transition-results-early.png')}); await page.waitForTimeout(100);
  await page.screenshot({path:path.join(out,'transition-results-mid.png')}); await page.waitForTimeout(250);
  await page.screenshot({path:path.join(out,'transition-results-settled.png')});
  await hoverPair('context-nav',page.getByRole('button',{name:'Attendance',exact:true}));
  await hoverPair('collapse',page.getByRole('button',{name:'Collapse results sidebar'}));
  await page.emulateMedia({reducedMotion:'reduce'});
  // One separate throttled synthetic mobile load; local figures are not field CWV.
  const cdp=await context.newCDPSession(page);
  await page.setViewportSize({width:390,height:844});
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});
  await cdp.send('Network.emulateNetworkConditions',{offline:false,downloadThroughput:200000,uploadThroughput:93750,latency:150});
  await page.goto('http://127.0.0.1:4400/app');
  await page.locator('.workspace-profile-trigger').waitFor(); await page.waitForTimeout(4000);
  const mobileVitals=await page.evaluate(()=>window.__vitals);
  const mobileResources=await page.evaluate(()=>performance.getEntriesByType('resource').map(r=>({path:new URL(r.name).pathname,type:r.initiatorType,encodedBytes:r.encodedBodySize,transferBytes:r.transferSize,durationMs:r.duration})));
  const mobileScrollFps=await page.evaluate(()=>new Promise(resolve=>{let previous;const times=[];const startY=scrollY;function frame(t){if(previous!==undefined)times.push(t-previous);previous=t;window.scrollTo(0,Math.min(document.documentElement.scrollHeight-innerHeight,times.length*10));if(times.length<60)requestAnimationFrame(frame);else{window.scrollTo(0,startY);resolve(1000/(times.reduce((a,b)=>a+b,0)/times.length));}}requestAnimationFrame(frame);}));
  await snap('390-throttled');
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});
  await cdp.send('Network.emulateNetworkConditions',{offline:false,downloadThroughput:-1,uploadThroughput:-1,latency:0});
  await cdp.detach(); await page.setViewportSize({width:1440,height:1000});
  await page.setViewportSize({width:1440,height:1000});
  for(const sample of ['mte2','resession','zero','zero-resession','pending']){
    scenario=sample; await page.goto('http://127.0.0.1:4400/app?tab=results'); await page.locator('.marks-table').waitFor();
    if(sample==='zero-resession'){
      check('Zero Re-session mark still exposes its column',await page.getByRole('columnheader',{name:'Re-session',exact:true}).count()===1);
      check('A real zero total stays zero, not Pending',await page.locator('.marks-total strong').first().innerText()==='0.00');
    }else if(sample==='pending'){
      check('Missing marks do not become a zero total',await page.locator('.marks-total .marks-pending').count()===6);
    }else if(sample==='resession'){
      check('Re-session column appears when present',await page.getByRole('columnheader',{name:'Re-session',exact:true}).count()===1);
      check('Re-session-only record has no empty MTE columns',await page.getByRole('columnheader',{name:'MTE 1',exact:true}).count()===0&&await page.getByRole('columnheader',{name:'MTE 2',exact:true}).count()===0);
      check('Re-session total uses session plus coursework',await page.locator('.marks-total strong').first().innerText()==='50.00');
    }else{
      check(`${sample} MTE 2 column is visible`,await page.getByRole('columnheader',{name:'MTE 2',exact:true}).count()===1);
      check(`${sample} total is correct`,await page.locator('.marks-total strong').first().innerText()===(sample==='zero'?'35.00':'45.50'));
    }
    await snap(`1440-${sample}-marks`);
  }
  scenario='full';
  scenario='unconnected'; await page.goto('http://127.0.0.1:4400/app'); await page.locator('.workspace-profile-trigger').waitFor();
  check('Unconnected dashboard shows no invented academic data',await page.locator('.marks-table').count()===0 && await page.getByText('Your courses belong here.').isVisible());
  await page.setViewportSize({width:390,height:844}); await snap('390-unconnected');
  scenario='paused'; await page.goto('http://127.0.0.1:4400/app'); await page.locator('.workspace-profile-trigger').waitFor();
  check('Paused monitoring is explicit',await page.locator('.semester-monitor-state').innerText()==='Monitoring paused');
  await snap('390-paused'); scenario='full'; await page.setViewportSize({width:1440,height:1000});
  // Frontend authorization and existing account controls. Requests are intercepted, no real account touched.
  admin=false; await page.goto('http://127.0.0.1:4400/app?tab=admin'); await page.locator('.workspace-profile-trigger').waitFor();
  await page.waitForFunction(()=>!new URL(location.href).searchParams.has('tab'));
  check('Non-admin URL falls back to Home',await nav('Home').getAttribute('aria-current')==='page');
  check('Non-admin sees no Admin destination',await page.getByRole('button',{name:'Admin',exact:true}).count()===0);
  await nav('You').click();
  await page.getByRole('button',{name:'Pause monitoring',exact:true}).click();
  check('Pause uses existing account PATCH',requests.some(r=>r.path==='/api/account'&&r.method==='PATCH'&&JSON.parse(r.body).paused===true));
  await page.getByRole('button',{name:'Reconnect SLCM',exact:false}).click();
  check('Existing connect dialog reachable',await page.getByRole('dialog').isVisible());
  await snap('1440-connect-dialog'); await scanAxe('Connect dialog'); await page.getByRole('button',{name:'Close dialog'}).click();
  await page.getByRole('button',{name:'Your profile',exact:true}).click();
  await page.locator('#workspace-profile-panel').getByRole('button',{name:'Sign out',exact:true}).click();
  await page.locator('.signin-screen').waitFor();
  check('Profile sign-out POST preserved',requests.some(r=>r.path==='/api/auth/logout'&&r.method==='POST'));
  await snap('1440-signed-out');
  await page.goto('http://127.0.0.1:4400/app?auth=register');
  await page.getByRole('dialog').waitFor(); await scanAxe('Registration dialog'); check('Signup query still opens registration',await page.getByRole('button',{name:'Create account',exact:true}).count()>0);
  await page.getByRole('button',{name:'Close dialog'}).click();
  await page.goto('http://127.0.0.1:4400/'); await page.locator('.landing-wordmark').waitFor();
  check('Landing theme choice untouched',await page.evaluate(()=>localStorage.getItem('mujheky-theme-choice'))==='light');
  check('Public landing remains public',await page.locator('.landing-hero').count()===1&&await page.locator('.workspace-header').count()===0);
  await page.screenshot({path:path.join(out,'1440-landing-light.png')});
  await page.setViewportSize({width:390,height:844}); await page.screenshot({path:path.join(out,'390-landing-light.png')});
  const screenshotCount=fs.readdirSync(out).filter(n=>n.endsWith('.png')&&!n.includes('contact')).length;
  const finalAxe=[...homeAxe,...resultsAxe]; fs.writeFileSync(path.join(out,'axe.json'),JSON.stringify(finalAxe,null,2));
  const report={checks,errors,expectedConsole,frames,screenshotCount,axe:finalAxe,axeCoverage,hoverEvidence,mobileVitals,mobileResources,mobileScrollFps,requests,synthetic:true,production:true};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({checks:checks.length,errors,expectedConsole,axe:finalAxe.map(v=>({id:v.id,impact:v.impact})),mobileVitals,mobileScrollFps,screenshots:screenshotCount,out},null,2));
  await browser.close();
  if(errors.length || finalAxe.some(v=>['critical','serious'].includes(v.impact))) process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1);});
