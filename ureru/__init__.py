# -*- coding: utf-8 -*-
import argparse
from bisect import bisect_left
from collections import defaultdict, namedtuple
from functools import partial
import itertools
from operator import itemgetter
import re
import sys

from bs4 import BeautifulSoup, SoupStrainer

VERSION = sys.version_info.major
if VERSION == 2:
    map = itertools.imap
    zip = itertools.izip


_change_tag_for_bs4 = lambda s: re.sub(r'(</*)(sync)',
                                       r'\1td',
                                       s,
                                       flags=re.I)
_ignore_some_stuff = lambda s: re.sub(r'(\s*\-+\s*|<br\s*\/*>|\&nbsp;*)',
                                      '\n',
                                      s,
                                      flags=re.I)
Caption = namedtuple('Caption', 'since, until, sentence')
Caption.__new__ = partial(Caption.__new__, until=None)


def to_string(caption):
    return '{c.since}>{c.until} : {c.sentence}\n\n'.format(c=caption)


def make_time_series(sami):
    """
    >>> input = u'''<BODY>
    ...    <SYNC Start=100>
    ...        <P Class=KRCC>가나다
    ...        <P Class=JPCC>あかさ
    ...    <SYNC Start=250>
    ...        <P Class=KRCC>라마바
    ...        <P Class=JPCC>たなは
    ...    <SYNC Start=800>
    ...        <P Class=KRCC>&nbsp;
    ...        <P Class=JPCC>&nbsp;
    ...    <SYNC Start=1600>
    ...        <P Class=KRCC>사아자
    ...        <P Class=JPCC>まやら
    ...    <SYNC Start=2000>
    ...        <P Class=KRCC>차
    ...        <P Class=JPCC>わ
    ...    <SYNC Start=80>
    ...        <P Class=ENCC>ABC
    ...    <SYNC Start=200>
    ...        <P Class=ENCC>DEF
    ...    <SYNC Start=1800>
    ...        <P Class=ENCC>JKL
    ...    <SYNC Start=5000>
    ...        <P Class=ENCC>M
    ... </BODY>'''
    >>> expected = {'ENCC': [Caption(since=80, until=None, sentence=u'ABC'),
    ...                      Caption(since=200, until=None, sentence=u'DEF'),
    ...                      Caption(since=1800, until=None, sentence=u'JKL'),
    ...                      Caption(since=5000, until=None, sentence=u'M'),
    ...                      Caption(since=10000, until=None, sentence=u'')],
    ...             'JPCC': [Caption(since=100, until=None, sentence=u'あかさ'),
    ...                      Caption(since=250, until=None, sentence=u'たなは'),
    ...                      Caption(since=800, until=None, sentence=u''),
    ...                      Caption(since=1600, until=None, sentence=u'まやら'),
    ...                      Caption(since=2000, until=None, sentence=u'わ'),
    ...                      Caption(since=7000, until=None, sentence=u'')],
    ...             'KRCC': [Caption(since=100, until=None, sentence=u'가나다'),
    ...                      Caption(since=250, until=None, sentence=u'라마바'),
    ...                      Caption(since=800, until=None, sentence=u''),
    ...                      Caption(since=1600, until=None, sentence=u'사아자'),
    ...                      Caption(since=2000, until=None, sentence=u'차'),
    ...                      Caption(since=7000, until=None, sentence=u'')]}
    >>> sorted(make_time_series(input).items()) == sorted(expected.items())
    True
    """
    def _normal_case(td):
        for p in td.select('p'):
            yield p['class'][0], p.text.strip()

    td_tags = SoupStrainer("td")
    td_soup = BeautifulSoup(salt(sami), "lxml", parse_only=td_tags)

    subtitles = defaultdict(list)
    for td in td_soup:
        start = int(td['start'])
        for class_, sentence in _normal_case(td):
            subtitles[class_].append(Caption(since=start, sentence=sentence))
    for class_ in subtitles.keys():
        subtitles[class_].append(Caption(since=subtitles[class_][-1].since + 5000, sentence=''))
    return subtitles


def salt(sami):
    like_html = _change_tag_for_bs4(sami)
    return _ignore_some_stuff(like_html)


def fill_until(multiful_time_series):
    return {key: _fill_until(values) for key, values in multiful_time_series.items()}


def _fill_until(time_series):
    """
    >>> input_ = [Caption(since=100, until=None, sentence='가나다'),
    ...           Caption(since=250, until=None, sentence='라마바'),
    ...           Caption(since=800, until=None, sentence=''),
    ...           Caption(since=1600, until=None, sentence='사아자'),
    ...           Caption(since=2000, until=None, sentence='차'),
    ...           Caption(since=7000, until=None, sentence='')]
    >>> expected = iter((Caption(since=100, until=250, sentence='가나다'),
    ...             Caption(since=250, until=800, sentence='라마바'),
    ...             Caption(since=1600, until=2000, sentence='사아자'),
    ...             Caption(since=2000, until=7000, sentence='차')))
    >>> tuple(_fill_until(input_)) == tuple(expected)
    True
    """
    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    def generate(iterable):
        for s, u in pairwise(iterable):
            if not s.sentence:
                continue
            yield Caption(since=s.since, until=u.since, sentence=s.sentence)
    return generate(time_series)


def sync(multiful_time_series, base_class='ENCC'):
    """
    >>> serize = lambda x: {key: list(values) for key, values in x.items()}
    >>> input_ = {'ENCC': iter([Caption(since=80, until=200, sentence='ABC'),
    ...                         Caption(since=200, until=1800, sentence='DEF'),
    ...                         Caption(since=1800, until=5000, sentence='JKL'),
    ...                         Caption(since=5000, until=10000, sentence='M')]),
    ...           'JPCC': iter([Caption(since=100, until=250, sentence='あかさ'),
    ...                         Caption(since=250, until=800, sentence='たなは'),
    ...                         Caption(since=1600, until=2000, sentence='まやら'),
    ...                         Caption(since=2000, until=7000, sentence='わ')]),
    ...           'KRCC': iter([Caption(since=100, until=250, sentence='가나다'),
    ...                         Caption(since=250, until=800, sentence='라마바'),
    ...                         Caption(since=1600, until=2000, sentence='사아자'),
    ...                         Caption(since=2000, until=7000, sentence='차')])}
    >>> expected = {'ENCC': iter([Caption(since=100, until=250, sentence='ABC'),
    ...                           Caption(since=250, until=800, sentence='DEF'),
    ...                           Caption(since=1600, until=2000, sentence='JKL'),
    ...                           Caption(since=2000, until=7000, sentence='M')]),
    ...             'JPCC': iter([Caption(since=100, until=250, sentence='あかさ'),
    ...                           Caption(since=250, until=800, sentence='たなは'),
    ...                           Caption(since=1600, until=2000, sentence='まやら'),
    ...                           Caption(since=2000, until=7000, sentence='わ')]),
    ...             'KRCC': iter([Caption(since=100, until=250, sentence='가나다'),
    ...                           Caption(since=250, until=800, sentence='라마바'),
    ...                           Caption(since=1600, until=2000, sentence='사아자'),
    ...                           Caption(since=2000, until=7000, sentence='차')])}
    >>> serize(sync(input_, 'KRCC')) == serize(expected)
    True
    """
    def get_time_gap(timestamp, of_time_series):
        _bisect_left = partial(bisect_left, of_time_series, lo=1, hi=max_index)
        position = _bisect_left(timestamp)
        before = abs(timestamp - of_time_series[position - 1])
        after = abs(timestamp - of_time_series[position])
        if before <= after:
            return position - 1, before
        return position, after

    def get_near_positions(since, until):
        since_position, since_gap = get_time_gap(since, since_of_time_series)
        until_position, until_gap = get_time_gap(until, until_of_time_series)
        position = since_position if since_gap <= until_gap else until_position
        return {'since': since_of_time_series[position],
                'until': until_of_time_series[position]}

    def classify_since_and_until(captions):
        return zip(*((caption.since, caption.until) for caption in captions))

    results = {}
    results[base_class], base_time_series = itertools.tee(multiful_time_series[base_class])
    since_of_time_series, until_of_time_series = classify_since_and_until(base_time_series)
    max_index = len(since_of_time_series) - 1
    targets = {key: value for key, value in multiful_time_series.items() if key != base_class}

    for target_class, target_time_series in targets.items():
        results[target_class] = (Caption(sentence=caption.sentence, **get_near_positions(caption.since, caption.until)) for caption in target_time_series)

    return results


def merge(multiful_time_series):
    '''
    >>> input_ = {'ENCC': iter([Caption(since=100, until=250, sentence='ABC'),
    ...                         Caption(since=250, until=800, sentence='DEF'),
    ...                         Caption(since=1600, until=2000, sentence='JKL'),
    ...                         Caption(since=2000, until=7000, sentence='M')]),
    ...           'JPCC': iter([Caption(since=100, until=250, sentence='あかさ'),
    ...                         Caption(since=250, until=800, sentence='たなは'),
    ...                         Caption(since=1600, until=2000, sentence='まやら'),
    ...                         Caption(since=2000, until=7000, sentence='わ')]),
    ...           'KRCC': iter([Caption(since=100, until=250, sentence='가나다'),
    ...                         Caption(since=250, until=800, sentence='라마바'),
    ...                         Caption(since=1600, until=2000, sentence='사아자'),
    ...                         Caption(since=2000, until=7000, sentence='차')])}
    >>> expected = iter((Caption(since=100, until=250, sentence='ABC\\nあかさ\\n가나다'),
    ...                  Caption(since=250, until=800, sentence='DEF\\nたなは\\n라마바'),
    ...                  Caption(since=1600, until=2000, sentence='JKL\\nまやら\\n사아자'),
    ...                  Caption(since=2000, until=7000, sentence='M\\nわ\\n차')))
    >>> tuple(merge(input_)) == tuple(expected)
    True
    '''
    def generate(iterable):
        for (since, until), items in iterable:
            yield Caption(since=since,
                          until=until,
                          sentence="\n".join(item[2] for item in items))

    def sort_for_groupby(multiful_time_series):
        caption_with_class = (zip(itertools.repeat(class_), captions) for class_, captions in multiful_time_series.items())
        merged_captions = itertools.chain.from_iterable(caption_with_class)
        sorted_captions = sorted(merged_captions, key=lambda x: (x[1][0], x[0]))
        return (caption for class_, caption in sorted_captions)

    time_series = sort_for_groupby(multiful_time_series)
    time_series_group = itertools.groupby(time_series, itemgetter(0, 1))
    return generate(time_series_group)


def generate(opened_files, target_file):
    time_series = []
    for f in opened_files:
        smi = f.read()
        time_series.extend(make_time_series(smi).items())
        f.close()
    multiful_time_series = dict(time_series)
    time_series_with_until = fill_until(multiful_time_series)
    syncd_time_series = sync(time_series_with_until)
    merged_time_series = merge(syncd_time_series)
    if not target_file:
        return merged_time_series
    for caption in merged_time_series:
        target_file.write(to_string(caption))
    target_file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync subtitles.')
    parser.add_argument('files', nargs='*', type=argparse.FileType())
    parser.add_argument('--test', action='store_true', help='Run doctests.')
    parser.add_argument('--out', type=argparse.FileType('w', encoding='utf-8'))
    args = parser.parse_args()
    if args.test:
        import doctest
        print('testing...')
        doctest.testmod()
    else:
        print(generate(args.files, args.out))
