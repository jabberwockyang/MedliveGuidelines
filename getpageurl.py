from threading import Thread
import pandas as pd
from DrissionPage import ChromiumOptions, ChromiumPage

# 初始化ChromiumOptions
co = ChromiumOptions()
# co.incognito()  # 匿名模式
# co.headless()  # 无头模式
# co.set_argument('--no-sandbox')  # 无沙盒模式
# co.no_imgs(True).mute(True)

def collect(tab):
    """用于采集的方法
    :param tab: ChromiumTab 对象
    :param result: 用于存储结果的列表
    :return: None
    """
    result = []
    while True:
        # 等待新数据加载完成
        tab.wait.ele_loaded(".guideList a:last-child", timeout=2)
        
        # 如果有"加载更多"按钮,点击翻页
        load_more_button = tab(".guideMore", timeout=2)
        if load_more_button and load_more_button.style('display')!='none':
            tab.scroll.to_see(load_more_button)
            # 等待"加载更多"按钮可用
            load_more_button.wait.enabled(timeout=2)
            # 点击"加载更多"按钮
            load_more_button.click()
        # 否则,采集完毕
        # elif tab(".noMore").style('display')!='none':
        #     break
        else:
            break
    
    # 解析页面,提取所需的数据
    a_list = tab.eles('xpath='+".//div[@class ='guideList']//a", timeout=2)
    titles = tab.eles('xpath='+'.//div[@class ="guideList"]//a//div[contains(@class,"guideTitle")]', timeout=2)
    sources = tab.eles('xpath='+".//div[@class ='guideList']//a//div[contains(@class,'guideLine2')]", timeout=2)
    download_methods = tab.eles('xpath='+".//div[@class ='guideList']//a//div[contains(@class,'guideBtmLabels')]", timeout=2)
    
    result = pd.DataFrame({
        '标题': [title.text for title in titles],
        '来源': [source.text for source in sources],
        '下载方式': [download_method.text for download_method in download_methods],
        '链接': [a.link for a in a_list]
    })
    return result

def main():
    # 新建页面对象

    for year in range(2018, 2022):
        # 访问目标页面
        page = ChromiumPage(co)
        page.get(f"https://guide.medlive.cn/guide/filter?sub_type=1&category=0&category_sec=0&year={year}&cn_flg=0")
        collocted_data = collect(page)
        collocted_data.to_csv(f"guides_{year}.csv", index=False)
        page.close()

if __name__ == '__main__':
    main()