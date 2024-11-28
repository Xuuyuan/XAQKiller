import json
import re
import requests


my_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36',
              'Content-Type': 'application/json',
              'Referer': 'https://ningde.xueanquan.com/MainPage.html'}


def finish_activity(ss, special_id, step):
    payload_n = {'specialId': int(special_id.groups()[0]), 'step': step}
    pr = ss.post('https://huodongapi.xueanquan.com/p/fujian/Topic/topic/platformapi/api/v1/records/sign', data=json.dumps(payload_n), headers=my_headers)
    prj = json.loads(pr.text)
    return prj['msg']


def surl_to_id(ss, url):
    gr = ss.get(url)
    ru = re.search(r".*(?=index.html)", url).group()
    ru += re.search(r"(?<=replace\(').*(?=')", gr.text).group()
    gr2 = ss.get(ru)
    gri = re.search(r'(?<=data-specialId=")(.+?)(?=(\"))', gr2.text)
    if gri is None:
        gri = re.search(r'(?<=data-specialId\s=")(.+?)(?=(\"))', gr2.text)
    return gri


def finish_work(ss, cid: str, wid, fid: int):
    payload_n = {'contents': '',
                 'courseID': cid,
                 'fid': fid,
                 'purpose': '',
                 'require': '',
                 'siteAddrees': '',
                 'siteName': '',
                 'testMark': 100,
                 'testResult': 1,
                 'testanswer': '0|0|0',
                 'testinfo': '已掌握技能',
                 'workId': wid,
                 }
    pr = ss.post('https://yyapi.xueanquan.com/fujian/api/v1/StudentHomeWork/HomeWorkSign', data=json.dumps(payload_n), headers=my_headers)
    prj = json.loads(pr.text)
    return prj['message']


def login(ss):
    account = input('请输入您的 安全教育平台 账号:')
    password = input('请输入您的 安全教育平台 密码:')
    payload = {'username': account, 'password': password}
    sl = ss.post('https://appapi.xueanquan.com/usercenter/api/v3/wx/login?checkShowQrCode=true&tmp=false', data=json.dumps(payload), headers=my_headers)
    return json.loads(sl.text)


def main():
    stu_session = requests.session()
    LoginInfo = login(stu_session)
    while LoginInfo['data'] is None:
        print(LoginInfo['err_desc'])
        LoginInfo = login(stu_session)
    login_end = stu_session.get('https://ningde.xueanquan.com/LoginHandler.ashx', headers=my_headers)
    ReferInfo = json.loads(login_end.text)
    print('登录成功.. 学生信息：', ReferInfo['UInfo']['SchoolName'], ReferInfo['UInfo']['TrueName'])
    # 获取任务列表
    work_list = stu_session.get('https://yyapi.xueanquan.com/fujian/safeapph5/api/v1/homework/homeworklist')
    print('任务列表获取：')
    work_list_json = json.loads(work_list.text)
    for n in work_list_json:
        n['title'] = n['title'][:-1] if n['title'][-1] == '	' else n['title']
        print(f"【{n['subTitle']}】 {n['title']} {n['workStatus']} {n['url']}")
    print('开始执行任务..')
    for n in work_list_json:
        if n['workStatus'] == 'UnFinish':
            if n['sort'] == 'Special':  # 专题任务
                SpecialId = surl_to_id(stu_session, n['url'])
                print('【' + n['sort'] + '】', n['title'], finish_activity(stu_session, SpecialId, 1), finish_activity(stu_session, SpecialId, 2), finish_activity(stu_session, SpecialId, 3))
            elif n['sort'] == 'Skill':  # 学习技能
                CourseId = re.search('(?<=li=).[0-9]+', n['url']).group()
                GId = re.search('(?<=gid=).[0-9]+', n['url']).group()
                stu_session.get('https://yyapi.xueanquan.com/fujian/JiaTing/CommonHandler/info?api-version=1&contentId=0&courseId=' + CourseId + '&gradeId=' + GId)  # 防止出现 请先观看视频Tips
                ReturnWork = stu_session.get('https://yyapi.xueanquan.com/fujian/api/v1/StudentHomeWork/GetSkillTestPaper?courseId=' + CourseId, headers=my_headers)
                ReturnWorkJson = json.loads(ReturnWork.text)
                Wid = ReturnWorkJson['result']['workId']
                Fid = ReturnWorkJson['result']['fid']
                print(f"【{n['sort']}】 {n['title']} {finish_work(stu_session, CourseId, Wid, Fid)} fid:{Fid} workid:{Wid} gid:{GId} courseid:{CourseId}")
            else:
                print('【' + n['subTitle'] + '】', n['title'], n['sort'], '暂不支持自动完成本类任务！')
    print('任务执行完毕！')


if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print('程序异常！', e)
