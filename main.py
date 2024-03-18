import base64
import os
from time import sleep
from urllib import request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pydrive.auth import GoogleAuth
import io
import json
import requests

NEED_TO_SEARCH_PROVINSI = ['DKI JAKARTA', 'Luar Negeri']
NEED_TO_SEARCH_KAB_FOR_JAKARTA = [
    'KOTA ADM. JAKARTA PUSAT', 'KOTA ADM. JAKARTA SELATAN']


def main():
    gauth = GoogleAuth()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    client_secrets_file = os.path.join(script_dir, 'client_secrets.json')
    client_creds_file = os.path.join(script_dir, 'credentials.json')
    gauth.LoadClientConfigFile(client_secrets_file)
    gauth.LoadCredentialsFile(client_creds_file)
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    
    gauth.SaveCredentialsFile(client_creds_file)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    url = 'https://pemilu2024.kpu.go.id/pilegdpr/hitung-suara'
    driver.get(url)
    provinsi_list = get_list(driver, 3)
    prov_names = [x.text for x in provinsi_list]
    for provinsi in prov_names:
        if provinsi in NEED_TO_SEARCH_PROVINSI:
            kabupaten_list, kab_names = get_names(
                driver, provinsi_list, prov_names, provinsi, 4)
            for kabupaten in kab_names:
                if provinsi == 'DKI JAKARTA' and kabupaten not in NEED_TO_SEARCH_KAB_FOR_JAKARTA:
                    continue
                kecamatan_list, kec_names = get_names(
                    driver, kabupaten_list, kab_names, kabupaten, 5)
                for kecamatan in kec_names:
                    kelurahan_list, kel_names = get_names(
                        driver, kecamatan_list, kec_names, kecamatan, 6)
                    for kelurahan in kel_names:
                        tps_list, tps_names = get_names(
                            driver, kelurahan_list, kel_names, kelurahan, 7)
                        for tps in tps_names:
                            driver.execute_script(
                                "arguments[0].click();", tps_list[tps_names.index(tps)])
                            sleep(7)
                            images = driver.find_elements(
                                By.XPATH, '//img[@alt="Form C1 image"]')
                            if len(images) > 0:
                                filename = f"{provinsi} - {kabupaten} - {kecamatan} - {kelurahan} - {tps}.pdf"
                                save_page_to_drive(filename, driver, gauth)
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
    driver.execute_script(
        "arguments[0].click();", list[names.index(curr)])
    lists = get_list(driver, index)
    sleep(1)
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
            url = image.get_attribute("src")
            filename = url.split('/')[-1]
            folder_id = '1jo-vt-7WyZkrvyxqIjVxzTQP5MD3GJZp'

            access_token = gauth.attr['credentials'].access_token
            metadata = {
                "name": filename,
                "parents": [folder_id]
            }

            r = requests.get(
                "https://www.googleapis.com/drive/v3/files?q=name='" +
                filename + "' and '" + folder_id + "' in parents",
                headers={"Authorization": "Bearer " + access_token}
            )
            if r.json().get('files'):
                print("file exists")
                return

            file = {
                'data': ('metadata', json.dumps(metadata), 'application/json'),
                'file': io.BytesIO(requests.get(url).content)
            }
            r = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
                headers={"Authorization": "Bearer " + access_token},
                files=file
            )

            print(r.status_code, r.text)

        except:
            print("error uploading image to drive")


def save_page_to_drive(filename, driver, gauth):
    try:
        folder_id = '1_Qt_NmSndhkV7QtX0JHauGM21Kk9wTsT'

        # check if token is expired
        if gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
            
        access_token = gauth.attr['credentials'].access_token
        metadata = {
            "name": filename,
            "parents": [folder_id]
        }

        r = requests.get(
            "https://www.googleapis.com/drive/v3/files?q=name='" +
            filename + "' and '" + folder_id + "' in parents",
            headers={"Authorization": "Bearer " + access_token}
        )

        if r.json().get('files'):
            print("file exists")
            return

        driver.execute_script("window.print();")
    
        sleep(5)
        
        result = driver.execute_cdp_cmd('Page.printToPDF', {'landscape': False, 'displayHeaderFooter': False})
        pdf_data = base64.b64decode(result['data'])

        file = {
            'data': ('metadata', json.dumps(metadata), 'application/json'),
            'file': io.BytesIO(pdf_data)
        }
        r = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
            headers={"Authorization": "Bearer " + access_token},
            files=file
        )

        print(r.status_code, r.text)

    except Exception as e:
        print(f"error uploading image to drive: {e}")


if __name__ == '__main__':
    main()
