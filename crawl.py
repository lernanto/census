#!/usr/bin/python3 -O
# -*- encoding: utf-8 -*-

'''爬取国家统计局人口普查数据.'''

__author__ = 'Edward Wong <lernanto.wong@gmail.com>'


import sys
import logging
import configparser
import os
import requests
import lxml.etree
import re
import time


def process(node, directory, url_prefix, dry_run=False, delay=None):
    '''递归地处理网页目录中的章节列表，并下载数据.'''

    # 先创建本目录
    logging.info('make directory {}'.format(directory))
    if not dry_run:
        os.makedirs(directory, exist_ok=True)

    # 递归处理子目录
    title = '未命名'
    for c in node.getchildren():
        anchors = c.xpath('.//a')
        if len(anchors) == 0:
            # 不含超链接，可能是章节标题
            text = re.sub(r'[:/\\?.\s]+', ' ', ''.join(c.itertext())).strip()
            if text:
                title = text

        elif len(anchors) == 1:
            # 含有一个超链接，叶节点，下载
            href = anchors[0].get('href')
            if href:
                url = '{}/{}'.format(url_prefix, href)

                # 标题，尽量提取章节标题，如果没有，使用链接文件名
                text = re.sub(r'[:/\\?.\s]+', ' ', anchors[0].text).strip()
                if text:
                    _, ext = os.path.splitext(href)
                    if not ext:
                        ext = 'xls'
                    fname = '{}{}'.format(text, ext)
                else:
                    fname = href.split('/')[-1]

                path = os.path.join(directory, fname)
                # TODO: 异常情况下可能出现新文件和已有文件重名，暂不处理

                logging.info('download {} -> {}'.format(url, path))
                if not dry_run:
                    rsp = requests.get(url)
                    if rsp.status_code == 200:
                        with open(path, 'wb') as f:
                            for chunk in rsp.iter_content(chunk_size=512):
                                f.write(chunk)
                    else:
                        logging.error('{}: {}'.format(rsp.status_code, rsp.reason))

                    # 必要时延迟一段时间，减轻网站压力
                    if delay > 0:
                        time.sleep(delay)

        else:
            # 含有多个超链接，子目录，递归处理
            process(c, os.path.join(directory, title), url_prefix, dry_run, delay)


logging.getLogger().setLevel(logging.INFO)

config = configparser.ConfigParser()
config.read_string('[DEFAULT]\n' + open(sys.argv[1], encoding='utf8').read())
config = config['DEFAULT']

for k, v in config.items():
    logging.info('{} = {}'.format(k, v))

url = config.get('url')
xpath = config.get('xpath')
encoding = config.get('encoding', 'GB18030')
output = config.get('output', '.')
dry_run = config.getboolean('dry_run', False)
delay = config.getfloat('delay')

if not url or not xpath:
    logging.error('must set url and xpath')
    sys.exit(1)

url_prefix = '/'.join(url.split('/')[:-1])

logging.info('start crawling {}'.format(url))

rsp = requests.get(url)
rsp.encoding = encoding
doc = lxml.etree.HTML(rsp.text)
root = doc.xpath(xpath)[0]

process(root, output, url_prefix, dry_run=dry_run, delay=delay)
logging.info('done')