# -*- coding: utf-8 -*-

import io
import itertools
import json
import re
import sys

change_tag_for_bs4 = lambda s: re.sub(r'(</*)(sync)',
                                      r'\1td',
                                      s,
                                      flags=re.I)


ignore_some_stuff = lambda s: re.sub(r'(\s*\-+\s*|<br\s*\/*>|\&nbsp;*)',
                                     '\n',
                                     s,
                                     flags=re.I)


def _accumulate(iterator):
    total = 0
    for item in iterator:
        total += item
        yield total


VERSION = sys.version_info.major
if VERSION == 2:
    itertools.accumulate = _accumulate


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
        accumulates = itertools.accumulate((c.since for c in c1))
        tmp_dictionary = {'name': key}
        tmp_dictionary['data'] = [to_dict(accu, caption) for (accu, caption) in zip(accumulates, c2)]
        results.append(tmp_dictionary)
    return results


def to_string(caption):
    return '{c.since}>{c.until} : {c.sentence}\n\n'.format(c=caption)
