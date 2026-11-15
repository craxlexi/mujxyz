// Browser-local fixtures only; never contacts SLCM or changes production accounts.
const {chromium} = require('../.qa-tools/node_modules/playwright');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const out = path.resolve('design-concepts/theme');
fs.mkdirSync(out, {recursive:true});
const now = Date.now()/1000;
const fixture = {user:{email:'student@example.test',is_admin:true,is_demo:false},account:{semester:3,paused:0,next_check:now+3600,last_check:now-120,last_success:now-120,status:'Monitoring',failures:0},snapshot:{student:{name:'Aanya Sharma'},courses:['Engineering Mathematics III','Data Structures and Algorithms','Digital Systems','Object Oriented Programming','Computer Organization','Communication Skills'].map((name,i)=>({code:`CS${2101+i}`,name,marks:{'MTE 1':String(17+i),'MTE 2':null,CWS:'18','RE-SESSION':null,PRS:null},grade:i%2?'A':null,credits:3})),official_sgpa:null},snapshot_at:now-120,events:[{id:'sample',semester:3,created:now-100,changes:[{course:'CS2101',field:'MTE 1',old:'16',new:'17'}]}],polling:{interval_minutes:60,paused:false,boost_until:0},push:{configured:false,public_key:'',subscriptions:0,delivery:{sent:0,pending:0,failed:0}},portal_verified:true};
let browser;
(async()=>{
  const cache=path.join(process.env.LOCALAPPDATA,'ms-playwright');
  const executablePath=fs.readdirSync(cache).filter(n=>/^chromium-\d+$/.test(n)).sort().reverse().map(n=>path.join(cache,n,'chrome-win64/chrome.exe')).find(p=>fs.existsSync(p));
  browser=await chromium.launch({headless:true,executablePath});
  const context=await browser.newContext({serviceWorkers:'block'});
  let admin=true;
  await context.route('**/api/**',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(route.request().url().endsWith('/dashboard')?{...fixture,user:{...fixture.user,is_admin:admin}}:route.request().url().endsWith('/admin/settings')?{interval_minutes:60,boost_minutes:10,boost_until:0,paused:false,accounts:400}:{})}));
  const page=await context.newPage(),errors=[],contrast=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('response',response=>{if(response.status()>=400)errors.push(`${response.status()} ${response.url()}`);});
  const origin=process.env.QA_ORIGIN||'http://localhost:3400';
  async function ready(){await page.locator('.workspace-theme-toggle').waitFor();await page.waitForTimeout(400);}
  async function capture(name){await page.waitForTimeout(250);await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Viewport overflow: '+name);}
  async function audit(name){await page.addScriptTag({path:require.resolve('../.qa-tools/node_modules/axe-core/axe.min.js')});const result=await page.evaluate(()=>axe.run(document,{runOnly:{type:'rule',values:['color-contrast']}}));contrast.push({name,violations:result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))});}
  for(const width of [1440,1024,768,390]){
    await page.setViewportSize({width,height:width===390?844:1000});
    await page.goto(origin+'/app');await ready();
    if(await page.getByRole('button',{name:'Switch to light mode',exact:true}).count())await page.getByRole('button',{name:'Switch to light mode',exact:true}).click();
    assert.equal(await page.locator('html').getAttribute('data-workspace-theme'),'light');
    assert.equal(await page.locator('.workspace-root').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(248, 248, 247)');
    await capture('light-dashboard-'+width);
    if(width===1440||width===390)await audit('dashboard-'+width);
    await page.goto(origin+'/app?tab=results');await ready();
    assert.equal(await page.locator('html').getAttribute('data-workspace-theme'),'light','Theme must persist after navigation');
    await capture('light-results-'+width);
    if(width===1440||width===390)await audit('results-'+width);
    if(width===390){
      await page.evaluate(()=>scrollTo(0,240));await page.waitForTimeout(700);
      assert.equal(await page.locator('.floating-nav').getAttribute('data-docked'),'true');
      await capture('light-docked-mobile');
      await page.getByRole('button',{name:'Your profile',exact:true}).click();await capture('light-docked-menu-mobile');
      await page.keyboard.press('Escape');await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(700);
    }
    const toggle=page.getByRole('button',{name:'Switch to dark mode',exact:true});
    await toggle.focus();await page.keyboard.press('Space');
    assert.equal(await page.locator('html').getAttribute('data-workspace-theme'),'dark');
    await capture('dark-results-'+width);
    if(width===1440||width===390)await audit('dark-results-'+width);
    await page.reload();await ready();
    assert.equal(await page.locator('html').getAttribute('data-workspace-theme'),'dark');
    await page.getByRole('button',{name:'Switch to light mode',exact:true}).click();
    for(const [tab,name] of [['activity','notifications'],['you','profile'],['admin','admin']]){
      await page.goto(origin+'/app?tab='+tab);await ready();await capture('light-'+name+'-'+width);
      if(width===390)await audit(name+'-'+width);
    }
    await page.getByRole('button',{name:'Your profile',exact:true}).click();await page.waitForTimeout(200);await capture('light-menu-'+width);
    await page.keyboard.press('Escape');
    assert(await page.getByRole('button',{name:'Your profile',exact:true}).evaluate(el=>el===document.activeElement));
    const bounds=await page.locator('.workspace-theme-toggle').boundingBox();assert(bounds.x>=0&&bounds.x+bounds.width<=width&&bounds.width>=44&&bounds.height>=44);
  }
  admin=false;await page.goto(origin+'/app?tab=admin');await ready();
  assert.equal(await page.getByRole('button',{name:'Admin',exact:true}).count(),0);
  assert.equal(await page.locator('.admin-panel').count(),0);
  await page.goto(origin+'/');assert.equal(await page.locator('html').getAttribute('data-workspace-theme'),null);
  const locked=await context.newPage();
  await locked.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage disabled');}}));
  await locked.goto(origin+'/app');
  await locked.getByRole('button',{name:'Switch to light mode',exact:true}).click();
  assert.equal(await locked.locator('html').getAttribute('data-workspace-theme'),'light','Toggle must work when storage is unavailable');
  await locked.close();
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({errors,contrast},null,2));
  assert.equal(errors.length,0,JSON.stringify(errors));
  assert(contrast.every(c=>c.violations.length===0),'Contrast failures: '+JSON.stringify(contrast.filter(c=>c.violations.length)));
  console.log('Theme QA passed: four widths, persistence, keyboard toggle, menus, authorization, contrast, landing isolation.');
  await browser.close();
})().catch(async error=>{console.error(error);await browser?.close();process.exitCode=1;});
