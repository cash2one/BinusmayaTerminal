import os
import sys
import argparse
import base64
from time import sleep
from PIL import Image
from selenium import webdriver

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", type=str,
                     help="Binusmaya username")
parser.add_argument("-p", "--password", type=str,
                     help="Binusmaya password. password enclosed with single quote")
parser.add_argument("-w", "--webdriver", type=str, default="chrome",
                     help="Webdriver options (chrome or phantomjs), default is chrome")
args = parser.parse_args()

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

curr_dir = os.getcwd()

if args.webdriver == 'chrome':
    driver_path = curr_dir + '/chromedriver'
    browser = webdriver.Chrome(driver_path)
elif args.webdriver == 'phantomjs':
    driver_path = curr_dir + '/phantomjs'
    browser = webdriver.PhantomJS(driver_path)

url = "https://binusmaya.binus.ac.id/login/index.php"

browser.get(url)
sleep(2)

xpaths = { 'uid' : '//*[@id="login"]/form/div/label/input',
                'pwd' : '//*[@id="login"]/form/p[1]/span/input',
                'captcha' : '//*[@id="defaultLoginReal"]',
                'submitBtn' : '//*[@id="ctl00_ContentPlaceHolder1_SubmitButtonBM"]'}

# Captcha solver on progress
print("solving captcha...")
ele_captcha = browser.find_element_by_xpath('//*[@id="login"]/form/p[2]/img')
img_captcha_base64 = browser.execute_async_script("""
    var ele = arguments[0], callback = arguments[1];
    ele.addEventListener('load', function fn(){
      ele.removeEventListener('load', fn, false);
      var cnv = document.createElement('canvas');
      cnv.width = 90; cnv.height = 32;
      cnv.getContext('2d').drawImage(this, 0, 0);
      callback(cnv.toDataURL('image/jpeg').substring(22));
    }, false);
    ele.dispatchEvent(new Event('load'));
    """, ele_captcha)

with open(r"captcha.jpg", 'wb') as f:
    f.write(base64.b64decode(img_captcha_base64))

# convert to black and white image
img = Image.open('captcha.jpg')
gray = img.convert('L')
bw_img = gray.point(lambda x: 0 if x < 128 else 255, '1')
bw_img.save('captcha_bw.jpg')

# extract image to txt
os.system('tesseract -psm 7 captcha_bw.jpg captcha')
f_op = open('captcha.txt', 'r')
s = f_op.readline()
f_op.close()

# temporary fix when encounter digit 2 recognize as 'Z'
if s[0] == 'Z':
    s[0] = 2
elif s[2] == 'Z':
    s[2] = 2

# calculate captcha
if s[1] == '+':
    captcha = int(s[0]) + int(s[2])
elif s[1] == '-':
    captcha = int(s[0]) - int(s[2])
elif s[1] == 'x':
    captcha = int(s[0]) * int(s[2])

print("captcha value:", captcha)
# remove files
os.remove('captcha.jpg')
os.remove('captcha_bw.jpg')
os.remove('captcha.txt')

browser.find_element_by_xpath(xpaths['uid']).clear()
browser.find_element_by_xpath(xpaths['uid']).send_keys(args.username)
browser.find_element_by_xpath(xpaths['pwd']).clear()
browser.find_element_by_xpath(xpaths['pwd']).send_keys(args.password)
browser.find_element_by_xpath(xpaths['captcha']).clear()
browser.find_element_by_xpath(xpaths['captcha']).send_keys(captcha)
browser.find_element_by_xpath(xpaths['submitBtn']).click()

# wait until page loaded
sleep(7)

# user profile
user_profile = browser.find_element_by_class_name("user-profile")
your_name = user_profile.find_element_by_class_name("student-name").text
your_name = your_name.title()
your_position = user_profile.find_element_by_class_name("position").text
print("\nUser profile: ")
print(your_name)
print(your_position)

# today agenda
print("\nToday agenda:")
widget_schedule = browser.find_element_by_class_name("widget-schedule")
today_agenda = widget_schedule.find_elements_by_class_name("schedule-item")
for course in today_agenda:
    print(course.text)

# get current courses
print("\nYour current courses:")
course_widget = browser.find_element_by_id("widget-current-courses")
my_current_courses = course_widget.find_elements_by_tag_name("li")
if len(my_current_courses): # check if current courses list loaded
    sleep(3)
    # course_widget = browser.find_element_by_id("widget-current-courses")
    my_current_courses = course_widget.find_elements_by_tag_name("li")
    for course in my_current_courses:
        print(course.text)
else:
    print("Current courses not loaded, probably slow internet connection.")

print("\nscraping finished...")

# get your data
#your_gpa = browser.find_element_by_id('gpa-score').text
#sat_point = browser.find_element_by_id('lblSATActivityPoints').text
#com_serv = browser.find_element_by_id('lblSATCommunityHours').text
#print("Your GPA:", your_gpa)
#print("Your SAT Point:", sat_point)
#print("Your Community Services hours:", com_serv)

print("press q to quit browser")
c = input().strip()
if c == 'q':
    browser.close()
