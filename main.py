from time import sleep
from urllib import request
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from pydrive.auth import GoogleAuth
import io
import json
import requests

NEED_TO_SEARCH_PROVINSI = ['DKI JAKARTA', 'Luar Negeri']


def main():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    driver = webdriver.Edge()
    url = 'https://pemilu2024.kpu.go.id/pilegdpr/hitung-suara'
    driver.get(url)
    provinsi_list = get_list(driver, 3)
    prov_names = [x.text for x in provinsi_list]
    for provinsi in prov_names:
        if provinsi in NEED_TO_SEARCH_PROVINSI:
            kabupaten_list, kab_names = get_names(
                driver, provinsi_list, prov_names, provinsi, 4)
            for kabupaten in kab_names:
                kecamatan_list, kec_names = get_names(
                    driver, kabupaten_list, kab_names, kabupaten, 5)
                for kecamatan in kec_names:
                    kelurahan_list, kel_names = get_names(
                        driver, kecamatan_list, kec_names, kecamatan, 6)
                    for kelurahan in kel_names:
                        tps_list, tps_names = get_names(
                            driver, kelurahan_list, kel_names, kelurahan, 7)
                        for tps in tps_names:
                            tps_list[tps_names.index(tps)].click()
                            sleep(6)
                            images = driver.find_elements(
                                By.XPATH, '//img[@alt="Form C1 image"]')
                            if len(images) > 0:
                                upload_to_drive(images, gauth)
                            # restore tps list
                            tps_list = get_list(driver, 7)
                        # restore kelurahan list
                        kelurahan_list = get_list(driver, 6)
                    # restore kecamatan list
                    kecamatan_list = get_list(driver, 5)
                # restore kabupaten list
                kabupaten_list = get_list(driver, 4)
            # restore provinsi_list elements
            provinsi_list = get_list(driver, 3)


def get_dropdowns(driver):
    return driver.find_elements(
        By.CSS_SELECTOR, '.vs--searchable')


def get_list(driver, index):
    sleep(1)
    dropdowns = get_dropdowns(driver)
    dropdown = dropdowns[index]
    dropdown.click()
    menu = dropdown.find_element(
        By.CSS_SELECTOR, 'ul.vs__dropdown-menu')
    lists = menu.find_elements(
        By.CSS_SELECTOR, 'li.vs__dropdown-option')
    return lists


def get_names(driver, list, names, curr, index):
    list[names.index(curr)].click()
    lists = get_list(driver, index)
    sleep(2)
    names = [x.text for x in lists]
    return lists, names


def download_images(images_url):
    for image in images_url:
        try:
            src = image.get_attribute("src")
            image_name = src.split('/')[-1]
            request.urlretrieve(src, f"{image_name}.jpg")
        except:
            print('error downloading image')

def upload_to_drive(images_url, gauth):
    for image in images_url:
        try:
            url = image.get_attribute("src") # Please set the URL of direct link of the image.
            filename = url.split('/')[-1] # Please set the filename.
            folder_id = '1jo-vt-7WyZkrvyxqIjVxzTQP5MD3GJZp' # Please set the folder ID of the shared Drive. When you want to create the file to the root folder of the shared Drive, please set the Drive ID here.

            access_token = gauth.attr['credentials'].access_token
            metadata = {
                "name": filename,
                "parents": [folder_id]
            }
            
            r = requests.get(
                "https://www.googleapis.com/drive/v3/files?q=name='" + filename + "' and '" + folder_id + "' in parents",
                headers={"Authorization": "Bearer " + access_token}
            )
            if r.json().get('files'):
                print("file exists")
                continue

            file = {
                'data': ('metadata', json.dumps(metadata), 'application/json'),
                'file': io.BytesIO(requests.get(url).content)
            }
            r = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
                headers={"Authorization": "Bearer " + access_token},
                files=file
            )

        except:
            print("error uploading image to drive")

main()
