import requests
import datetime
import json
import dpath.util
from dotenv import load_dotenv
from tqdm import tqdm
from time import sleep
from pprint import pprint

load_dotenv()


class PicsGrabber:
    url_vk = 'https://api.vk.com/method/'

    def __init__(self):
        self.api_vk_version = '5.131'
        self.url_dict = {}
        self.id = ID
        self.vk_token = VK_Token
        self.yandex_token = YANDEX_TOKEN

    def grab_vk(self):
        user_id = input('Введите ID пользователя, фотографии которого вы хотите импортировать:\n')
        album = input(
            'Введите название альбома (wall, profile или saved), фотографии из которого вы хотите импортировать.\n')
        count = input('Укажите максимальное число фотографий (не более 1000), которых нужно импортировать:\n')
        params = {
            'user_id': user_id,
            'access_token': self.vk_token,
            'v': self.api_vk_version,
            'extended': '1',
            'album_id': album,
            'photo_sizes': '1',
            'count': count
        }

        try:
            imported_json = requests.get(self.url_vk + 'photos.get', params=params)
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
                url_dict = {}
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
                                url_dict[file_name] = dpath.util.get(size, 'url')
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

                self.choose_resource_for_export(url_dict)
                self.url_dict = url_dict
                return

        except KeyError:
            print(
                'Произошла ошибка. Возможно профиль или альбом закрыт настройками приватности или альбома не существует. '
                'Проверьте правильность написания альбома и его доступность из вашего профиля.\n')
            return

    def yd_folder_maker(self, url_dict):
        dir_name = input('Введите имя папки, которую хотите создать на своем Яндекс Диске:\n')
        params = {'path': dir_name}
        headers = {'Content-Type': 'application/json', 'Authorization': 'OAuth {}'.format(self.yandex_token)}
        response = requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers=headers, params=params)
        if response.status_code != 201:
            print(
                f'Упс, произошла ошибка: {response.status_code}. Проверьте, возможно папка с таким названием уже существует.\n')
        else:
            self.yd_upload(dir_name, url_dict)

    def yd_upload(self, dir_name, url_dict):
        path = dir_name + '/'
        headers = {'Content-Type': 'application/json', 'Authorization': 'OAuth {}'.format(self.yandex_token)}
        for filename, url in tqdm(url_dict.items(), desc='Photos uploading'):
            sleep(.1)
            params = {'path': path + filename, 'url': url, 'overwrite': 'true', }
            response = requests.post('https://cloud-api.yandex.net/v1/disk/resources/upload', headers=headers,
                                     params=params)
            response.raise_for_status()
            if response.status_code != 202:
                print(f'Не удалось загрузить файл {filename} на Яндекс Диск')

    import_resource_dict = {'1': grab_vk, '2': grab_vk, '3': grab_vk, '4': False}

    def greeting(self):
        print()
        import_resource = input('Выберите ресурс, из  которого хотите импортировать фотографии:\n'
                                '1 - Импортировать фото из Вкондакте\n'
                                '2 - Импортировать фото из Одноклассники\n'
                                '3 - Импортировать фото из Instagram\n'
                                '4 - Завершить выполнение программы\n')
        if import_resource == '4':
            print('Спасибо за использование! До свидания!\n')
            exit()
        elif import_resource in self.import_resource_dict:
            self.import_resource_dict[import_resource](self)
        else:
            print(f'Команды {import_resource} не существует. Укажите номер выбранного вами варианта\n')

    export_resource_dict = {'1': yd_folder_maker, '2': grab_vk, '3': False}

    def choose_resource_for_export(self, url_dict):
        export_resource = input('Выберите ресурс, в который хотите экспортировать фотографии:\n'
                                '1 - Импортировать фото в Yandex Disc\n'
                                '2 - Импортировать фото в Google Drive\n'
                                '3 - Завершить выполнение программы\n')
        if export_resource == '3':
            print('Спасибо за использование! До свидания!\n')
            exit()
        elif export_resource in self.export_resource_dict:
            self.export_resource_dict[export_resource](self, url_dict)
        else:
            print(f'Команды {export_resource} не существует. Укажите номер выбранного вами варианта\n')


if __name__ == '__main__':
    my_grabber = PicsGrabber()
    print('Приветствую Вас в программе "PicsGrabber"!')
    while True:
        my_grabber.greeting()

