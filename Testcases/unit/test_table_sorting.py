"""Sorting must retain every page and reject incorrect order or ignored clicks."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from Commons.browser_actions import Ui
from Commons.table_sorting import SortRule, SortingOptions, TableSorting, assert_sorted, infer_rule

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('direction,values', [
    ('asc', ['2', '10', '100', 'Not Reported']),
    ('desc', ['100', '10', '2', 'Not Reported']),
])
def test_numeric_sorting_and_missing_values(direction, values):
    rule = SortRule(kind='number', missing=('', 'Not Reported'))
    keys = [rule.key(value, direction) for value in values]
    assert_sorted(keys, direction)
    with pytest.raises(AssertionError):
        assert_sorted(keys[::-1], direction)
    assert SortRule(separator=';').key('Neoplasms, NOS; Other', 'asc') == 'Neoplasms, NOS'
    assert SortRule(separator=';').key('Neoplasms, NOS; Other', 'desc') == 'Other'
    assert infer_rule('Participant ID', ['10', '2']).kind == 'text'
    assert infer_rule('Age', ['10', '2', 'Not Reported']).kind == 'number'
    with pytest.raises(AssertionError):
        SortRule(kind='number').key('ten', direction)


def sorting_app(page, tmp_path, style='aria', broken=False, drop=False, initial_age=False):
    page.set_content('''<div id="results"><table><thead><tr>
      <th><input type="checkbox"></th><th>ID</th><th>Available CPI Mapping</th><th>Age</th>
      </tr></thead><tbody></tbody></table>
      <button aria-label="Previous page">Previous</button><button aria-label="Next page">Next</button></div>''')
    page.evaluate('''({style, broken, drop, initialAge}) => {
      let rows = [['A1','10'],['B2','2'],['C3','100'],['D4',''],['E5','30']];
      let current = 0, active = initialAge ? 3 : 1, direction = 'asc';
      if(initialAge) rows.sort((a,b)=>a[1]===''?1:b[1]===''?-1:Number(a[1])-Number(b[1]));
      const headers = [...document.querySelector('thead tr').children];
      if (style === 'hashed') {
        const selection = document.createElement('td');
        selection.innerHTML = headers[0].innerHTML;
        headers[0].replaceWith(selection);
      }
      const previous = document.querySelector('[aria-label="Previous page"]');
      const next = document.querySelector('[aria-label="Next page"]');
      function indicators() {
        for (const index of [1,3]) {
          const selected = active === index;
          if (style === 'aria') headers[index].setAttribute('aria-sort', selected ? (direction==='asc'?'ascending':'descending'):'none');
          else {
            headers[index].setAttribute('direction',direction);
            headers[index].innerHTML = '<span role="button" '+(style==='hashed'?'aria-describedby="tooltip"':'title="sort"')+' class="' +
              (style==='hashed'?'mui-jss-jss123':('MuiTableSortLabel-root-17 '+(selected?'MuiTableSortLabel-active-18':'')))+'">'+(index===1?'ID':'Age')+
              (selected?'<svg class="MuiTableSortLabel-iconDirection'+(direction==='asc'?'Asc':'Desc')+'-19"></svg>':'')+'</span>';
          }
        }
      }
      function render() {
        document.querySelector('tbody').innerHTML = rows.slice(current*2,current*2+2).map(row=>
          '<tr><td><input type="checkbox"></td><td>'+row[0]+'</td><td><button>1</button></td><td>'+row[1]+'</td></tr>').join('');
        previous.disabled = current===0; next.disabled = current*2+2>=rows.length;
      }
      for (const index of [1,3]) headers[index].onclick=()=>{
        direction=active===index && direction==='asc'?'desc':'asc'; active=index; indicators();
        const requested=direction;
        setTimeout(()=>{
          rows.sort((a,b)=>{
            const x=a[index===1?0:1],y=b[index===1?0:1];
            if(x==='')return y===''?0:1;if(y==='')return -1;
            const comparison=index===1?(x<y?-1:x>y?1:0):Number(x)-Number(y);
            return broken?comparison:comparison*(requested==='desc'?-1:1);
          });if(drop && requested==='desc')rows.pop();current=0;render();
        },80);
      };
      previous.onclick=()=>{current--;render();};next.onclick=()=>{current++;render();};
      indicators();render();
    }''', {'style': style, 'broken': broken, 'drop': drop, 'initialAge': initial_age})
    repo = Mock()
    repo.xpath.side_effect = lambda key: "//*[@id='results']" if key == 'Table' else "//button[@aria-label='Next page']"
    return Mock(page=page, ui=Ui(page, timeout_ms=500), repo=repo, output_dir=tmp_path, results=[],
                TABS={'People': SimpleNamespace(table='Table', next='Next')})


@pytest.mark.parametrize('style', ['aria', 'mui', 'hashed'])
def test_dynamic_sorting_reads_all_pages_and_skips_non_sortable_cells(page, tmp_path, style):
    app = sorting_app(page, tmp_path, style)
    evidence = TableSorting(app, 'People').verify('case.xlsx')
    assert evidence['record_count'] == 5
    assert {(e['column'], e['direction'], e['status']) for e in evidence['columns']} == {
        (column, direction, 'PASSED') for column in ('ID','Age') for direction in ('asc','desc')}
    assert {e['column'] for e in evidence['skipped']} == {'Column 1','Available CPI Mapping'}
    saved = json.loads((tmp_path/'result_tabs/case/people_sorting.json').read_text())
    assert saved == evidence


def test_ignored_sort_with_changed_indicator_fails_and_saves_evidence(page, tmp_path):
    app = sorting_app(page, tmp_path, broken=True)
    with pytest.raises(AssertionError, match='not sorted|did not settle'):
        TableSorting(app, 'People').verify('broken.xlsx')
    saved = json.loads((tmp_path/'result_tabs/broken/people_sorting.json').read_text())
    assert any(entry['status']=='FAILED' for entry in saved['columns'])


def test_sorting_refuses_a_truncated_baseline(page, tmp_path):
    app = sorting_app(page, tmp_path)
    with pytest.raises(AssertionError, match='narrow the filters'):
        TableSorting(app, 'People', SortingOptions(max_rows=2)).verify('too-many.xlsx')


@pytest.mark.parametrize('tab,folder,label', [
    ('Participants','participants','Participants'), ('Studies','studies','Studies'),
    ('Samples','samples','Samples'), ('GeneticAnalysis','genetic_analysis','Genetic_Analysis'),
    ('Files','files','Files'), ('ImagingData','imaging_data','Imaging_Data'),
])
def test_shared_excel_sorting_action_uses_case_name_and_preserves_filter(tab, folder, label):
    from pathlib import Path
    import openpyxl
    from Commons.apps.c3dc.app import C3DC
    from Testcases.unit.python_cases import run_python_case, case_report_name
    case = Path(__file__).resolve().parents[2] / f'Testcases/C3DC/result_tabs/{folder}/test_TC03_C3DC_Verify_{label}_Tab_Sorting.py'
    app = Mock(spec=C3DC)
    run_python_case(app, case)
    app.select_filter.assert_called_once_with('Diagnosis/Diagnosis', 'AbdominalFibromatosis')
    app.verify_result_tab_sorting.assert_called_once_with(tab, case_report_name(case))
    if tab in ('Files', 'ImagingData'):
        app.open_explore_files.assert_called_once_with()
        names = [call[0] for call in app.mock_calls]
        assert names.index('select_filter') < names.index('open_explore_files') < names.index('verify_result_tab_sorting')
    app.load_query_file.assert_not_called()


def test_sorted_output_cannot_hide_a_removed_record(page, tmp_path):
    app = sorting_app(page, tmp_path, drop=True)
    with pytest.raises(AssertionError, match='sorting changed table data/membership'):
        TableSorting(app, 'People').verify('missing-row.xlsx')


def test_c3dc_waiter_rejects_old_column_and_direction_and_http_success_with_graphql_error():
    from Commons.apps.c3dc.table_sorting import sorting_options
    options = sorting_options(Mock(), 'Participants')
    response = Mock(url='https://example.org/v1/graphql/')
    response.request.method = 'POST'
    response.request.post_data_json = {
        'operationName': 'participantOverview',
        'variables': {'order_by': 'participant_id', 'sort_direction': 'asc'}}
    assert options.response_matches(response, 'Participant ID', 'asc')
    assert not options.response_matches(response, 'Participant ID', 'desc')
    assert not options.response_matches(response, 'Sex at Birth', 'asc')
    response.json.return_value = {'errors': [
        {'message': 'Exception: No mapping found for [age_at_treatment_start] in order to sort on'}]}
    with pytest.raises(AssertionError, match='No mapping found for'):
        options.response_ids(response)


def test_cached_initial_order_does_not_require_another_http_response(page, tmp_path):
    from urllib.parse import parse_qs, urlparse
    app = sorting_app(page, tmp_path, initial_age=True)
    requests = []
    def respond(route):
        query = parse_qs(urlparse(route.request.url).query)
        field, direction = query['field'][0], query['direction'][0]
        requests.append((field, direction))
        rows = [('A1',10),('B2',2),('C3',100),('D4',None),('E5',30)]
        column = 0 if field == 'ID' else 1
        present = [row for row in rows if row[column] is not None]
        ordered = sorted(present, key=lambda row:row[column], reverse=direction=='desc')
        ordered += [row for row in rows if row[column] is None]
        route.fulfill(content_type='application/json', headers={'access-control-allow-origin':'*'},
                      body=json.dumps({'ids':[row[0] for row in ordered[:2]]}))
    page.route('https://sorting.test/data?*', respond)
    page.evaluate('''() => {
      for(const index of [1,3]) {
        const header=document.querySelectorAll('th')[index], old=header.onclick;
        header.onclick=()=>{
          old();
          const direction=header.getAttribute('aria-sort')==='ascending'?'asc':'desc';
          if(!(index===3 && direction==='asc'))
            fetch('https://sorting.test/data?field='+(index===1?'ID':'Age')+'&direction='+direction);
        };
      }
    }''')
    options = SortingOptions(identity_column='ID',
        response_matches=lambda response,name,direction:
            response.url==f'https://sorting.test/data?field={name}&direction={direction}',
        response_ids=lambda response:response.json()['ids'])
    evidence = TableSorting(app,'People',options).verify('cached.xlsx')
    assert all(entry['status']=='PASSED' for entry in evidence['columns'])
    assert requests==[('ID','asc'),('ID','desc'),('Age','desc')]


def test_sort_waits_for_render_after_response_when_old_values_already_look_sorted(page, tmp_path):
    app = sorting_app(page, tmp_path, initial_age=True)
    app.ui.timeout_ms = 2000
    page.locator('th').nth(1).evaluate("el => el.setAttribute('aria-sort', 'ascending')")
    page.locator('th').nth(3).evaluate("el => el.setAttribute('aria-sort', 'none')")
    page.route('https://sorting.test/slow-age', lambda route: route.fulfill(
        content_type='application/json', headers={'access-control-allow-origin': '*'},
        body=json.dumps({'ids': ['C3', 'E5'], 'ages': ['100', '30']})))
    page.evaluate('''() => {
      const header = document.querySelectorAll('th')[3];
      header.onclick = () => {
        header.setAttribute('aria-sort', 'ascending');
        fetch('https://sorting.test/slow-age').then(r => r.json()).then(data => {
          setTimeout(() => {
            document.querySelector('tbody').innerHTML = data.ids.map((id, i) =>
              '<tr><td></td><td>'+id+'</td><td></td><td>'+data.ages[i]+'</td></tr>').join('');
          }, 350);
        });
      };
    }''')
    options = SortingOptions(identity_column='ID',
        response_matches=lambda response, name, direction: response.url == 'https://sorting.test/slow-age',
        response_ids=lambda response: response.json()['ids'])
    helper = TableSorting(app, 'People', options)
    helper.discover()
    helper.rules = {'Age': SortRule(kind='number')}
    # The old page is ascending already; its indicator or short DOM stability is insufficient.
    assert [row[3] for row in helper.snapshot()] == ['2', '10']
    helper.set_direction(3, 'Age', 'asc')
    rows = helper.snapshot()
    assert [row[1] for row in rows] == ['C3', 'E5']
    with pytest.raises(AssertionError, match='not sorted'):
        assert_sorted([helper.key(3, 'Age', row, 'asc') for row in rows], 'asc')


def test_link_columns_compare_urls_when_labels_are_identical(page, tmp_path):
    app = sorting_app(page, tmp_path)
    page.set_content('''<div id="results"><table><thead><tr><th aria-sort="ascending">Viewer</th></tr></thead>
      <tbody><tr><td><a href="https://example.org/a">View</a></td></tr>
      <tr><td><a href="https://example.org/b">View</a></td></tr></tbody></table></div>''')
    page.evaluate('''() => document.querySelector('th').onclick=()=>{
      const header=document.querySelector('th'), body=document.querySelector('tbody');
      header.setAttribute('aria-sort',header.getAttribute('aria-sort')==='ascending'?'descending':'ascending');
      [...body.rows].reverse().forEach(row=>body.appendChild(row));
    }''')
    evidence=TableSorting(app,'People',SortingOptions(link_columns=('Viewer',))).verify('links.xlsx')
    assert [entry['status'] for entry in evidence['columns']]==['PASSED','PASSED']
    assert evidence['columns'][1]['values']==['https://example.org/b','https://example.org/a']


def test_c3dc_unknown_sample_age_uses_indexed_numeric_sentinel():
    from Commons.apps.c3dc.table_sorting import sorting_options
    rule=sorting_options(Mock(),'Samples').rules['Participant Age at Collection (days)']
    assert_sorted([rule.key(value,'asc') for value in ('Not Reported','2','10')],'asc')


def test_c3dc_files_without_collection_metadata_sort_as_missing():
    from Commons.apps.c3dc.table_sorting import sorting_options
    rule=sorting_options(Mock(),'Files').rules['Age at Collection']
    assert rule.key('Not Reported','asc') is None
    assert_sorted([rule.key(value,'asc') for value in ('2','10','Not Reported')],'asc')


def test_study_investigator_names_keep_embedded_commas_as_complete_values():
    from Commons.apps.c3dc.table_sorting import sorting_options
    options=sorting_options(Mock(),'Studies')
    response=Mock()
    names=['Elaine R. Mardis, PhD','Malcolm Smith, MD, PhD']
    response.json.return_value={'data':{'studyOverview':[
        {'study_id':'phs001','personnel_name':names,'pubmed_id':[],'grant_id':[]}]}}
    assert options.response_ids(response)==['phs001']
    values=options.cell_values('Principal Investigator(s)','phs001',', '.join(names))
    assert options.rules['Principal Investigator(s)'].key(values,'desc')=='Malcolm Smith, MD, PhD'
    with pytest.raises(AssertionError, match='displayed values differ'):
        options.cell_values('Principal Investigator(s)','phs001',names[0])


def test_multiline_cells_preserve_array_boundaries(page,tmp_path):
    app=sorting_app(page,tmp_path)
    page.locator('tbody tr').first.locator('td').nth(1).evaluate("cell=>cell.innerHTML='A1<br>A2'")
    helper=TableSorting(app,'People')
    helper.discover()
    assert helper.snapshot()[0][1]=='A1; A2'
    assert SortRule(kind='number').key(['10','2'],'asc')==2
