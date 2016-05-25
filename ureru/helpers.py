# -*- coding: utf-8 -*-

import io
import itertools
import json
import re

try:
    _accumulate = itertools.accumulate
except AttributeError:
    def _accumulate(iterator):
        total = 0
        for item in iterator:
            total += item
            yield total


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
    def to_dict(accu, caption):
        return {
            'x': caption.since,
            'y': accu,
            'z': caption.until,
            'c': caption.sentence.replace('\n', '<br>')
        }
    results = []
    for key, captions in time_series.items():
        c1, c2 = itertools.tee(captions)
        accumulates = _accumulate((c.since for c in c1))
        tmp_dictionary = {'name': key}
        tmp_dictionary['data'] = [to_dict(accu, caption) for (accu, caption) in zip(accumulates, c2)]
        results.append(tmp_dictionary)
    return results
