import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const directory = dirname(fileURLToPath(import.meta.url));
const defaultInput = resolve(directory, "../evals/results.jsonl");
const input = resolve(process.argv[2] ?? defaultInput);
const output = join(directory, "dashboard.html");

function invalid(row, line, message) {
  throw new Error(`Invalid result row ${line}: ${message}`);
}

function validate(row, line) {
  if (!row || typeof row !== "object" || Array.isArray(row)) invalid(row, line, "expected an object");
  if (typeof row.date !== "string" || !Number.isFinite(Date.parse(row.date))) invalid(row, line, "date must be an ISO date or timestamp");
  if (typeof row.week !== "string" || !/^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$/.test(row.week)) invalid(row, line, "week must be YYYY-Www");
  if (!(["baseline", "eval"].includes(row.kind))) invalid(row, line, "kind must be baseline or eval");
  if (!(typeof row.tested === "string" && row.tested.trim())) invalid(row, line, "tested must be a non-empty string");
  if (typeof row.control_only !== "boolean") invalid(row, line, "control_only must be a boolean");
  if (!( ["baseline", "shipped", "rejected"].includes(row.verdict))) invalid(row, line, "verdict must be baseline, shipped, or rejected");
  if ((row.kind === "baseline") !== (row.verdict === "baseline")) invalid(row, line, "baseline kind and verdict must match");
  if (!Array.isArray(row.targets) || row.targets.some(n => !Number.isInteger(n) || n < 1 || n > 7) || new Set(row.targets).size !== row.targets.length) invalid(row, line, "targets must be unique behavior numbers 1–7");
  if (!row.scores || typeof row.scores !== "object" || Array.isArray(row.scores)) invalid(row, line, "scores must map behaviors 1–7 to scores or null");
  if (!row.trust || typeof row.trust !== "object" || Array.isArray(row.trust)) invalid(row, line, "trust must map behaviors 1–7 to a trust state");
  for (let behavior = 1; behavior <= 7; behavior++) {
    const score = row.scores[behavior];
    const state = row.trust[behavior];
    if (!(score === null || (typeof score === "number" && Number.isFinite(score) && score >= 0 && score <= 100))) invalid(row, line, `scores.${behavior} must be 0–100 or null`);
    if (!( ["ok", "not-trusted", "not-measured", "not-evaluable"].includes(state))) invalid(row, line, `trust.${behavior} must be ok, not-trusted, not-measured, or not-evaluable`);
    if (state === "ok" && score === null) invalid(row, line, `scores.${behavior} cannot be null when trust is ok`);
    if ((state === "not-measured" || state === "not-evaluable") && score !== null) invalid(row, line, `scores.${behavior} must be null when trust is ${state}`);
  }
  if (!row.deltas || typeof row.deltas !== "object" || Array.isArray(row.deltas)) invalid(row, line, "deltas must map targeted behaviors to points or null");
  for (const target of row.targets) {
    const delta = row.deltas[target];
    if (!(delta === null || (typeof delta === "number" && Number.isFinite(delta)))) invalid(row, line, `deltas.${target} must be points or null`);
  }
  if (typeof row.report !== "string" || !row.report.trim()) invalid(row, line, "report must be a repository-relative path");
  const reportPath = row.report.split("#", 1)[0];
  if (reportPath.startsWith("/") || /^[a-z][a-z\d+.-]*:/i.test(reportPath) || reportPath.split(/[\\/]/).includes("..")) invalid(row, line, "report must stay inside the repository");
  if (typeof row.skill_commit !== "string" || !row.skill_commit.trim()) invalid(row, line, "skill_commit must be a non-empty string");
}

const exists = existsSync(input);
if (!exists && input !== defaultInput) throw new Error(`Results file not found: ${input}`);
const rows = exists
  ? readFileSync(input, "utf8").split(/\r?\n/).filter(line => line.trim()).map((line, index) => {
      let row;
      try { row = JSON.parse(line); }
      catch (error) { throw new Error(`Invalid JSON on result row ${index + 1}: ${error.message}`); }
      validate(row, index + 1);
      return row;
    })
  : [];

const data = JSON.stringify(rows).replaceAll("<", "\\u003c");
const fixture = relative(directory, input).split(sep)[0] === "fixture";
const source = relative(directory, input).split(sep).join("/") || basename(input);
const fixtureNotice = fixture ? '<p class="notice" role="note">Sample fixture · illustrative scores only; this is not a real evaluation.</p>' : "";

const html = `<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hivecall · Weekly improvement</title>
<style>
:root{color:#242424;background:#fff;font:15px/1.5 Inter,system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0}main{max-width:1240px;margin:auto;padding:56px 32px}header{margin-bottom:36px}.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#666}h1,h2{font-family:"Cal Sans",Inter,system-ui,sans-serif;font-weight:600;line-height:1.1}h1{font-size:42px;margin:12px 0}h2{font-size:24px;margin:0 0 8px}p{color:#646464;max-width:850px}.panel{background:#fff;border-radius:12px;padding:24px;margin-top:28px;box-shadow:0 1px 5px -4px rgba(19,19,22,.7),0 0 0 1px rgba(34,42,53,.08),0 4px 8px rgba(34,42,53,.05)}.notice{display:inline-block;margin:8px 0 0;padding:7px 11px;border-radius:7px;background:#f5f5f5;color:#242424;font-size:13px}.chart-wrap,.table-wrap{overflow:auto}.chart{display:block;width:100%;min-width:900px;height:auto;margin-top:12px}.note{font-size:13px}.key{display:flex;gap:20px;flex-wrap:wrap;color:#646464;font-size:13px;margin-top:10px}.key span{display:inline-flex;align-items:center;gap:7px}.key i{display:inline-block;width:12px;height:12px;border:2px solid #242424;border-radius:50%;background:#fff}.key b{font-size:17px;line-height:1}.key b.unscored{display:inline-flex;align-items:center;justify-content:center;width:21px;height:15px;border:1px solid #7a4b00;border-radius:3px;background:#fff4d6;color:#7a4b00;font-size:8px}table{width:100%;border-collapse:collapse;text-align:left;font-size:14px}th,td{padding:13px 12px;vertical-align:top;box-shadow:0 1px rgba(34,42,53,.1)}th{color:#646464;font-weight:500;white-space:nowrap}td:first-child{white-space:nowrap}a{color:#0969a2;text-decoration:underline;text-underline-offset:2px}td a{display:inline-block;white-space:nowrap}.verdict{display:inline-block;padding:2px 8px;border-radius:999px;background:#f1f1f1;color:#242424;font-size:12px;white-space:nowrap}.verdict.shipped{background:#e8f1eb}.verdict.rejected{background:#f4eded}.empty{fill:#646464;font-size:14px}footer{margin-top:32px;color:#646464;font-size:13px}@media(max-width:640px){main{padding:32px 18px}h1{font-size:34px}.panel{padding:18px}}
</style>
<main>
<header><div class="eyebrow">Retro / Hivecall</div><h1>Weekly improvement</h1><p>Track all seven behaviors week by week. Solid points are trusted; hollow points are scored but not trusted; NT marks a not-trusted result with no score; a gap means the behavior was not measured or not evaluable. Ship markers show weeks with a shipped change.</p>${fixtureNotice}</header>
<section class="panel"><h2>Behavior trends</h2><p class="note">Scores use a 0–100 scale. Each lane shares the same scale. Partial (filtered) runs stay in the table but do not count toward trends. If a week has multiple full rows, the chart shows the latest; the table keeps every result.</p><div class="chart-wrap"><svg id="chart" class="chart" role="img" aria-label="Weekly score trend for seven behaviors"></svg></div><div class="key"><span><i aria-hidden="true"></i> Not trusted score</span><span><b class="unscored" aria-hidden="true">NT</b> Not trusted (no score)</span><span><b aria-hidden="true">—</b> Not measured or not evaluable (no point; line breaks)</span><span><b aria-hidden="true">◆</b> A change shipped</span></div></section>
<section class="panel"><h2>Evaluation history</h2><div class="table-wrap"><table><thead><tr><th>Date / week</th><th>What was tested</th><th>Verdict</th><th>Score change on targets</th><th>Report</th></tr></thead><tbody id="history"></tbody></table></div></section>
<footer>Source: <code>${source.replaceAll("&", "&amp;").replaceAll("<", "&lt;")}</code> · Generated offline with Node.js; no network requests.</footer>
</main>
<script>
const rows = ${data};
const names = ["Finish or park every item with a reason","Every tick has proof","Never quiet while work is open","Parallel work without clashes","Watchdog: real alerts, no missed stalls","Clear tasks and clean reports","Reasonable time and cost"];
const $ = id => document.getElementById(id);
function svg(tag, attrs, text) { const node=document.createElementNS("http://www.w3.org/2000/svg",tag); for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value); if(text!==undefined)node.textContent=text; return node; }
function draw() {
  const chart=$("chart"), trendRows=rows.filter(row=>!row.control_only), weeks=[...new Set(trendRows.map(row=>row.week))].sort();
  const left=350, right=80, top=40, lane=62, width=Math.max(1000,left+right+Math.max(1,weeks.length-1)*145), height=top+lane*7+38;
  chart.replaceChildren(); chart.setAttribute("viewBox","0 0 "+width+" "+height); chart.setAttribute("aria-label",weeks.length?"Seven behavior trends across "+weeks.length+" weeks. Ship markers indicate shipped changes; hollow points are not-trusted scores; NT markers mean not trusted with no score; gaps are not measured or not evaluable.":"No weekly results yet");
  if(!rows.length){chart.append(svg("text",{x:width/2,y:150,"text-anchor":"middle",class:"empty"},"No results yet. The weekly eval will appear here."));$("history").replaceChildren();return;}
  if(!trendRows.length){chart.append(svg("text",{x:width/2,y:150,"text-anchor":"middle",class:"empty"},"No full evaluation results yet."));}
  else {
  const weekly=weeks.map(week=>{const records=trendRows.filter(row=>row.week===week).sort((a,b)=>Date.parse(a.date)-Date.parse(b.date));return {week,latest:records.at(-1),shipped:records.some(row=>row.verdict==="shipped")};});
  const plotRight=width-right, plotWidth=plotRight-left;
  const xAt=index=>weeks.length===1?left+plotWidth/2:left+plotWidth*index/(weeks.length-1);
  weekly.forEach((item,index)=>{if(item.shipped){const x=xAt(index);chart.append(svg("line",{x1:x,x2:x,y1:top-9,y2:top+lane*7-7,stroke:"#242424","stroke-width":1,"stroke-dasharray":"4 5",opacity:.55}),svg("path",{d:"M "+x+" "+(top-14)+" l 5 5 -5 5 -5 -5 Z",fill:"#242424"}),svg("text",{x,y:top-19,"text-anchor":"middle",fill:"#242424","font-size":10,"font-weight":600},"SHIP"));}});
  for(let behavior=1;behavior<=7;behavior++){
    const rowTop=top+(behavior-1)*lane, scoreY=score=>rowTop+47-(score/100)*35;
    chart.append(svg("text",{x:8,y:rowTop+31,fill:"#242424","font-size":13,"font-weight":500},behavior+". "+names[behavior-1]));
    for(const [value,y] of [[100,rowTop+12],[50,rowTop+29.5],[0,rowTop+47]]){
      chart.append(svg("line",{x1:left,x2:plotRight,y1:y,y2:y,stroke:"#e2e2e2","stroke-width":1,"stroke-dasharray":value===50?"3 4":"none"}));
      chart.append(svg("text",{x:left-9,y:y+4,"text-anchor":"end",fill:"#777","font-size":10},String(value)));
    }
    const points=weekly.map((item,index)=>({x:xAt(index),y:typeof item.latest.scores[behavior]==="number"?scoreY(item.latest.scores[behavior]):null,trust:item.latest.trust[behavior],week:item.week,score:item.latest.scores[behavior]}));
    for(let i=0;i<points.length-1;i++)if(points[i].trust==="ok"&&points[i+1].trust==="ok"&&points[i].y!==null&&points[i+1].y!==null)chart.append(svg("line",{x1:points[i].x,y1:points[i].y,x2:points[i+1].x,y2:points[i+1].y,stroke:"#3f3f3f","stroke-width":2.2,"stroke-linecap":"round"}));
    for(const point of points){
      if(point.y!==null){const hollow=point.trust==="not-trusted",circle=svg("circle",{cx:point.x,cy:point.y,r:hollow?5.2:4,fill:hollow?"#fff":"#242424",stroke:"#242424","stroke-width":hollow?2:1});circle.append(svg("title",{},"Behavior "+behavior+", "+point.week+": "+point.score+"/100"+(hollow?", not trusted":"")));chart.append(circle);}
      else if(point.trust==="not-trusted"){
        const y=rowTop+50,marker=svg("g",{});
        marker.append(svg("rect",{x:point.x-10,y,width:20,height:12,rx:3,fill:"#fff4d6",stroke:"#7a4b00","stroke-width":1.2}),svg("text",{x:point.x,y:y+9,"text-anchor":"middle",fill:"#7a4b00","font-size":8,"font-weight":700},"NT"),svg("title",{},"Behavior "+behavior+", "+point.week+": not trusted; no score"));
        chart.append(marker);
      }
    }
  }
  weekly.forEach((item,index)=>chart.append(svg("text",{x:xAt(index),y:height-8,"text-anchor":"middle",fill:"#646464","font-size":12},item.week)));
  }
  const history=$("history");history.replaceChildren();
  [...rows].sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).forEach(row=>{
    const tr=document.createElement("tr");
    const date=document.createElement("td");date.textContent=new Date(row.date).toLocaleDateString()+" · "+row.week;tr.append(date);
    const tested=document.createElement("td");tested.textContent=(row.control_only?"PARTIAL (filtered) · ":"")+row.tested;tr.append(tested);
    const verdict=document.createElement("td"),badge=document.createElement("span");badge.className="verdict "+row.verdict;badge.textContent=row.verdict;verdict.append(badge);tr.append(verdict);
    const delta=document.createElement("td");delta.textContent=row.verdict==="baseline"?"Baseline":row.targets.length?row.targets.map(n=>{if(row.trust[n]==="not-measured")return "#"+n+" not measured";if(row.trust[n]==="not-evaluable")return "#"+n+" not evaluable";if(row.trust[n]==="not-trusted")return "#"+n+" not trusted";const value=row.deltas[n];return "#"+n+" "+(value===null?"not measured":(value>0?"+":"")+value+" pts");}).join(" · "):"No targets";tr.append(delta);
    const report=document.createElement("td"),link=document.createElement("a"),[path,anchor]=row.report.split("#",2);link.href="../../../../../../"+path.split("/").map(encodeURIComponent).join("/")+(anchor?"#"+encodeURIComponent(anchor):"");link.textContent="Open report";report.append(link);tr.append(report);
    history.append(tr);
  });
}
window.addEventListener("resize",draw);draw();
</script>
</html>
`;

writeFileSync(output, html);
console.log(`Dashboard: ${output}`);
