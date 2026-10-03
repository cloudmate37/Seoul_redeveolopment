"""Convert collected EPSG:5174 boundaries to a public WGS84 GeoJSON."""
import argparse,json,pathlib
from pyproj import Transformer
from shapely.geometry import Polygon,mapping
from shapely.validation import make_valid
from shapely.ops import transform,unary_union
def build(snapshot,output):
 data=json.loads(snapshot.read_text());features=[]
 convert=Transformer.from_crs(5174,4326,always_xy=True).transform
 for d in data['targets']:
  polygons=[]
  for feature in data['boundaries'][d['presentSn']]:
   g=Polygon()
   for ring in feature['geometry']['rings']:g=g.symmetric_difference(make_valid(Polygon(ring)))
   polygons.append(g)
  boundary=unary_union(polygons)
  geographic=make_valid(transform(convert,boundary));geometry=mapping(geographic)
  point=geographic.representative_point()
  assert 126.7<point.x<127.3 and 37.4<point.y<37.8
  features.append({'type':'Feature','properties':{'id':d['presentSn'],'name':d['bsnsName'],'center':[point.y,point.x]},'geometry':geometry})
 assert len(features)==230
 output.write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,separators=(',',':')))
 print('230개 구역 경계 저장:',output)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('snapshot',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args();build(a.snapshot,a.output)
