// Tiny French Studio - Cloudflare Worker.
// Serves the paste-a-script page and starts/monitors the GitHub Actions render. Secrets: GH_TOKEN, STUDIO_PASSWORD.
const MAX_SCRIPT = 20000;
const MODES = ["check", "render", "post"];
const enc = new TextEncoder();

async function same(a, b) {
  const [x, y] = await Promise.all([crypto.subtle.digest("SHA-256", enc.encode(a)), crypto.subtle.digest("SHA-256", enc.encode(b))]);
  const u = new Uint8Array(x), v = new Uint8Array(y);
  let d = 0;
  for (let i = 0; i < u.length; i++) d |= u[i] ^ v[i];
  return d === 0;
}
const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const gh = (env, path, init = {}) => fetch("https://api.github.com/repos/" + env.GH_OWNER + "/" + env.GH_REPO + path, {
  ...init,
  headers: { Authorization: "Bearer " + env.GH_TOKEN, Accept: "application/vnd.github+json", "User-Agent": "tiny-french-studio", "X-GitHub-Api-Version": "2022-11-28", ...(init.headers || {}) },
});

async function authed(env, body) {
  if (!env.STUDIO_PASSWORD || !env.GH_TOKEN) return json({ error: "The studio is not configured yet: set the STUDIO_PASSWORD and GH_TOKEN secrets." }, 503);
  if (typeof body.password !== "string" || !(await same(body.password, env.STUDIO_PASSWORD))) {
    await new Promise((r) => setTimeout(r, 800));
    return json({ error: "Wrong password." }, 401);
  }
  return null;
}

async function start(env, body) {
  const bad = await authed(env, body);
  if (bad) return bad;
  const script = body.script, mode = body.mode;
  if (typeof script !== "string" || !script.trim()) return json({ error: "The script is empty." }, 422);
  if (script.length > MAX_SCRIPT) return json({ error: "The script is too long (limit " + MAX_SCRIPT + " characters)." }, 422);
  if (!MODES.includes(mode)) return json({ error: "Unknown mode." }, 422);
  const job = Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) => b.toString(16).padStart(2, "0")).join("");
  const r = await gh(env, "/actions/workflows/generate.yml/dispatches", {
    method: "POST",
    body: JSON.stringify({ ref: env.GH_REF || "main", inputs: { job, script, mode } }),
  });
  if (r.status !== 204) {
    const t = await r.text();
    return json({ error: "GitHub refused to start the job (HTTP " + r.status + "). " + t.slice(0, 300) }, 502);
  }
  return json({ job });
}

const WEIGHTS = { check: { render: 1 }, render: { render: 0.85, deploy: 0.15 }, post: { render: 0.7, deploy: 0.1, instagram: 0.2 } };

async function status(env, body) {
  const bad = await authed(env, body);
  if (bad) return bad;
  const job = String(body.job || ""), mode = String(body.mode || "render");
  if (!/^[a-f0-9]{16}$/.test(job)) return json({ error: "Bad job id." }, 422);
  const rr = await gh(env, "/actions/runs?event=workflow_dispatch&per_page=30");
  if (!rr.ok) return json({ error: "Could not read GitHub (HTTP " + rr.status + ")." }, 502);
  const run = ((await rr.json()).workflow_runs || []).find((x) => x.display_title === "Lesson " + job);
  if (!run) return json({ state: "queued", phase: "Waiting for GitHub to start the job", progress: 0.02 });
  const jr = await gh(env, "/actions/runs/" + run.id + "/jobs");
  const jobs = jr.ok ? (await jr.json()).jobs || [] : [];
  const w = WEIGHTS[mode] || WEIGHTS.render;
  let progress = 0, phase = "Starting";
  for (const j of jobs) {
    const wt = w[j.name];
    if (!wt) continue;
    const steps = j.steps || [];
    const done = steps.filter((s) => s.status === "completed").length;
    progress += wt * (j.status === "completed" ? 1 : steps.length ? done / steps.length : 0);
    const cur = steps.find((s) => s.status === "in_progress");
    if (cur) phase = j.name === "instagram" ? "Posting to Instagram: " + cur.name : cur.name;
  }
  const out = { state: run.status === "completed" ? (run.conclusion === "success" ? "done" : "error") : "running", phase, progress: Math.min(0.99, progress), run_url: run.html_url };
  if (out.state === "done") {
    out.progress = 1; out.phase = "Finished";
    if (mode !== "check") out.video_url = "https://" + env.GH_OWNER + ".github.io/" + env.GH_REPO + "/videos/lesson-" + job + ".mp4";
    out.posted = mode === "post" && jobs.some((j) => j.name === "instagram" && j.conclusion === "success");
  }
  if (out.state === "error") {
    const msgs = [];
    for (const j of jobs.filter((x) => x.conclusion === "failure")) {
      const ar = await gh(env, "/check-runs/" + j.id + "/annotations");
      if (ar.ok) for (const a of await ar.json()) if (a.annotation_level === "failure") msgs.push(a.message);
      if (!msgs.length) { const s = (j.steps || []).find((x) => x.conclusion === "failure"); msgs.push("The step '" + (s ? s.name : j.name) + "' failed."); }
    }
    out.error = msgs.join("\n") || "The job failed. Open the run on GitHub for details.";
  }
  return json(out);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    try {
      if (req.method === "GET" && url.pathname === "/") return new Response(PAGE, { headers: { "content-type": "text/html; charset=utf-8" } });
      if (req.method === "GET" && url.pathname === "/api/sample") {
        const r = await fetch("https://raw.githubusercontent.com/" + env.GH_OWNER + "/" + env.GH_REPO + "/" + (env.GH_REF || "main") + "/lessons/03-un-croissant.txt");
        return json({ script: r.ok ? await r.text() : "" });
      }
      if (req.method === "POST" && (url.pathname === "/api/start" || url.pathname === "/api/status")) {
        const raw = await req.text();
        if (raw.length > 90000) return json({ error: "Request too large." }, 413);
        let body;
        try { body = JSON.parse(raw); } catch (e) { return json({ error: "Bad request." }, 400); }
        if (!body || typeof body !== "object") return json({ error: "Bad request." }, 400);
        return url.pathname === "/api/start" ? await start(env, body) : await status(env, body);
      }
      return json({ error: "Not found." }, 404);
    } catch (e) {
      return json({ error: "Unexpected server problem." }, 500);
    }
  },
};

const PAGE = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tiny French Studio</title>
<style>
:root{--navy:#26304a;--lav:#b9a7f5;--blush:#f6b6cd;--sky:#a9d0f5;--cream:#fff5e8;--muted:#606882}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--navy);background:linear-gradient(180deg,var(--sky) 0,var(--cream) 340px,var(--cream))}
main{max-width:820px;margin:0 auto;padding:20px 16px 60px}h1{margin:8px 0 0;font-size:2rem}.tag{margin:0 0 16px;color:var(--muted)}
.card{background:#fffffff0;border-radius:18px;padding:16px;margin-bottom:16px;box-shadow:0 4px 16px #26304a14}
textarea,input[type=password]{width:100%;border:2px solid var(--lav);border-radius:12px;padding:12px;color:var(--navy);background:#fff;font:14px/1.45 ui-monospace,Menlo,Consolas,monospace}
textarea{min-height:320px;resize:vertical}input[type=password]{font-family:inherit;font-size:16px;margin-top:6px}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
button{border:0;border-radius:999px;padding:12px 18px;font:600 15px system-ui,sans-serif;cursor:pointer;background:var(--lav);color:var(--navy)}
button.primary{background:var(--navy);color:#fff}button:disabled{opacity:.5;cursor:not-allowed}
.msg{margin-top:12px;padding:10px 12px;border-radius:10px;white-space:pre-wrap;word-break:break-word;font-size:14px}
.ok{background:#e3f5ea;color:#2f8f5b}.bad{background:#fde6ea;color:#c0394d}.info{background:#eef0fb;color:var(--navy)}
.bar{height:14px;border-radius:999px;background:#e6e0fb;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--lav),var(--blush));transition:width .5s}
video{width:100%;max-width:360px;display:block;margin:12px auto;border-radius:14px;background:#000}
a.dl{display:inline-block;margin:4px 6px 4px 0;padding:8px 14px;border-radius:999px;background:var(--blush);color:var(--navy);text-decoration:none;font-weight:600;font-size:14px}
label{font-size:14px;color:var(--muted)}[hidden]{display:none!important}
</style></head><body><main>
<h1>🥐 Tiny French Studio</h1><p class="tag">Small steps. Big dreams. Paste a lesson, get a Reel with Camille &amp; Julien.</p>
<section class="card"><strong>1. Your lesson script</strong>
<textarea id="script" spellcheck="false" aria-label="Lesson script"></textarea>
<div class="row"><button id="sample">Load sample lesson</button><button id="check">Check script</button></div>
<div style="margin-top:14px"><label for="pw">Studio password</label><input id="pw" type="password" autocomplete="current-password">
<label style="display:block;margin-top:6px"><input type="checkbox" id="remember"> Remember on this device</label></div>
<div class="row"><button id="render">Make video</button><button id="post" class="primary">Make video &amp; post to Instagram</button></div>
<div id="msg" class="msg" hidden></div></section>
<section class="card" id="job" hidden><strong>2. Progress</strong><div id="phase" style="margin-top:6px"></div><div class="bar"><i id="fill"></i></div><div id="jmsg" class="msg" hidden></div></section>
<section class="card" id="result" hidden><strong>3. Done</strong><div id="rmsg" class="msg" hidden></div><video id="player" controls playsinline hidden></video><div id="links"></div></section>
</main><script>
var $=function(i){return document.getElementById(i)};
function show(el,c,t){el.className="msg "+c;el.textContent=t;el.hidden=false}
function api(path,body){return fetch(path,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(d){return{ok:r.ok,d:d}})})}
$("pw").value=localStorage.getItem("tf_pw")||"";$("remember").checked=!!localStorage.getItem("tf_pw");
fetch("/api/sample").then(function(r){return r.json()}).then(function(d){$("script").value=d.script});
$("sample").onclick=function(){fetch("/api/sample").then(function(r){return r.json()}).then(function(d){$("script").value=d.script;$("msg").hidden=true})};
var timer=null,cur=null,t0=0;
function begin(mode){
  if(!$("script").value.trim()){show($("msg"),"bad","Paste a lesson script first.");return}
  if(!$("pw").value){show($("msg"),"bad","Enter the studio password.");return}
  if($("remember").checked)localStorage.setItem("tf_pw",$("pw").value);else localStorage.removeItem("tf_pw");
  setBusy(true);$("msg").hidden=true;$("result").hidden=true;$("job").hidden=false;$("jmsg").hidden=true;$("fill").style.width="2%";$("phase").textContent="Sending to GitHub...";
  api("/api/start",{password:$("pw").value,script:$("script").value,mode:mode}).then(function(x){
    if(!x.ok){setBusy(false);$("job").hidden=true;show($("msg"),"bad",x.d.error||"Could not start.");return}
    cur={job:x.d.job,mode:mode};t0=Date.now();clearInterval(timer);timer=setInterval(poll,5000);poll()})}
function setBusy(b){["check","render","post"].forEach(function(i){$(i).disabled=b})}
function poll(){
  api("/api/status",{password:$("pw").value,job:cur.job,mode:cur.mode}).then(function(x){
    var j=x.d;if(!x.ok){clearInterval(timer);setBusy(false);show($("jmsg"),"bad",j.error||"Status check failed.");return}
    $("fill").style.width=Math.round(j.progress*100)+"%";
    $("phase").textContent=j.phase+" ("+Math.round(j.progress*100)+"%, "+Math.round((Date.now()-t0)/1000)+"s)";
    if(j.state==="error"){clearInterval(timer);setBusy(false);show($("jmsg"),"bad","Failed:\\n"+j.error+(j.run_url?"\\n\\nDetails: "+j.run_url:""))}
    if(j.state==="done"){clearInterval(timer);setBusy(false);finish(j)}
  }).catch(function(){show($("jmsg"),"bad","Lost contact with the studio. Check your connection; the job keeps running on GitHub.")})}
function finish(j){
  $("result").hidden=false;var m=$("rmsg");
  if(cur.mode==="check"){show(m,"ok","Script is valid. You can make the video now.");$("player").hidden=true;$("links").innerHTML="";return}
  show(m,j.posted?"ok":"info",j.posted?"Posted to Instagram (confirmed).":"Video is ready. It was not posted to Instagram.");
  var base=j.video_url.replace(/\\.mp4$/,"");$("player").src=j.video_url;$("player").hidden=false;
  $("links").innerHTML='<a class="dl" href="'+j.video_url+'" download>MP4 video</a><a class="dl" href="'+base+'.srt" download>Subtitles</a><a class="dl" href="'+base+'.caption.txt" target="_blank">Caption</a><a class="dl" href="'+base+'.jpg" target="_blank">Cover</a><a class="dl" href="'+base+'.json" target="_blank">Metadata</a>'}
$("check").onclick=function(){begin("check")};$("render").onclick=function(){begin("render")};
$("post").onclick=function(){if(confirm("Make the video and post it to your Instagram now?"))begin("post")};
</script></body></html>`;
