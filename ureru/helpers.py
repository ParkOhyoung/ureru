# -*- coding: utf-8 -*-

import io
import json
import re


def change_tag_for_bs4(s):
    return re.sub(r'(</*)(sync)', r'\1td', s, flags=re.I)


def ignore_some_stuff(s):
    return re.sub(r'(\s*\-+\s*|<br\s*\/*>|\&nbsp;*)', '\n', s, flags=re.I)


def make_sample(file_name, data):
    with io.open('utils/{}.js'.format(file_name), 'w', encoding='utf8') as js_file:
        data = json.dumps(to_dict_for_highchart(data), ensure_ascii=False)
        js_file.write(u'var {}_data='.format(file_name))
        js_file.write(data)
        js_file.write(u';')


def to_dict_for_highchart(time_series):
    def to_dict(caption):
        return {
            'x': caption.since,
            'y': caption.until - caption.since,
            'z': caption.until,
            'c': caption.sentence.replace('\n', '<br>')
        }
    results = []
    for key, captions in time_series.items():
        tmp_dictionary = {'name': key}
        tmp_dictionary['data'] = [to_dict(caption) for caption in captions]
        results.append(tmp_dictionary)
    return results
