#!/usr/bin/python3 -O
# -*- encoding: utf-8 -*-

'''爬取国家统计局人口普查数据.'''

__author__ = 'Edward Wong <lernanto.wong@gmail.com>'


import logging
import os
import requests
import lxml.etree
import time


def process(node, directory, url_prefix, delay=None):
    '''递归地处理网页中地章节列表，并下载数据.'''

    # 先创建本目录
    logging.info('make directory {}'.format(directory))
    os.makedirs(directory, exist_ok=True)

    # 递归处理子目录
    title = '未命名'
    for c in node.getchildren():
        if c.tag == 'li':
            anchors = c.xpath('a')
            if len(anchors) > 0:
                # 含有超链接的是叶节点，下载
                href = anchors[0].get('href')
                if href:
                    url = '{}/{}'.format(url_prefix, href)

                    # 标题
                    title = anchors[0].text.strip()
                    if title:
                        _, ext = os.path.splitext(href)
                        if not ext:
                            ext = 'xsl'
                        fname = '{}{}'.format(title, ext)
                    else:
                        fname = href.split('/')[-1]

                    path = os.path.join(directory, fname)
                    # TODO: 异常情况下可能出现新文件和已有文件重名，暂不处理

                    logging.info('download {} -> {}'.format(url, path))
                    rsp = requests.get(url)
                    if rsp.status_code == 200:
                        with open(path, 'wb') as f:
                            f.write(rsp.raw.data)
                    else:
                        logging.error('{}: {}'.format(rsp.status_code, rsp.reason))

                    # 必要时延迟一段时间，减轻网站压力
                    if delay > 0:
                        time.sleep(delay)

            else:
                # 非叶节点，章节标题
                title = c.text.strip()

        elif c.tag == 'ul':
            # 子目录
            process(c, os.path.join(directory, title), url_prefix, delay)


url = 'http://www.stats.gov.cn/tjsj/pcsj/rkpc/6rp/lefte.htm'
directory = '中国2010年人口普查资料'
url_prefix = '/'.join(url.split('/')[:-1])

logging.getLogger().setLevel(logging.INFO)
logging.info('start crawling {}'.format(url))

rsp = requests.get(url)
rsp.encoding = 'GB18030'
doc = lxml.etree.HTML(rsp.text)
root = doc.xpath('//table/tbody/center/tr[last()]/th/ul')[0]

process(root, directory, url_prefix, 0.1)
logging.info('done')