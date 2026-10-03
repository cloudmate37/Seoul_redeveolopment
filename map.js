export async function createDistrictMap(districts,onSelect){
 const L=window.L;
 if(!L)throw new Error('지도 라이브러리를 불러오지 못했습니다.');
 const map=L.map('map',{minZoom:9,maxZoom:19}).setView([37.5665,126.978],11);
 const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'}).addTo(map);
 let tileErrors=0;
 tiles.on('tileerror',()=>{if(++tileErrors>=3){const warning=document.querySelector('#map-error');warning.hidden=false;warning.textContent='배경지도를 불러오지 못했습니다. 구역 위치와 경계는 계속 확인할 수 있습니다.';}});
 tiles.on('tileload',()=>{tileErrors=0;document.querySelector('#map-error').hidden=true;});
 L.control.scale({imperial:false,position:'bottomleft'}).addTo(map);
 const response=await fetch('data/boundaries.geojson');
 if(!response.ok)throw new Error('구역 경계를 불러오지 못했습니다.');
 const geo=await response.json(),catalog=new Map(districts.map(d=>[d.id,d]));
 const group=L.featureGroup().addTo(map),entries=new Map();
 const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 for(const f of geo.features){
  const d=catalog.get(f.properties.id);if(!d)continue;
  const color=d.fields['추진상태']==='완료'?'#12649b':'#dc8a16';
  const polygon=L.geoJSON(f,{style:{color,weight:1.5,fillOpacity:.22}});
  const marker=L.circleMarker(f.properties.center,{radius:5,color:'#fff',weight:1.5,fillColor:color,fillOpacity:1});
  const title=`${escape(d.name)}<br><span>${escape(d.fields['자치구'])} · ${escape(d.fields['추진상태'])}</span>`;
  polygon.bindTooltip(title,{sticky:true});marker.bindTooltip(title,{direction:'top'});
  polygon.on('click',()=>onSelect(d.id));marker.on('click',()=>onSelect(d.id));
  entries.set(d.id,{polygon,marker,color,name:d.name});
 }
 let visible=[];
 function update(filtered,selected,fit=false){
  visible=filtered;group.clearLayers();
  for(const d of filtered){
   const e=entries.get(d.id);if(!e)continue;
   e.polygon.setStyle({color:d.id===selected?'#c83b36':e.color,weight:d.id===selected?3:1.5,fillOpacity:d.id===selected ? .4 : .22});
   e.marker.setStyle({fillColor:d.id===selected?'#c83b36':e.color,radius:d.id===selected?7:5});
   group.addLayer(e.polygon);group.addLayer(e.marker);
   const path=e.marker.getElement();
   if(path){path.setAttribute('role','button');path.setAttribute('tabindex','0');path.setAttribute('aria-label',`${e.name} 구역 상세 보기`);path.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();onSelect(d.id);}};}
  }
  if(fit)fitVisible();
 }
 function fitVisible(){if(visible.length&&group.getBounds().isValid())map.fitBounds(group.getBounds(),{padding:[24,24],maxZoom:visible.length===1?16:13,animate:false});}
 function focus(id){const e=entries.get(id);if(e)map.fitBounds(e.polygon.getBounds(),{padding:[40,40],maxZoom:16,animate:false});}
 return {update,focus,fitVisible,map};
}
