import re
import os
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import glob
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import json
from queue import Queue
from fuzzywuzzy import process

class PoisonPill:
    pass

def parse_download_params(onclick):
    if onclick is None:
        return None
    if not isinstance(onclick, (str, bytes)):
        return None
    pattern = r'download_info\("(.*?)",\s*"(.*?)",\s*"(.*?)"\)'
    match = re.search(pattern, onclick)
    if match:
        file_id = match.group(1)
        file_name = match.group(2)
        token = match.group(3)
        # 对文件名进行 URL 编码,以处理特殊字符
        file_name = quote(file_name)
        return file_id, file_name, token
    else:
        return None

def collect(url):
    """用于采集的方法
    :param url: 页面的 URL
    :param pageid: 页面的 ID
    :return: 下载链接,如果没有找到则返回 None
    """
    pageid = url.split('/')[-1]
    # response = requests.get(url)
    try:
        response = requests.get(url)
        print (f"请求成功: {url}")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        download_button = soup.select_one(".sideBtn.downLoad")
        if download_button:
            onclick = download_button.get('onclick')
            params = parse_download_params(onclick)
            if params:
                file_id, file_name, token = params
                download_url = f"https://guide.medlive.cn/guide/download?id={pageid}&sub_type=1&fid={file_id}&fn={file_name}&sk={token}"
                return download_url
            else:
                print(f"解析下载参数失败: {url}")
                return None
        else:
            print(f"没有找到下载按钮: {url}")
            return None
        
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print(f"请求失败: {url}, 错误: {str(e)}")
        return None


def process_row(filename, row, queue):
    url = row['链接']
    new_row = row.copy()
    new_row['download_url'] =collect(url)

    new_row = new_row.to_json()
    new_row = json.loads(new_row)
    new_row = json.dumps(new_row, ensure_ascii=False)
    queue.put((filename, new_row))

def write_to_file(queue):
    while True:
        filename, new_row = queue.get(timeout=1)

        if isinstance(filename, PoisonPill):
            queue.task_done()
            break
        
        filename = filename.split('.')[0]
        with open(f'{filename}_durl.jsonl', 'a') as f:
            f.write(new_row + '\n')
        print(f"写入文件: {filename}_durl.jsonl")
        queue.task_done()
        

def getdownloadurl(retriveddflist):
    
    queue = Queue()
    
    with ThreadPoolExecutor() as executor:
        writer_thread = executor.submit(write_to_file, queue)
        
        for filename, retriveddf in retriveddflist:
            futures = []
            for index, row in retriveddf.iterrows():
                future = executor.submit(process_row, filename, row, queue)
                futures.append(future)
            for future in futures:
                future.result()

        queue.put((PoisonPill(), PoisonPill()))
        
        queue.join()
        writer_thread.result()

def retrieval(repopath, requestpath, keywords:list = None):
    '''
    repopath: str, path to the repository of guides
    requestpath: str, path to the request files
    keywords: list, list of keywords to filter the download methods
    '''
    files = glob.glob(os.path.join(requestpath, '*request.txt')) # 这里根据需要修改正则以匹配文件
    repos = glob.glob(os.path.join(repopath, 'guides_*.csv')) # 这里根据需要修改正则以匹配文件

    repodflist = [pd.read_csv(repo) for repo in repos]
    repodf = pd.concat(repodflist)

    retriveddflist =[]
    for file in files:
        with open(file, 'r') as f:
            queries = f.readlines()
        queries = [query.strip() for query in queries]  
        retrieved = []
        for query in queries:
            best_match = process.extractOne(query, repodf['标题'])
            match_title, score = best_match[0], best_match[1]
            match_url = repodf[repodf['标题'] == match_title]['链接'].values[0]
            match_downloadmethod = repodf[repodf['标题'] == match_title]['下载方式'].values[0]
            retrieved.append((query, match_title, score, match_url, match_downloadmethod))

        retrieved_df = pd.DataFrame(retrieved, columns=['请求', '标题', '相似度', '链接', '下载方式'])
        
        if keywords:
            regex_pattern = '|'.join(keywords)
            retrieved_df = retrieved_df[retrieved_df['下载方式'].str.contains(regex_pattern, na=False)]
        
        retriveddflist.append((file,retrieved_df))
    return retriveddflist


 

if __name__ == '__main__':
    retriveddflist = retrieval('data', 'data', keywords = ['站内免费下载']) # keywords =  ['站内VIP下载', '会员可通过APP阅读', '第三方数据库下载']
    getdownloadurl(retriveddflist)