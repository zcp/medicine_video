/**
 * 在 mp-weixin 产物 common/vendor.js 与 app.js 顶部注入控制台补丁。
 * 必须早于 Vue/uni，否则会出现原生的 [] [object Object]。
 *
 * 用法:
 *   node scripts/inject-console-patch.js
 *   node scripts/inject-console-patch.js --watch
 */
const fs = require('fs')
const path = require('path')

const MARKER = '/* __live_saas_console_patch__ */'

const PATCH = `${MARKER}
(function(){try{
  var g=typeof globalThis!=='undefined'?globalThis:typeof wx!=='undefined'?wx:{};
  if(g.__liveSaasConsolePatched)return;
  g.__liveSaasConsolePatched=true;
  function t(v){
    if(v==null)return String(v);
    var ty=typeof v;
    if(ty==='string'||ty==='number'||ty==='boolean')return String(v);
    if(ty==='symbol')return v.toString();
    if(ty==='function')return '[Function]';
    if(v instanceof Error)return v.name+': '+v.message;
    if(Array.isArray(v)){if(!v.length)return'';try{return JSON.stringify(v)}catch(e){return'[Array('+v.length+')]'}}
    try{return JSON.stringify(v)}catch(e){
      try{var ks=Object.keys(v).slice(0,8);return ks.length?'{'+ks.join(',')+'}':''}catch(e2){return''}
    }
  }
  function drop(s){return!s||s==='[object Object]'||/^\\[\\]\\s*(\\[object Object\\])?$/.test(s)}
  ;['log','info','warn','error','debug'].forEach(function(m){
    var o=console[m].bind(console);
    console[m]=function(){
      var a=[].slice.call(arguments).map(t).map(function(x){return String(x).trim()}).filter(Boolean).join(' ');
      if(drop(a))return;
      o(a);
    };
  });
}catch(e){}})();
`

function inject(filePath) {
  if (!fs.existsSync(filePath)) return false
  let code = fs.readFileSync(filePath, 'utf8')
  if (code.includes(MARKER)) return false
  fs.writeFileSync(filePath, PATCH + '\n' + code, 'utf8')
  return true
}

function targets(root) {
  return [
    path.join(root, 'dist/dev/mp-weixin/common/vendor.js'),
    path.join(root, 'dist/dev/mp-weixin/app.js'),
    path.join(root, 'dist/build/mp-weixin/common/vendor.js'),
    path.join(root, 'dist/build/mp-weixin/app.js')
  ]
}

function run(root) {
  let n = 0
  for (const file of targets(root)) {
    if (inject(file)) {
      n += 1
      console.log('[inject-console-patch]', file)
    }
  }
  return n
}

function watch(root) {
  console.log('[inject-console-patch] watching dist mp-weixin outputs...')
  run(root)
  setInterval(() => run(root), 1000)
}

if (require.main === module) {
  const root = path.resolve(__dirname, '..')
  if (process.argv.includes('--watch')) {
    watch(root)
  } else {
    run(root)
  }
}

module.exports = { run, PATCH, MARKER }
