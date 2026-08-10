import os
import shutil
import json
import secrets
import requests
import re
from datetime import datetime

def load_template(name, noxaml = False):
    print(f'load_template-加载模板文件-{name}')
    global templates
    if not name in templates:
        t_path = os.path.join(BASE_PATH, 'templates', name+('' if noxaml else '.xaml'))
        with open(t_path,'r', encoding='utf-8') as f:
            templates[name] =  f.read()

def load_rank_template():
    load_template('rank_up')
    load_template('rank_down')
    load_template('rank_even')
    load_template('rank_new')
    load_template('rank_re')
    load_template('rank_rf')

def save_output_file(name, data):
    print(f'save_output_file-保存输出文件-{name}')
    o_path = os.path.join(BASE_PATH, 'output', name)
    os.makedirs(os.path.dirname(o_path), exist_ok=True)
    with open(o_path,'w', encoding='utf-8') as f:
        f.write(data)

def replaces(string: str, s: dict):
    output = string
    for l, d in s.items():
        output = output.replace('{'+l+'}', str(d))
    return output

def uninumber(n: int):
    if n >= 100000000:
        return '{:.1f}'.format(n/100000000) + '亿'
    elif n >= 10000:
        return '{:.1f}'.format(n/10000) + '万'
    else:
        return n
    
def nlv(s):
    return '\\n'.join(str(s).splitlines())

def rank_status(m):
    if m['specialStatus']:
        if m['specialStatus'] == 'revote':
            return 're'
        else:
            return 'rf'
    else:
        if not (m['weeksOnBoard'] != 1 or m['firstRecordedAt'] == None or m['issueEndDate'] == None or m['firstRecordedAt'] > m['issueEndDate']):
            return 'new'
        if m['lastRank']:
            if m['rank'] > m['lastRank']:
                return 'up'
            if m['rank'] < m['lastRank']:
                return 'down'
            if m['rank'] == m['lastRank']:
                return 'even'
        return 'up'

def escape_xaml(text):
    if text is None:
        return ''
    return (
        text.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('"', '&quot;')
             .replace("'", '&apos;')
    )

def iso_to_timestamp(iso_str):
    return int(datetime.fromisoformat(iso_str.replace('Z', '+00:00')).timestamp())

def mainpage():
    print('mainpage-开始')
    print('mainpage-加载模板')
    load_template('mainpage')
    load_template('music')
    load_rank_template()

    print('mainpage-加载缓存')
    try:
        with open(f'data/b1_issues/{b1_issues[0]['issue_id']}.json','r',encoding='utf-8') as f:
            music_data = json.load(f)[-5:]
    except:
        print('mainpage-获取api数据')
        music_data = requests.get(f'https://biliboard.uk/api/public/boards/1/issues/{b1_issues[0]['issue_id']}/rankings').json()[-5:]
        with open(f'data/b1_issues/{b1_issues[0]['issue_id']}.json','w',encoding='utf-8') as f:
            json.dump(music_data, f, ensure_ascii=False)

    print('mainpage-构建页面')
    output = replaces(templates['mainpage'],{
        'music':'\n'.join([
            replaces(templates['music'],{
                'img': escape_xaml('https://biliboard.uk'+m['coverUrl']),
                'name': escape_xaml(m['title']),
                'name_cn': escape_xaml(m['titleCn']),
                'p': escape_xaml('/'.join([p['name'] for p in m['producers']])),
                'v': escape_xaml('/'.join([v['name'] for v in m['vocalists']])),
                'rank': replaces(templates[f'rank_{rank_status(m)}'],{
                    'rank':m['rank']
                }),
                'rate': escape_xaml(m['rate']) if m['rate'] != None else '无',
                'more': (lambda n, l: f'+{(n-l)/l*100:.2f}%')(m['score'], music_data[index]['score']) if index != len(music_data) else '无',
                'score_view': m['stats']['views'],
                'score_like': m['stats']['likes'],
                'score_coin': m['stats']['coins'],
                'score_fav': m['stats']['favorites'],
                'score_main': str(m['score'])[:-4] if m['score'] >= 10000 else m['score'],
                'score_trivial': str(m['score'])[-4:] if m['score'] >= 10000 else '',
                's1': m['lastRank'] if m['lastRank'] else '--',
                's2': m['weeksOnBoard'] if m['weeksOnBoard'] else '--',
                's3': m['peakRank'] if m['peakRank'] else '--',
                's1t': '上周排名', 's2t': '在榜周数', 's3t': '最高排名',
            }) for index, m in enumerate(music_data,start=1)
        ][::-1]),
        'gv': BUILD_VERSION,
        'i': b1_issues[0]['issue_id'],
        'all': f'https://vocaloid.p.kaphia.qzz.io/board1/issue_{b1_issues[0]['issue_id']}.json',
    })
    print('mainpage-保存输出文件')
    save_output_file('Custom.xaml',output)
    save_output_file('Custom.xaml.ini',BUILD_VERSION)
    save_output_file('Custom.json',json.dumps({
        'Title': f'Vocaloid 术力口榜单'
    },ensure_ascii=False))

def b1issues():
    print('b1issues-开始')
    print('b1issues-加载模板')
    load_template('issuepage')
    load_template('music')
    load_template('indexpage')
    load_template('indexpage-item')
    load_rank_template()

    print('b1issues-构建页面')
    for issue in b1_issues:
        print(f'b1issues-开始第{issue['issue_id']}期')

        print('b1issues-加载缓存')
        try:
            with open(f'data/b1_issues/{issue['issue_id']}.json','r',encoding='utf-8') as f:
                music_data = json.load(f)
        except:
            print('b1issues-获取api数据')
            music_data = requests.get(f'https://biliboard.uk/api/public/boards/1/issues/{issue['issue_id']}/rankings').json()
            with open(f'data/b1_issues/{issue['issue_id']}.json','w',encoding='utf-8') as f:
                json.dump(music_data, f, ensure_ascii=False)

        output = replaces(templates['issuepage'],{
            'music':'\n'.join([
                replaces(templates['music'],{
                    'img': escape_xaml('https://biliboard.uk'+m['coverUrl']),
                    'name': escape_xaml(m['title']),
                    'name_cn': escape_xaml(m['titleCn']),
                    'p': escape_xaml('/'.join([p['name'] for p in m['producers']])),
                    'v': escape_xaml('/'.join([v['name'] for v in m['vocalists']])),
                    'rank': replaces(templates[f'rank_{rank_status(m)}'],{
                        'rank':m['rank']
                    }),
                    'rate': escape_xaml(m['rate']) if m['rate'] != None else '无',
                    'more': (lambda n, l: f'+{(n-l)/l*100:.2f}%' 
                        if l>0 else '无'
                    )(m['score'], music_data[index]['score']) if index != len(music_data) else '无',
                    'score_view': m['stats']['views'],
                    'score_like': m['stats']['likes'],
                    'score_coin': m['stats']['coins'],
                    'score_fav': m['stats']['favorites'],
                    'score_main': str(m['score'])[:-4] if m['score'] >= 10000 else m['score'],
                    'score_trivial': str(m['score'])[-4:] if m['score'] >= 10000 else '',
                    's1': m['lastRank'] if m['lastRank'] else '--',
                    's2': m['weeksOnBoard'] if m['weeksOnBoard'] else '--',
                    's3': m['peakRank'] if m['peakRank'] else '--',
                    's1t': '上周排名', 's2t': '在榜周数', 's3t': '最高排名',
                }) for index, m in enumerate(music_data,start=1)
            ]),
            'title': f'周榜 第{issue['issue_id']}期 {issue['year']}年第{issue['week']}周',
            'bv': issue['video_bvid'],
            'all': 'https://vocaloid.p.kaphia.qzz.io/board1/index.json',
        })
        save_output_file(f'board1/issue_{issue['issue_id']}.xaml',output)
        save_output_file(f'board1/issue_{issue['issue_id']}.json',json.dumps({
            'Title': f'Vocaloid 术力口榜单 | 周榜 第{issue['issue_id']}期 {issue['year']}年第{issue['week']}周'
        },ensure_ascii=False))
    
    print('b1issues-保存目录')
    save_output_file(f'board1/index.xaml',replaces(templates['indexpage'],{
        'title':'周榜',
        'item':''.join([
            replaces(templates['indexpage-item'],{
                'title': f'周榜 第{issue['issue_id']}期',
                'info': f'{issue['year']}年第{issue['week']}周',
                'url': f'https://vocaloid.p.kaphia.qzz.io/board1/issue_{issue['issue_id']}.json',
            })
            for issue in sorted(b1_issues, key=lambda x: int(x['issue_id']), reverse=True)
        ])
    }))
    save_output_file(f'board1/index.json',json.dumps({
        'Title': f'Vocaloid 术力口榜单 | 周榜列表'
    },ensure_ascii=False))

def b2issues():
    print('b2issues-开始')
    print('b2issues-加载模板')
    load_template('issuepage')
    load_template('music')
    load_template('indexpage')
    load_template('indexpage-item')
    load_rank_template()

    print('b2issues-构建页面')
    for issue in b2_issues:
        print(f'b2issues-开始第{issue['issue_id']}期')

        print('b2issues-加载缓存')
        try:
            with open(f'data/b2_issues/{issue['issue_id']}.json','r',encoding='utf-8') as f:
                music_data = json.load(f)
        except:
            print('b2issues-获取api数据')
            music_data = requests.get(f'https://biliboard.uk/api/public/boards/2/issues/{issue['issue_id']}/rankings').json()
            with open(f'data/b2_issues/{issue['issue_id']}.json','w',encoding='utf-8') as f:
                json.dump(music_data, f, ensure_ascii=False)

        output = replaces(templates['issuepage'],{
            'music':'\n'.join([
                replaces(templates['music'],{
                    'img': escape_xaml('https://biliboard.uk'+m['coverUrl']),
                    'name': escape_xaml(m['title']),
                    'name_cn': escape_xaml(m['titleCn']),
                    'p': escape_xaml('/'.join([p['name'] for p in m['producers']])),
                    'v': escape_xaml('/'.join([v['name'] for v in m['vocalists']])),
                    'rank': replaces(templates[f'rank_{rank_status(m)}'],{
                        'rank':m['rank']
                    }),
                    'rate': escape_xaml(m['rate']) if m['rate'] != None else '无',
                    'more': (lambda n, l: f'+{(n-l)/l*100:.2f}%' 
                        if l>0 else '无'
                    )(m['score'], music_data[index]['score']) if index != len(music_data) else '无',
                    'score_view': m['stats']['views'],
                    'score_like': m['stats']['likes'],
                    'score_coin': m['stats']['coins'],
                    'score_fav': m['stats']['favorites'],
                    'score_main': str(m['score'])[:-4] if m['score'] >= 10000 else m['score'],
                    'score_trivial': str(m['score'])[-4:] if m['score'] >= 10000 else '',
                    's1': m['lastRank'] if m['lastRank'] else '--',
                    's2': m['weeksOnBoard'] if m['weeksOnBoard'] else '--',
                    's3': m['peakRank'] if m['peakRank'] else '--',
                    's1t': '上周排名', 's2t': '在榜周数', 's3t': '最高排名',
                }) for index, m in enumerate(music_data,start=1)
            ]),
            'title': f'传说榜 第{issue['issue_id']}期 {issue['year']}年第{issue['week']}周',
            'bv': issue['video_bvid'],
            'all': 'https://vocaloid.p.kaphia.qzz.io/board2/index.json',
        })
        save_output_file(f'board2/issue_{issue['issue_id']}.xaml',output)
        save_output_file(f'board2/issue_{issue['issue_id']}.json',json.dumps({
            'Title': f'Vocaloid 术力口榜单 | 传说榜 第{issue['issue_id']}期 {issue['year']}年第{issue['week']}周'
        },ensure_ascii=False))
    
    print('b2issues-保存目录')
    save_output_file(f'board2/index.xaml',replaces(templates['indexpage'],{
        'title':'传说榜',
        'item':''.join([
            replaces(templates['indexpage-item'],{
                'title': f'传说榜 第{issue['issue_id']}期',
                'info': f'{issue['year']}年第{issue['week']}周',
                'url': f'https://vocaloid.p.kaphia.qzz.io/board2/issue_{issue['issue_id']}.json',
            })
            for issue in sorted(b2_issues, key=lambda x: int(x['issue_id']), reverse=True)
        ])
    }))
    save_output_file(f'board2/index.json',json.dumps({
        'Title': f'Vocaloid 术力口榜单 | 传说榜列表'
    },ensure_ascii=False))

def b3issues():
    print('b3issues-开始')
    print('b3issues-加载模板')
    load_template('issuepage')
    load_template('music')
    load_template('indexpage')
    load_template('indexpage-item')
    load_rank_template()
    sub_title = {
        0: '年榜',
        1: '上半年榜',
        2: '下半年榜',
    }

    print('b3issues-构建页面')
    for issue in b3_issues:
        print(f'b3issues-开始第{issue['issue_id']}期')

        print('b3issues-加载缓存')
        try:
            with open(f'data/b3_issues/{issue['issue_id']}.json','r',encoding='utf-8') as f:
                music_data = json.load(f)
        except:
            print('b3issues-获取api数据')
            music_data = requests.get(f'https://biliboard.uk/api/public/boards/3/issues/{issue['issue_id']}/rankings').json()
            with open(f'data/b3_issues/{issue['issue_id']}.json','w',encoding='utf-8') as f:
                json.dump(music_data, f, ensure_ascii=False)

        output = replaces(templates['issuepage'],{
            'music':'\n'.join([
                replaces(templates['music'],{
                    'img': escape_xaml('https://biliboard.uk'+m['coverUrl']),
                    'name': escape_xaml(m['title']),
                    'name_cn': escape_xaml(m['titleCn']),
                    'p': escape_xaml('/'.join([p['name'] for p in m['producers']])),
                    'v': escape_xaml('/'.join([v['name'] for v in m['vocalists']])),
                    'rank': replaces(templates[f'rank_{rank_status(m)}'],{
                        'rank':m['rank']
                    }),
                    'rate': escape_xaml(m['rate']) if m['rate'] != None else '无',
                    'more': (lambda n, l: f'+{(n-l)/l*100:.2f}%' 
                        if l>0 else '无'
                    )(m['score'], music_data[index]['score']) if index != len(music_data) else '无',
                    'score_view': m['stats']['views'],
                    'score_like': m['stats']['likes'],
                    'score_coin': m['stats']['coins'],
                    'score_fav': m['stats']['favorites'],
                    'score_main': str(m['score'])[:-4] if m['score'] >= 10000 else m['score'],
                    'score_trivial': str(m['score'])[-4:] if m['score'] >= 10000 else '',
                    's1': m['lastRank'] if m['lastRank'] else '--',
                    's2': m['weeksOnBoard'] if m['weeksOnBoard'] else '--',
                    's3': m['peakRank'] if m['peakRank'] else '--',
                    's1t': '上周排名', 's2t': '在榜周数', 's3t': '最高排名',
                }) for index, m in enumerate(music_data,start=1)
            ]),
            'title': f'年榜 {issue['year']}年{sub_title[issue['week']]}',
            'bv': issue['video_bvid'],
            'all': 'https://vocaloid.p.kaphia.qzz.io/board3/index.json',
        })
        save_output_file(f'board3/issue_{issue['issue_id']}.xaml',output)
        save_output_file(f'board3/issue_{issue['issue_id']}.json',json.dumps({
            'Title': f'Vocaloid 术力口榜单 | 年榜 {issue['year']}年{sub_title[issue['week']]}'
        },ensure_ascii=False))
    
    print('b3issues-保存目录')
    save_output_file(f'board3/index.xaml',replaces(templates['indexpage'],{
        'title':'年榜',
        'item':''.join([
            replaces(templates['indexpage-item'],{
                'title': f'年榜 第{issue['issue_id']}期',
                'info': f'{issue['year']}年{sub_title[issue['week']]}',
                'url': f'https://vocaloid.p.kaphia.qzz.io/board3/issue_{issue['issue_id']}.json',
            })
            for issue in sorted(b3_issues, key=lambda x: int(x['issue_id']), reverse=True)
        ])
    }))
    save_output_file(f'board3/index.json',json.dumps({
        'Title': f'Vocaloid 术力口榜单 | 年榜列表'
    },ensure_ascii=False))

def init():
    print('init-初始化中')
    global OUTPUT_PATH, BASE_PATH, BUILD_VERSION, templates, test_environment, b1_issues, b2_issues, b3_issues
    templates = {}
    BUILD_VERSION = secrets.token_hex(4)
    BASE_PATH = os.path.dirname(__file__)
    OUTPUT_PATH = os.path.join(BASE_PATH,'output')
    print('init-获取周榜数据')
    b1_issues = requests.get('https://biliboard.uk/api/public/boards/1/issues').json()
    b1_issues = [{**i, 'issue_id':str(i['issue_id'])} for i in b1_issues]
    print('init-获取传说榜数据')
    b2_issues = requests.get('https://biliboard.uk/api/public/boards/2/issues').json()
    b2_issues = [{**i, 'issue_id':str(i['issue_id'])} for i in b2_issues]
    print('init-获取年榜数据')
    b3_issues = requests.get('https://biliboard.uk/api/public/boards/3/issues').json()
    b3_issues = [{**i, 'issue_id':str(i['issue_id'])} for i in b3_issues]
    shutil.rmtree(OUTPUT_PATH,ignore_errors=True)
    os.makedirs(OUTPUT_PATH,exist_ok=True)
    os.makedirs(os.path.join(BASE_PATH,'data'),exist_ok=True)
    os.makedirs(f'data/b1_issues', exist_ok=True)
    os.makedirs(f'data/b2_issues', exist_ok=True)
    os.makedirs(f'data/b3_issues', exist_ok=True)

    # test_environment = os.path.exists(os.path.join(BASE_PATH,'test_environment'))

    # if test_environment:
    #     from urllib3.exceptions import InsecureRequestWarning
    #     requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # type: ignore

    print('init-运行mainpage')
    mainpage()

    print('init-运行b1issues')
    b1issues()
    print('init-运行b2issues')
    b2issues()
    print('init-运行b3issues')
    b3issues()

init()