// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import { extractArticle, extractFrom } from '../apps/browser-extension/src/extraction';
import { request, unwrap } from '../packages/types/src';

describe('extracción local de páginas',()=>{
 it('conserva artículo y excluye scripts, navegación y anuncios',()=>{
  document.body.innerHTML=`<nav>MENÚ EXCLUIDO</nav><article><h1>Un paseo por el bosque</h1>${Array.from({length:10},()=>'<p>El bosque nos invita a caminar despacio y escuchar a los pájaros. La naturaleza nos acompaña durante todo el camino.</p>').join('')}<aside>ANUNCIO EXCLUIDO</aside><script>SECRETO EXCLUIDO</script><p hidden>OCULTO EXCLUIDO</p></article><footer>PIE EXCLUIDO</footer>`;
  const result=extractArticle(document);
  expect(result.text).toContain('bosque');
  for(const excluded of ['MENÚ EXCLUIDO','ANUNCIO EXCLUIDO','SECRETO EXCLUIDO','OCULTO EXCLUIDO','PIE EXCLUIDO'])expect(result.text).not.toContain(excluded);
 });
 it('lee desde un párrafo y continúa en orden',()=>{
  document.body.innerHTML='<main><p>Primero.</p><p id="start">Segundo <b>párrafo.</b></p><p>Tercero.</p></main>';
  expect(extractFrom(document,document.querySelector('#start b')).text).toBe('Segundo párrafo.\n\nTercero.');
 });
 it('omite elementos ocultos por CSS',()=>{
  document.body.innerHTML='<main><p>Inicio.</p><p style="display:none">Oculto.</p><p>Final.</p></main>';
  expect(extractFrom(document,document.querySelector('p')).text).toBe('Inicio.\n\nFinal.');
 });
});
it('comparte un protocolo versionado y rechaza errores',()=>{
 expect(request('pause')).toMatchObject({protocol_version:1,type:'command',command:'pause'});
 expect(()=>unwrap({protocol_version:1,id:'x',type:'response',success:false,error:{code:'model_missing',message:'Instala el modelo.'}})).toThrow('Instala el modelo.');
});
