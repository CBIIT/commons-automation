"""Page sizes must change actual rows, retain all records, and keep navigation coherent."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from Commons.browser_actions import Ui
from Commons.table_pagination import PaginationOptions, TablePagination, parse_page_range, resized_offset

pytestmark = pytest.mark.unit


def pagination_app(page, tmp_path, *, style='native', total=139, sizes=(10,25,50,100), fault='', policy='first'):
    page.set_content('''<div id="unrelated"><button aria-label="Next page">Unrelated</button></div>
      <div id="results"><table><thead><tr><th>ID</th><th>Value</th></tr></thead><tbody></tbody></table>
      <div class="MuiTablePagination-root-fixture"><span>Rows per page:</span><span id="size-control"></span>
      <span id="range"></span><button aria-label="Previous page">Previous</button>
      <button aria-label="Next page">Next</button></div></div>''')
    page.evaluate('''({style,total,sizes,fault,policy})=>{
      let size=sizes[0],current=0;
      const footer=document.querySelector('.MuiTablePagination-root-fixture');
      const previous=footer.querySelector('[aria-label="Previous page"]');
      const next=footer.querySelector('[aria-label="Next page"]');
      const holder=document.querySelector('#size-control');
      const control=document.createElement(style==='native'?'select':'div');
      if(style==='native') {
        for(const value of sizes){const option=document.createElement('option');option.value=value;option.textContent=value;control.appendChild(option);}
        control.onchange=()=>resize(Number(control.value));
      } else {
        control.setAttribute('role','button');control.className='MuiSelect-root-fixture';
        control.onclick=()=>{
          const menu=document.createElement('ul');menu.setAttribute('role','listbox');
          for(const value of sizes){const option=document.createElement('li');option.setAttribute('role','option');
            option.dataset.value=value;option.textContent=value;
            option.onclick=()=>{resize(value);menu.remove();};menu.appendChild(option);}
          document.body.appendChild(menu);
        };
      }
      holder.appendChild(control);
      document.addEventListener('keydown',event=>{if(event.key==='Escape')document.querySelector('[role="listbox"]')?.remove();});
      function render(){
        const offset=current*size, end=Math.min(offset+size,total);
        const count=fault==='rowcount' && size===25?Math.min(10,end-offset):end-offset;
        const rows=[];
        for(let index=offset;index<offset+count;index++){
          const actual=fault==='duplicate' && offset>0 && index===offset?index-1:index;
          rows.push('<tr><td>p'+String(actual).padStart(4,'0')+'</td><td>value-'+actual+'</td></tr>');
        }
        document.querySelector('tbody').innerHTML=rows.join('') || '<tr><td colspan="2">No results</td></tr>';
        document.querySelector('#range').textContent=(total?offset+1:0)+'–'+end+' of '+(fault==='total'?total+1:total);
        previous.disabled=current===0;
        next.disabled=end===total || fault==='next';
        if(style==='native')control.value=String(size);else control.textContent=String(size);
      }
      function resize(value){
        const oldOffset=current*size,oldPage=current;
        size=value;
        if(policy==='first')current=0;
        else if(policy==='keep_first_row')current=Math.floor(oldOffset/size);
        else current=Math.min(oldPage,Math.max(0,Math.ceil(total/size)-1));
        if(fault==='reset' && oldPage>0)current=Math.min(oldPage,Math.max(0,Math.ceil(total/size)-1));
        if(style==='native')control.value=String(size);else control.textContent=String(size);
        setTimeout(render,30);
      }
      previous.onclick=()=>{current--;setTimeout(render,30);};
      next.onclick=()=>{current++;setTimeout(render,30);};
      render();
    }''', {'style':style,'total':total,'sizes':list(sizes),'fault':fault,'policy':policy})
    repo=Mock()
    repo.xpath.side_effect=lambda key:"//*[@id='results']" if key=='Table' else "//button[@aria-label='Next page']"
    app=Mock(page=page,ui=Ui(page,timeout_ms=1200),repo=repo,output_dir=tmp_path,results=[],
             TABS={'People':SimpleNamespace(table='Table',next='Next')})
    options=PaginationOptions(identity_columns=('ID',),total_reader=lambda:total,size_change_policy=policy)
    return app,options


@pytest.mark.parametrize('style',['native','mui'])
def test_all_page_sizes_ranges_bidirectional_pages_and_mid_page_resize(page,tmp_path,style):
    app,options=pagination_app(page,tmp_path,style=style)
    evidence=TablePagination(app,'People',options).verify('sizes.xlsx')
    assert evidence['available_sizes']==[10,25,50,100]
    assert evidence['record_count']==139 and evidence['restored']
    assert [len(item['forward_pages']) for item in evidence['sizes']]==[14,6,3,2]
    assert [item['forward_pages'][-1]['row_count'] for item in evidence['sizes']]==[9,14,39,39]
    assert all(item['mid_page_resize']['start']==1 for item in evidence['sizes'])
    assert all(len(item['backward_pages'])==len(item['forward_pages'])-1 for item in evidence['sizes'])
    assert json.loads((tmp_path/'result_tabs/sizes/people_pagination.json').read_text())==evidence


@pytest.mark.parametrize('total',[0,3,50])
def test_empty_small_and_exact_page_result_counts(page,tmp_path,total):
    app,options=pagination_app(page,tmp_path,total=total,sizes=(50,100))
    evidence=TablePagination(app,'People',options).verify('small.xlsx',[50,100])
    for item in evidence['sizes']:
        assert len(item['forward_pages'])==1
        assert item['forward_pages'][0]['row_count']==total
        assert item['forward_pages'][0]['previous_disabled'] and item['forward_pages'][0]['next_disabled']
        assert item['mid_page_resize']['status']=='NOT_APPLICABLE'


def test_required_missing_page_size_is_not_silently_skipped(page,tmp_path):
    app,options=pagination_app(page,tmp_path,sizes=(50,100))
    with pytest.raises(AssertionError,match='Required page sizes unavailable'):
        TablePagination(app,'People',options).verify('missing.xlsx',[10,25,50,100])


@pytest.mark.parametrize('fault,expected',[
    ('rowcount','did not settle'),('duplicate','repeated record identities'),
    ('total','did not finish loading'),('next','Incorrect Next'),('reset','did not settle'),
])
def test_pagination_defects_fail_and_save_evidence(page,tmp_path,fault,expected):
    app,options=pagination_app(page,tmp_path,fault=fault,total=65,sizes=(10,25))
    with pytest.raises(AssertionError,match=expected):
        TablePagination(app,'People',options).verify('broken.xlsx')
    evidence=json.loads((tmp_path/'result_tabs/broken/people_pagination.json').read_text())
    assert evidence.get('error')


@pytest.mark.parametrize('policy',['keep_first_row','same_page'])
def test_application_specific_size_change_policy(page,tmp_path,policy):
    app,options=pagination_app(page,tmp_path,total=65,sizes=(10,25),policy=policy)
    evidence=TablePagination(app,'People',options).verify('policy.xlsx')
    assert evidence['restored']


def test_range_formats_and_resize_math():
    assert parse_page_range('Showing 1 to 25 of 1,139 entries')==(1,25,1139)
    assert parse_page_range('101–139 of 139')==(101,139,139)
    assert parse_page_range('0-0 of 0')==(0,0,0)
    for text in ('10-5 of 10','0-10 of 10','1-20 of 10','No rows'):
        with pytest.raises(AssertionError):parse_page_range(text)
    assert resized_offset(100,50,25,139,'first')==0
    assert resized_offset(100,50,25,139,'keep_first_row')==100
    assert resized_offset(100,50,25,139,'same_page')==50


@pytest.mark.parametrize('tab,folder,label',[
    ('Files','files','Files'),('Studies','studies','Studies'),
    ('Participants','participants','Participants'),('Samples','samples','Samples'),
    ('GeneticAnalysis','genetic_analysis','Genetic_Analysis'),
    ('ImagingData','imaging_data','Imaging_Data'),
])
def test_excel_pagination_cases_dispatch_supported_sizes_and_preserve_diagnosis(tab,folder,label):
    from pathlib import Path
    import openpyxl
    from Commons.apps.c3dc.app import C3DC
    from Commons.excel_testcase.runner import run_testcase_excel
    case=Path(__file__).resolve().parents[2]/f'Testcases/C3DC/result_tabs/{folder}/TC04_C3DC_Verify_{label}_Tab_Pagination.xlsx'
    workbook=openpyxl.load_workbook(case)
    assert workbook['_Lists'].sheet_state=='hidden'
    assert workbook['Steps'].data_validations.dataValidation[0].formula1 in workbook.defined_names
    assert 'verify_result_tab_pagination' in [row[0] for row in workbook['_Lists'].values]
    workbook.close()
    app=Mock(spec=C3DC)
    run_testcase_excel(app,case)
    app.verify_result_tab_pagination.assert_called_once_with(tab,page_sizes=[50,100],report_name=case.name)
    app.select_filter.assert_called_once_with('Diagnosis/Diagnosis','AbdominalFibromatosis')
    app.load_query_file.assert_not_called()
    if tab in ('Files','ImagingData'):
        calls=[call[0] for call in app.mock_calls]
        assert calls.index('select_filter')<calls.index('open_explore_files')<calls.index('verify_result_tab_pagination')
