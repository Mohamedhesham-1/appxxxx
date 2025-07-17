from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.cookies import RequestsCookieJar
import requests
import time
import asyncio
from telegram import Bot
from telegram.request import HTTPXRequest
from collections import Counter
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta

# عدد الأيام اللي عايز تبحث فيهم (مثلاً: 30 يوم قدام)
search_days = 31
start_date = datetime.today()
end_date = start_date + timedelta(days=search_days)
date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(search_days + 1)]

# --- User---
email = "blsbot8@gmail.com"
password = "Passport123@"
date = '2025-07-01'
# --- User---





# --- Global Session Variables ---
TELEGRAM_TOKEN = "8161136526:AAF3FO9U51boonoPN21WN11S7zRmaw9Yrmo"
CHAT_IDS = ['-1002871171006']
category_ids = [
    '5c2e8e01-796d-4347-95ae-0c95a9177b26',
    '37ba2fe4-4551-4c7d-be6e-5214617295a9',
    '9b1ae169-39b1-4783-aa12-ffa189dec130',
]
location_id = "60d2df036755e8de168d8db7"
visa_type = "c805c157-7e8f-4932-89cf-d7ab69e1af96"
visa_sub_type = "19102874-4542-4852-8f63-a042bc644eba"
mission_id = "beae2d19-89a9-46e7-9415-5422adafe619"

headers = {
    "Content-Type": "application/json"
}

bot = Bot(token=TELEGRAM_TOKEN, request=HTTPXRequest(read_timeout=30.0))


session_cookies = []
request_verification_token = ""
driver = None

def selenium_login():
    global session_cookies, request_verification_token, driver

    def restart_login():
        print("❌ CAPTCHA failed, restarting login...")
        selenium_login()  # Recursively restart login
        return

    if driver is not None:
        try:
            driver.quit()
        except:
            pass

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://egypt.blsspainglobal.com/Global/account/Login")
    wait = WebDriverWait(driver, 30)

    # Email
    email_input = next(inp for inp in driver.find_elements(By.TAG_NAME, "input") if inp.is_displayed())
    email_input.clear()
    email_input.send_keys(email)

    verify_button = wait.until(EC.element_to_be_clickable((By.ID, "btnVerify")))
    verify_button.click()

    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='password']")))
    for input_element in driver.find_elements(By.CSS_SELECTOR, "input[type='password']"):
        if input_element.is_displayed():
            input_element.clear()
            input_element.send_keys(password)
            break

    # Get images
    all_images = driver.find_elements(By.CSS_SELECTOR, ".main-div-container img")
    visible_images = []
    for img in all_images:
        try:
            parent = img.find_element(By.XPATH, "./..")
            if img.is_displayed() and driver.execute_script("return window.getComputedStyle(arguments[0]).display !== 'none';", parent):
                visible_images.append(img)
        except Exception as e:
            print("Visibility check error:", e)
    visible_images = visible_images[:9]

    base64_images = [img.get_attribute("src").split(",")[1] for img in visible_images if img.get_attribute("src").startswith("data:image")]

    # NoCaptchaAI
    response = requests.post(
        "https://api.nocaptchaai.com/createTask",
        json={
            "clientKey": "hashemahmed-4ae8e09d-f4e0-034f-2b6e-611095929e9a",
            "task": {
                "type": "ImageToTextTask",
                "images": base64_images,
                "numeric": True,
                "module": "morocco",
                "case": False,
                "maxLength": 3
            }
        },
        headers={"Content-Type": "application/json"}
    )
    result = response.json()
    print("NoCaptchaAI response:", result)

    if "solution" not in result or "text" not in result["solution"]:
        raise Exception(f"NoCaptchaAI failed: {result}")

    image_texts = result["solution"]["text"]
    most_common_value, _ = Counter(image_texts).most_common(1)[0]

    # Click all matching
    image_elements = [img for img in driver.find_elements(By.CSS_SELECTOR, ".main-div-container img") if img.is_displayed()][:9]
    for idx, text in enumerate(image_texts):
        if idx < len(image_elements) and text == most_common_value:
            try:
                driver.execute_script("arguments[0].click();", image_elements[idx])
                time.sleep(0.3)
            except Exception as e:
                print(f"Failed to click image {idx}: {e}")

    # Submit CAPTCHA
    try:
        verify_btn = driver.find_element(By.ID, "btnVerify")
        verify_btn.click()
    except:
        print("⚠️ Failed to click 'btnVerify', restarting login...")
        restart_login()
        return

    # Wait and check if CAPTCHA was accepted
    time.sleep(3)
    try:
        # If btnVerifyCaptcha is still visible, the CAPTCHA failed
        driver.find_element(By.ID, "btnVerifyCaptcha")
        restart_login()
        return
    except:
        pass  # CAPTCHA accepted

    print("✅ Login successful!")

    driver.get("https://egypt.blsspainglobal.com/Global/bls/visatypeverification")
    request_verification_token = driver.find_element(By.NAME, "__RequestVerificationToken").get_attribute("value")
    session_cookies = driver.get_cookies()

async def check_category(category_id, index):
    global session_cookies, request_verification_token

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "RequestVerificationToken": request_verification_token,
        "Referer": f"https://egypt.blsspainglobal.com/Global/blsAppointment/ManageAppointment?appointmentFor=Individual&applicantsNo=1&visaType={visa_type}&visaSubType={visa_sub_type}&appointmentCategory={category_id}&location={location_id}",
        "Origin": "https://egypt.blsspainglobal.com"
    }

    jar = RequestsCookieJar()
    for cookie in session_cookies:
        jar.set(cookie['name'], cookie['value'], domain=cookie.get('domain'), path=cookie.get('path'))

    available_days = {}

    for date in date_range:
        url = f"https://egypt.blsspainglobal.com/Global/blsappointment/GetAvailableSlotsByDate?appointmentDate={date}&locationId={location_id}&categoryId={category_id}&visaType={visa_type}&visaSubType={visa_sub_type}&applicantCount=1&dataSource=WEB_BLS&missionId={mission_id}"
        try:
            response = requests.post(url, headers=headers, cookies=jar)
            if response.status_code == 401:
                print("🔁 انتهت الجلسة، تسجيل الدخول مرة أخرى...")
                selenium_login()
                return
            elif response.status_code == 429:
                print("⏳ تم تحديد معدل الطلبات، الانتظار 3 دقائق...")
                await asyncio.sleep(180) # انتظر 3 دقائق
                return

            response.raise_for_status() # ترفع استثناء لأخطاء HTTP (مثل 4xx أو 5xx)
            data = response.json()
            
            # سطر التصحيح هذا مفيد جدًا، لا تحذفه إلا بعد التأكد أن الكود يعمل بشكل سليم
            print(f"DEBUG: الاستجابة للتاريخ {date} والفئة {category_id}: {data}")

            # تأكد أن 'data' هي قائمة (List) قبل محاولة التكرار عليها
            if isinstance(data, list):
                # قم بتصفية الفترات الزمنية التي يكون فيها 'Count' أكبر من 0 (أي يوجد بها مواعيد)
                # واستخدم 'Name' للحصول على وقت الموعد
                slots_for_this_date = [
                    slot['Name'] for slot in data 
                    if 'Name' in slot and 'Count' in slot and slot['Count'] > 0
                ]
                
                # إذا وجدنا أي مواعيد متاحة لهذا التاريخ، قم بإضافتها
                if slots_for_this_date:
                    available_days[date] = slots_for_this_date
            else:
                # هذا الجزء للتعامل مع الحالات التي لا تكون فيها 'data' قائمة 
                # (قد تكون قاموساً يحتوي على رسالة خطأ مثلاً من الخادم)
                print(f"⚠️ تحذير: استجابة غير متوقعة لـ {date} (الفئة: {category_id}). البيانات الخام: {data}")

        except Exception as e:
            # رسالة خطأ عامة لأي مشكلة أخرى تحدث أثناء جلب البيانات أو تحليلها
            print(f"❌ خطأ أثناء جلب التاريخ {date}: {e}")

    # --- الطباعة والتبليغ عبر تليجرام ---
    # هذا الجزء سيتم تنفيذه بعد مراجعة جميع التواريخ ضمن نطاق البحث
    
    label = ["Normal", "Premium", "Prime Time"][index]
    
    if available_days: # إذا كانت هناك أي أيام بها مواعيد
        print(f"\n✅ مواعيد متاحة في {label}:")
        message = f"✅ مواعيد متاحة في {label}:\n"
        for day, slots in available_days.items():
            print(f" - {day}: {', '.join(slots)}")
            message += f"التاريخ: {day}\nالأوقات: {', '.join(slots)}\n"
        for chat_id in CHAT_IDS:
            await bot.send_message(chat_id=chat_id, text=message)
    else: # إذا لم يتم العثور على أي مواعيد في جميع الأيام التي تم البحث فيها
        # هذا الجزء سيتم طباعته في الكونسول فقط، ولن يتم إرسال رسالة تيليجرام
        print(f"❌ لا توجد مواعيد في {label}")
        
    # إرسال الرسالة عبر Telegram
    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=message)


async def send_request_and_notify():
    # Check the first category
    await check_category(category_ids[0], 0)

    # Check the rest
    for idx, category_id in enumerate(category_ids[1:], start=1):
        await check_category(category_id, idx)

    # Re-check the first category again
    await check_category(category_ids[0], 0)

async def main_loop():
    selenium_login()
    while True:
        await send_request_and_notify()
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        if driver:
            driver.quit()
