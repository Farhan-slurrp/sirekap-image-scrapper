from time import sleep
from urllib import request
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By

NEED_TO_SEARCH_PROVINSI = ['DKI JAKARTA', 'Luar Negeri']


def main():
    driver = webdriver.Edge()
    url = 'https://pemilu2024.kpu.go.id/pilegdpr/hitung-suara'
    driver.get(url)
    provinsi_list = get_list(driver, 3)
    prov_names = [x.text for x in provinsi_list]
    for provinsi in prov_names:
        if provinsi in NEED_TO_SEARCH_PROVINSI[0]:
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
                            sleep(10)
                            images = driver.find_elements(
                                By.XPATH, '//img[@alt="Form C1 image"]')
                            if len(images) > 0:
                                download_images(images)
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
    dropdowns = get_dropdowns(driver)
    dropdown = dropdowns[index]
    dropdown.click()
    menu = dropdown.find_element(
        By.CSS_SELECTOR, 'ul.vs__dropdown-menu')
    list = menu.find_elements(
        By.CSS_SELECTOR, 'li.vs__dropdown-option')
    return list


def get_names(driver, list, names, curr, index):
    list[names.index(curr)].click()
    list = get_list(driver, index)
    names = [x.text for x in list]
    return list, names


def download_images(images_url):
    for image in images_url:
        try:
            src = image.get_attribute("src")
            image_name = src.split('/')[-1]
            request.urlretrieve(src, f"{image_name}.jpg")
        except:
            print('error downloading image')


main()
