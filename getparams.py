import json
import urllib.parse
import base64
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime


def extract_params_from_xml(xml_file):
    # 解析 XML 文件
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # 存储提取的参数
    params_list = []

    # 遍历 XML 树，提取 GET 和 POST 参数
    for item in root.findall('.//item'):
        request = item.find('request').text
        if request:
            # 提取 GET 参数
            method = item.find('method').text
            if method == 'GET':
                # /Api/User/UserSetting.ashx?action=userload&uname=admin&pw=admin123
                url_path = item.find('path').text
                # 包含?，但是不含.js .css
                if '?' in url_path and not any(ext in url_path for ext in ['.js?', '.css?']):
                    params = url_path.split('?')[-1]
                    params_list.append(params)
                    # print('GET--',params)
                else:
                    # 无参数get请求
                    pass

            # 提取 POST 参数
            elif method == 'POST':
                decoded_bytes_request = base64.b64decode(request.strip())
                try:
                    decoded_string_request = decoded_bytes_request.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_string_request = decoded_bytes_request.decode('utf-8', errors='ignore')

                if 'Content-Type: application/json' in decoded_string_request:
                    # json字符串
                    params_all = decoded_string_request.strip().split('\r\n\r\n')[-1]
                    params_json = json.loads(params_all)
                    try:
                        # 转化为url编码的字符串
                        params = urllib.parse.urlencode(params_json)
                    except Exception as e:
                        continue
                    # 避免提取出错，造成脏数据
                    if 'User-Agent:' in params and 'Host:' in params:
                        continue
                    params_list.append(params.strip())
                    # print(params)


                elif 'Content-Type: application/x-www-form-urlencoded' in decoded_string_request:
                    params = decoded_string_request.strip().split('\r\n\r\n')[-1]
                    # 避免提取出错，造成脏数据
                    if 'User-Agent:' in params and 'Host:' in params:
                        continue

                    params_list.append(params)
                    # print('POST--',params)
                # exit()
            else:
                pass

    return params_list


def process_parameters(query_string):
    # 解析查询字符串为键值对列表
    params = urllib.parse.parse_qsl(query_string, keep_blank_values=True)

    # 使用字典去重并保留第一个值，并且去重长度超500的值
    unique_params = {}
    for key, value in params:
        if key not in unique_params and len(value) < 500:
            unique_params[key] = value

    # 将字典转换回查询字符串
    result_query_string = urllib.parse.urlencode(unique_params)

    return result_query_string


def url_to_json(params_url_tostring):
    parsed_query = urllib.parse.parse_qs(params_url_tostring)
    json_data = {key: value[0] if len(value) == 1 else value for key, value in parsed_query.items()}
    # 将字典转换为 JSON 字符串
    json_string = json.dumps(json_data, indent=4)
    return json_string


def main():
    parser = argparse.ArgumentParser(description='python getparams.py -f target.xml')
    parser.add_argument('-f', '--file', type=str, help='目标url文件')
    args = parser.parse_args()

    if not args.file or '.xml' not in args.file:
        exit('请检查参数-f，且目标文件是xml格式')

    xml_file = args.file
    params_list = extract_params_from_xml(xml_file)

    # 输出提取的参数
    query_string = '&'.join(params_list)
    params_url_encode = process_parameters(query_string)
    params_json_encode = url_to_json(params_url_encode)
    # print(params_url_encode)
    # print(params_json_encode)

    current_datetime = datetime.now().strftime("%Y%m%d")
    out_file_name = xml_file  + '_' + str(current_datetime) + '.txt'
    with open(out_file_name,'a+',encoding='utf-8') as fpp:
        fpp.write(params_url_encode)
        fpp.write('\n\n')
        fpp.write(params_json_encode)
        print(params_url_encode)
        print('\n\n')
        print(params_json_encode)


if __name__ == '__main__':
    main()
