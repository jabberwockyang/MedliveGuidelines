import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import random
import string
import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


DOWNLOADPATH = 'download'

class Login(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        }
        self.login_url = 'https://www.medlive.cn/auth/login?service=https%3A%2F%2Fwww.medlive.cn%2F'
        self.post_url = 'https://www.medlive.cn/auth/login?service=https%3A%2F%2Fwww.medlive.cn%2F'
        self.session = requests.Session()
    
    def encrypt(self, word, key):
        iv = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        key = key.encode('utf-8')
        iv = iv.encode('utf-8')
        word = word.encode('utf-8')
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(word, AES.block_size))
        encrypted = base64.b64encode(iv + encrypted)
        return encrypted.decode('utf-8')
    
    def login(self, username, password):
        response = self.session.get(self.login_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        lt = soup.find('input', {'name': 'lt'}).get('value')
        key = soup.find('input', {'id': 'key'}).get('value')
        
        data = {
            "loginType": "password",
            "appName": "",
            "lt": lt,
            "execution": "e1s1",
            "_eventId": "submit",
            "username": username,
            "password": self.encrypt(password, key),
            "tel": "",
            "smsCode": "",
            "demo-checkbox1": "on",
            "rememberMe": "true",
            "loginsubmit": ""
        }
        
        response = self.session.post(self.post_url, data=data, headers=self.headers)
        
        if response.status_code == 200:
            print('登录成功!')
            # print(response.text)

    def download(self, url, file_name):
        file_name = file_name.replace('.pdf','') + '.pdf'
        response = self.session.get(url, headers=self.headers)
        with open(os.path.join(DOWNLOADPATH,file_name), 'wb') as f:
            f.write(response.content)

def download_freefile(login, url, file_name):
    login.download(url, file_name)


if __name__ == '__main__':
    login = Login()
    login.login('yourusername', 'yourpassword')
    repos = glob.glob('data/request.txt_durl.jsonl')
    print(repos)
    with ThreadPoolExecutor() as executor:
        futures = []
        for repo in repos:
            with open(repo, 'r') as f:
                for line in f:
                    row = json.loads(line)
                    url = row['download_url']
                    file_name = row['标题']
                    futures.append(executor.submit(download_freefile, login, url, file_name))

        for future in as_completed(futures):
            future.result()
