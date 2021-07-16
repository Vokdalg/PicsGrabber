import requests
import datetime
import json
import dpath.util
import os
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
import io
from dotenv import load_dotenv
from tqdm import tqdm
from time import sleep
from pprint import pprint

load_dotenv()


# class GDUploader:
#
#     def gd_folder_maker(self, url_dict):
#         dir_name = input('Введите имя папки, которую хотите создать на своем Google Drive:\n')
#         scopes = ['https://www.googleapis.com/auth/drive']
#         credentials = service_account.Credentials.from_service_account_file(
#             MainMenu.service_account_file, scopes=scopes)
#         service = build('drive', 'v3', credentials=credentials)
#
#         folder_id = '1JKG3skCRR8xdzA26mzrX7r6NkwZAsb5E'
#         file_metadata = {
#             'name': dir_name,
#             'mimeType': 'application/vnd.google-apps.folder',
#             'parents': [folder_id]
#         }
#         response = service.files().create(body=file_metadata, fields='id').execute()
#         for id, number in response.items():
#             dir_name = number
#         self.gd_upload(dir_name, url_dict)
#
#     def gd_upload(self, dir_name, url_dict):
#         print(dir_name)
#         scopes = ['https://www.googleapis.com/auth/drive']
#         credentials = service_account.Credentials.from_service_account_file(
#             MainMenu.service_account_file, scopes=scopes)
#         service = build('drive', 'v3', credentials=credentials)
#         for filename, url in tqdm(url_dict.items(), desc='Photos uploading'):
#             sleep(.1)
#             file_path = url
#             file_metadata = {
#                 'name': filename,
#                 'parents': [dir_name]
#             }
#             media = MediaFileUpload(file_path, resumable=True)
#             r = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
#             pprint(r)


class VKGrabber:

    def grab_vk(self):
        user_id = input('Введите ID пользователя, фотографии которого вы хотите импортировать:\n')
        album = input(
            'Введите название альбома (wall, profile или saved), фотографии из которого вы хотите импортировать.\n')
        count = input('Укажите максимальное число фотографий (не более 1000), которых нужно импортировать:\n')
        params = {
            'user_id': user_id,
            'access_token': MainMenu.vk_token,
            'v': MainMenu.api_vk_version,
            'extended': '1',
            'album_id': album,
            'photo_sizes': '1',
            'count': count
        }

        try:
            imported_json = requests.get(MainMenu.url_vk + 'photos.get', params=params)
            imported_json = imported_json.json()

            if int(dpath.util.get(imported_json, "response/count")) == 0:
                print('Фотографий в указанном альбоме не обнаружено!\n')
                return
            else:
                print(
                    f'Всего в профиле указанного пользователя обнаружено {dpath.util.get(imported_json, "response/count")} фото.\n')
                print('Начинаю граббинг фото!\n')

                result_json = []
                list_of_filenames = []
                list_of_sizes = ['w', 'z', 'y', 'x', 'm', 's']
                for photo in tqdm(dpath.util.get(imported_json, 'response/items'), desc='Photos grabbing'):
                    sleep(.1)
                    finder_status = False
                    for letter in list_of_sizes:
                        for size in photo['sizes']:
                            if dpath.util.get(size, 'type') == letter:
                                file_name = str(dpath.util.get(photo['likes'], 'count')) + '.jpg'
                                if file_name in list_of_filenames:
                                    file_name = str(dpath.util.get(photo['likes'], 'count')) + '_' + str(
                                        datetime.date.today()) + '.jpg'
                                if finder_status:
                                    continue
                                list_of_filenames.append(file_name)
                                MainMenu.url_dict[file_name] = dpath.util.get(size, 'url')
                                name_dict = {
                                    'file_name': file_name,
                                    'size': letter
                                }
                                result_json.append(name_dict)
                                finder_status = True

                result_file = open('result.json', 'w+', encoding='utf-8')
                json.dump(result_json, result_file, ensure_ascii=False, indent=4)
                result_file.close()
                print('Отчет о загруженных фотографияк сформирован в файл result.json')
                print()

                MainMenu.choose_resource_for_export(self)
                return

        except KeyError:
            print(
                'Произошла ошибка. Возможно профиль или альбом закрыт настройками приватности или альбома не существует. '
                'Проверьте правильность написания альбома и его доступность из вашего профиля.\n')
            return


class YandexUploader:

    def yd_folder_maker(self):
        MainMenu.dir_name = input('Введите имя папки, которую хотите создать на своем Яндекс Диске:\n')
        params = {'path': MainMenu.dir_name}
        headers = {'Content-Type': 'application/json', 'Authorization': 'OAuth {}'.format(MainMenu.yandex_token)}
        response = requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers=headers, params=params)
        if response.status_code != 201:
            print(
                f'Упс, произошла ошибка: {response.status_code}. Проверьте, возможно папка с таким названием уже существует.\n')
        else:
            YandexUploader.yd_upload(self)

    def yd_upload(self):
        path = MainMenu.dir_name + '/'
        headers = {'Content-Type': 'application/json', 'Authorization': 'OAuth {}'.format(MainMenu.yandex_token)}
        for filename, url in tqdm(MainMenu.url_dict.items(), desc='Photos uploading'):
            sleep(.1)
            params = {'path': path + filename, 'url': url, 'overwrite': 'true', }
            response = requests.post('https://cloud-api.yandex.net/v1/disk/resources/upload', headers=headers,
                                     params=params)
            response.raise_for_status()
            if response.status_code != 202:
                print(f'Не удалось загрузить файл {filename} на Яндекс Диск')


class MainMenu:
    url_vk = 'https://api.vk.com/method/'
    api_vk_version = '5.131'
    url_dict = {}
    dir_name = ''
    vk_token = os.getenv('VK_TOKEN')
    yandex_token = os.getenv('YANDEX_TOKEN')
    service_account_file = 'picsgrabber-114c6c5758b2.json'

    import_resource_dict = {'1': VKGrabber.grab_vk, '2': VKGrabber.grab_vk, '3': False}

    def greeting(self):
        print()
        import_resource = input('Выберите ресурс, из  которого хотите импортировать фотографии:\n'
                                '1 - Импортировать фото из Вкондакте\n'
                                '2 - Импортировать фото из Instagram\n'
                                '3 - Завершить выполнение программы\n')
        if import_resource == '3':
            print('Спасибо за использование! До свидания!\n')
            exit()
        elif import_resource in self.import_resource_dict:
            self.import_resource_dict[import_resource](self)
        else:
            print(f'Команды {import_resource} не существует. Укажите номер выбранного вами варианта\n')

    export_resource_dict = {'1': YandexUploader.yd_folder_maker, '2': GDUploader.gd_folder_maker, '3': False}

    def choose_resource_for_export(self):
        export_resource = input('Выберите ресурс, в который хотите экспортировать фотографии:\n'
                                '1 - Импортировать фото в Yandex Disc\n'
                                '2 - Импортировать фото в Google Drive\n'
                                '3 - Завершить выполнение программы\n')
        if export_resource == '3':
            print('Спасибо за использование! До свидания!\n')
            exit()
        elif export_resource in self.export_resource_dict:
            self.export_resource_dict[export_resource](self)
        else:
            print(f'Команды {export_resource} не существует. Укажите номер выбранного вами варианта\n')


if __name__ == '__main__':
    my_menu = MainMenu()
    my_vk_grabber = VKGrabber()
    my_yandex_uploader = YandexUploader()
    my_gd_uploader = GDUploader()
    print('Приветствую Вас в программе "PicsGrabber"!')
    while True:
        my_menu.greeting()
