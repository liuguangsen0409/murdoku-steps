import {expect,test} from 'vitest';
import {cases,resolveRoute} from '../src/case/catalog';
test('root is reserved for home and every case has its own direct route',()=>{expect(resolveRoute('/')).toEqual({});for(const c of cases){expect(resolveRoute('/'+c.slug).case).toBe(c);expect(resolveRoute('/'+c.slug+'/').redirect).toBe('/'+c.slug);}expect(resolveRoute('/missing').notFound).toBe(true);});
test('old query links resolve to canonical case paths',()=>{expect(resolveRoute('/','?case=frontier-town').redirect).toBe('/frontier-town');expect(resolveRoute('/','?case=24h-delivery').redirect).toBe('/24h-delivery');expect(resolveRoute('/','?case=missing').notFound).toBe(true);});
