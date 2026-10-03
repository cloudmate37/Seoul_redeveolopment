#!/usr/bin/env python3
"""Build public static pages from the locally collected Seoul snapshot."""
import argparse, json, pathlib, re, shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
PUBLIC='https://cloudmate37.github.io/Seoul_redeveolopment/'
def save(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
def build(snapshot,template,workbook_stage,write_frontend=False):
 data=json.loads((snapshot/'view_data.json').read_text())
 attachments={a['id']:{k:v for k,v in a.items() if k not in {'path','sha256','bytes','error'}} for a in data['attachments']}
 for a in attachments.values():a['status']='원본 링크 보존'
 catalog=[]
 for d in data['districts']:
  for p in d['plans']:p['data']=data['plan_data'][p['id']];p['district_plan']=data['district_plan_data'][p['id']]
  for b in d['businesses']:b['data']=data['business_data'][b['id']]
  d['attachments']=[attachments[i] for i in d['attachment_ids']]
  save(ROOT/'data/districts'/f'{d["id"]}.json',d)
  catalog.append({k:v for k,v in d.items() if k not in {'plans','businesses','attachment_ids','attachments'}})
 meta={k:data[k] for k in ['collected_at','source','issues','layer_stats','labels']}
 meta['districts']=catalog;save(ROOT/'data/catalog.json',meta)
 shutil.copy2(snapshot/'collection_report.json',ROOT/'collection_report.json')
 text=template.read_text();style=re.search(r'<style>(.*?)</style>',text,re.S).group(1)
 app=text.split('<script>',1)[1].split('</script>',1)[0]
 app=app[app.index('const $='):]
 app=app.replace("const attachmentMap=new Map(DATA.attachments.map(a=>[a.id,a]));","const attachmentMap=new Map();")
 app=app.replace('let selected=null,tabName=',"let selected=decodeURIComponent(location.hash.slice(1))||DATA.districts[0]?.id,tabName=")
 app=app.replace('function filesFor(owner){return DATA.attachments.filter(a=>a.owners.includes(owner));}',"function filesFor(owner){return [...attachmentMap.values()].filter(a=>a.owners.includes(owner));}")
 app=app.replace("function renderDetail(){const d=DATA.districts.find(d=>d.id===selected);",'''async function renderDetail(){const id=selected;let d;try{d=await loadDistrict(id);}catch(error){if(id===selected){$('#detail').innerHTML='<p class="status-note">구역 자료를 불러오지 못했습니다. 인터넷 연결을 확인한 뒤 다시 시도하세요.</p><button class="plain" id="retry">다시 시도</button>';$('#retry').onclick=renderDetail;}return;}if(id!==selected)return;''')
 app=app.replace("selected=decodeURIComponent(location.hash.slice(1))||DATA.districts[0]?.id;renderList();","renderList();")
 loader='''let DATA;const cache=new Map(),pending=new Map();
async function loadDistrict(id){if(!id)return null;if(cache.has(id))return cache.get(id);if(pending.has(id))return pending.get(id);$('#detail').innerHTML='<p class="muted">구역 자료를 불러오는 중입니다…</p>';const request=fetch('data/districts/'+encodeURIComponent(id)+'.json').then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).then(d=>{cache.set(id,d);for(const a of d.attachments)attachmentMap.set(a.id,a);return d;}).finally(()=>pending.delete(id));pending.set(id,request);return request;}
try{const response=await fetch('data/catalog.json');if(!response.ok)throw new Error('HTTP '+response.status);DATA=await response.json();}catch(error){document.querySelector('#subtitle').textContent='자료를 불러오지 못했습니다. 연결을 확인하고 새로고침하세요.';throw error;}
'''
 if write_frontend:
  (ROOT/'app.js').write_text(loader+app)
  (ROOT/'style.css').write_text(style)
 page=text.split('<script>',1)[0]
 page=re.sub(r'<style>.*?</style>','<link rel="stylesheet" href="style.css">',page,flags=re.S)
 page=page.replace('구역 경계 전체와 교차하는 공개 도시계획·사업 자료를 수집했습니다.','2026-10-02에 수집한 자료입니다. 첨부는 서울시 원본 링크로 연결됩니다. 구역 경계 전체와 교차하는 공개 도시계획·사업 자료를 수집했습니다.')
 if write_frontend:(ROOT/'index.html').write_text(page+'<script type="module" src="app.js"></script></html>')
 (ROOT/'.nojekyll').touch()
 # Rebuild workbook links for the public website, avoiding local-only paths.
 wb=json.loads((snapshot/'workbook_data.json').read_text())
 for sheet in wb['sheets']:
  headers=sheet['headers']
  for row in sheet['rows']:
   for i,h in enumerate(headers):
    if h=='로컬 상세':row[i]=PUBLIC+row[i]
    if h=='원본자료':row[i]=PUBLIC+'data/districts/'+row[headers.index('구역 ID')]+'.json'
    if h=='저장상태':row[i]='원본 링크 보존'
   if sheet['name']=='첨부파일':
    for h in ['로컬 파일','용량(byte)','오류']:row[headers.index(h)]=None
  if sheet['name']=='첨부파일':
   remove={headers.index(h) for h in ['로컬 파일','용량(byte)','오류']}
   sheet['headers']=[h for i,h in enumerate(headers) if i not in remove]
   sheet['rows']=[[v for i,v in enumerate(row) if i not in remove] for row in sheet['rows']]
 save(workbook_stage/'workbook_data.json',wb)
 print('Built',len(catalog),'districts;',len(attachments),'attachment URLs')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('snapshot',type=pathlib.Path);p.add_argument('template',type=pathlib.Path);p.add_argument('workbook_stage',type=pathlib.Path);p.add_argument('--write-frontend',action='store_true',help='기존 화면을 HTML 템플릿으로 덮어씁니다.');a=p.parse_args();build(a.snapshot,a.template,a.workbook_stage,a.write_frontend)
