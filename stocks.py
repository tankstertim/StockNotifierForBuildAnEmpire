import pydirectinput
import pyautogui
import time
from constants import *
# Take a screenshot of the entire screen and save it



def is_color_close(c1, c2, tolerance=25):
    return (
        abs(c1[0] - c2[0]) <= tolerance and
        abs(c1[1] - c2[1]) <= tolerance and
        abs(c1[2] - c2[2]) <= tolerance
    )


def take_screenshot():
    """
    Takes a screenshot of the entire screen and saves it as a PNG file.

    :param filename: Name of the file to save the screenshot.
    """
    screenshot = pyautogui.screenshot()  # Take the screenshot
    return screenshot    # Save it to the given filename
    

def click_button(posx,posy):
    pydirectinput.moveTo(posx,posy, duration=0.1)
    pydirectinput.moveTo(posx +5, posy,duration=0.2)
    pydirectinput.click()
    pydirectinput.click()

def scroll(amount):
    pyautogui.scroll(amount)

def check_items():
    screenshot = take_screenshot()

    color1 = screenshot.getpixel((ITEM_1_POS[0], ITEM_1_POS[1]))
    color2 = screenshot.getpixel((ITEM_2_POS[0], ITEM_2_POS[1]))

    stock = []
    stock.append(is_color_close(color1, LIGHT_COLOR))
    stock.append(is_color_close(color2, LIGHT_COLOR))

    return stock


def get_stock(item_list, scroll_amount):
    stocks = {}
    scroll_number = ((len(item_list)) //2) + 1
    scroll(scroll_amount * scroll_number)
    index = 0
    for i in range(scroll_number):
        stock = check_items()

     
        if index < len(item_list):
            stocks[item_list[index]] = stock[0]
            if stock[0]:
                print(f"{item_list[index]} is in stock")
            else:
                print(f"{item_list[index]} is out of stock")

        if index +1 < len(item_list):  
            stocks[item_list[index+1]] = stock[1]
            if stock[1]:
                print(f"{item_list[index+1]} is in stock")
            else:
                print(f"{item_list[index+1]} is out of stock")
        index += 2
        scroll(-scroll_amount)
   
    
    scroll(scroll_amount *  scroll_number)
    return stocks


def click_scroll():
    click_button(SCROLL_POS[0], SCROLL_POS[1])
 

def get_economy_stock():
    click_button(ECONOMY_BUTTON_POS[0], ECONOMY_BUTTON_POS[1])
    click_scroll()
    return get_stock(ECONOMY_ITEMS, 330)

def get_population_stock():
    click_button(POPULATON_BUTTON_POS[0], POPULATON_BUTTON_POS[1])
    click_scroll()
    return get_stock(POPULATION_ITEMS,345)

def get_utiltiy_stock():
    click_button(UTILITYBUTTON_POS[0], UTILITYBUTTON_POS[1])
    click_scroll()
    return get_stock(UTILITY_ITEMS,345)



def get_all_stocks():
    all_stocks = {}
    all_stocks['economy'] = get_economy_stock()
    all_stocks['population'] = get_population_stock()
    all_stocks['utility'] = get_utiltiy_stock()
    return all_stocks   
