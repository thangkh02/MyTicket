import os
import django
import re
import requests
from datetime import datetime
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import io
from PIL import Image
from django.core.files.base import ContentFile
# Import webdriver-manager để tự động cài đặt ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager
# Thêm thư viện unidecode để chuyển đổi tiếng Việt thành không dấu
try:
    from unidecode import unidecode
except ImportError:
    print("Đang cài đặt thư viện unidecode...")
    import subprocess
    subprocess.check_call(["pip", "install", "unidecode"])
    from unidecode import unidecode

# Cấu hình Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket.settings')
django.setup()

from app.models import Event, EventSession

def parse_date_time(text):
    """Phân tích chuỗi ngày tháng từ text với nhiều định dạng khác nhau"""
    try:
        # Xử lý nhiều định dạng ngày tháng khác nhau
        
        # Định dạng 1: "T6, 17/05/2024, 20:00"
        pattern1 = r'[A-Za-z]+, (\d{2}/\d{2}/\d{4}), (\d{2}:\d{2})'
        match = re.search(pattern1, text)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            dt_str = f"{date_str} {time_str}"
            return datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        
        # Định dạng 2: "17 tháng 05, 2025" (định dạng mới từ Ticketbox)
        pattern2 = r'(\d{2}) tháng (\d{2}), (\d{4})'
        match = re.search(pattern2, text)
        if match:
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)
            # Giả định giờ mặc định là 20:00
            dt_str = f"{day}/{month}/{year} 20:00"
            return datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        
        # Định dạng 3: "May 17, 2025" (phiên bản tiếng Anh)
        pattern3 = r'([A-Za-z]+) (\d{1,2}), (\d{4})'
        match = re.search(pattern3, text)
        if match:
            month_name = match.group(1)
            day = match.group(2)
            year = match.group(3)
            
            # Chuyển đổi tên tháng sang số
            month_dict = {
                'January': '01', 'February': '02', 'March': '03', 'April': '04',
                'May': '05', 'June': '06', 'July': '07', 'August': '08',
                'September': '09', 'October': '10', 'November': '11', 'December': '12',
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05',
                'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10',
                'Nov': '11', 'Dec': '12'
            }
            
            if month_name in month_dict:
                month = month_dict[month_name]
                dt_str = f"{day}/{month}/{year} 20:00"
                return datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        
        print(f"Không tìm thấy định dạng ngày tháng phù hợp cho: '{text}'")
    except Exception as e:
        print(f"Lỗi phân tích ngày tháng: {e} - Văn bản: '{text}'")
    
    # Nếu không thể phân tích, sử dụng thời gian hiện tại + 1 tháng làm mặc định
    return datetime.now().replace(month=datetime.now().month + 1 if datetime.now().month < 12 else 1)

def download_image(url, event_title):
    """Tải ảnh từ URL và trả về ContentFile để lưu vào Model"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # Xử lý tên file
            file_name = urlparse(url).path.split('/')[-1]
            # Đảm bảo file có phần mở rộng
            if not any(file_name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                file_name = f"{file_name}.jpg"
            
            # Đọc và tối ưu hóa hình ảnh
            image = Image.open(io.BytesIO(response.content))
            image_io = io.BytesIO()
            image.save(image_io, format='JPEG', quality=85)
            
            return ContentFile(image_io.getvalue(), name=file_name)
    except Exception as e:
        print(f"Lỗi khi tải hình ảnh: {e}")
    return None

def crawl_ticketbox(category='music', max_pages=3):
    """
    Crawl dữ liệu sự kiện từ Ticketbox.vn và lưu vào cơ sở dữ liệu
    """
    print(f"Bắt đầu crawl dữ liệu cho danh mục: {category}")
    
    # Cấu hình Chrome Driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Chạy ngầm không hiển thị UI
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")  # Tắt sandbox để giải quyết lỗi quyền truy cập
    chrome_options.add_argument("--disable-dev-shm-usage")  # Khắc phục lỗi bộ nhớ chia sẻ trên một số hệ thống
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Chi tiết lỗi nếu có
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("Đang khởi tạo ChromeDriver...")
        # Khởi tạo driver với ChromeDriverManager
        driver = webdriver.Chrome(options=chrome_options)
        events_crawled = 0
        
        for page in range(1, max_pages + 1):
            url = f"https://ticketbox.vn/search?cate={category}&page={page}"
            print(f"Đang crawl trang {page}: {url}")
            
            driver.get(url)                # Chờ trang tải xong
            try:
                print("Đang chờ trang tải nội dung...")
                # Lấy nội dung trang trước - cập nhật CSS selector cho cấu trúc trang mới
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.sc-12dd4e85-1'))
                )
                print("Đã tìm thấy phần tử sự kiện trên trang")
            except TimeoutException:
                print(f"Hết trang hoặc timeout ở trang {page}")
                # Lưu nội dung trang để debug
                with open(f'page_debug_{page}.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"Đã lưu nội dung trang vào file page_debug_{page}.html để debug")
                break
              # Parse nội dung
            print("Đang phân tích nội dung trang...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
              # Lưu trữ các liên kết sự kiện trước khi xử lý
            event_links = {}
            
            # Phương pháp 1: Tìm tất cả các thẻ a chứa phần tử có class text-title
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                title_elem = link.select_one('.text-title')
                if title_elem:
                    title_text = title_elem.text.strip()
                    href = link['href']
                    if not href.startswith('http'):
                        href = f"https://ticketbox.vn{href}"
                    event_links[title_text] = href
                    print(f"Phương pháp 1 - Đã tìm thấy link: {title_text} -> {href}")
            
            # Phương pháp 2: Tìm thẻ a chứa thẻ div.sc-12dd4e85-1
            # Đây là cấu trúc phổ biến trên trang mới của Ticketbox
            if not event_links:
                # Lưu cấu trúc HTML để debug
                print("Đang thử phương pháp 2 để tìm link sự kiện...")
                
                # Phân tích lại HTML bằng cách tìm các phần tử có chứa class tiêu đề
                event_containers = soup.find_all(lambda tag: tag.name == 'a' and tag.find(class_='sc-12dd4e85-1'))
                
                for container in event_containers:
                    title_elem = container.select_one('.text-title')
                    if title_elem and 'href' in container.attrs:
                        title_text = title_elem.text.strip()
                        href = container['href']
                        if not href.startswith('http'):
                            href = f"https://ticketbox.vn{href}"
                        event_links[title_text] = href
                        print(f"Phương pháp 2 - Đã tìm thấy link: {title_text} -> {href}")
            
            # Phương pháp 3: Lấy trực tiếp JavaScript data nếu có
            if not event_links:
                print("Đang thử phương pháp 3 để tìm link sự kiện...")
                
                # Thử tìm dữ liệu từ JavaScript trong trang
                scripts = soup.find_all('script')
                for script in scripts:
                    script_text = script.string
                    if script_text and 'eventList' in script_text:
                        print("Tìm thấy dữ liệu sự kiện trong JavaScript")
                        # Lưu script để debug
                        with open('event_script.js', 'w', encoding='utf-8') as f:
                            f.write(script_text)
            
            if not event_links:
                print("Không thể tìm thấy liên kết sự kiện bằng các phương pháp tự động!")
                # Lưu toàn bộ HTML để kiểm tra thủ công
                with open(f'full_page_{page}.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"Đã lưu toàn bộ trang vào file full_page_{page}.html")
            
            # Danh sách sự kiện với CSS selectors mới
            events = soup.select('.sc-12dd4e85-1')
            print(f"Tìm thấy {len(events)} sự kiện trên trang {page}")
            
            if not events:
                print(f"Không tìm thấy sự kiện nào ở trang {page}")
                break
            
            for event in events:
                try:
                    # Trích xuất thông tin cơ bản với CSS selectors mới
                    name_elem = event.select_one('.text-title')
                    name = name_elem.text.strip() if name_elem else "Chưa có tên"
                    
                    img_elem = event.select_one('img')
                    img_url = img_elem['src'] if img_elem else ""
                    
                    # Tìm thông tin ngày tháng
                    date_elem = event.select_one('.text-normal span')
                    event_time = date_elem.text.strip() if date_elem else ""
                    
                    # Địa điểm có thể không có trên trang danh sách
                    event_location = "Không có thông tin địa điểm"                    # Lấy URL chi tiết sự kiện từ danh sách đã lưu trước đó
                    detail_link = None
                    if name in event_links:
                        detail_link = event_links[name]
                        print(f"Tìm thấy link từ danh sách đã lưu: {detail_link}")
                    else:
                        # Phương án dự phòng 1: Tìm tất cả các thẻ a chứa tiêu đề sự kiện
                        if name_elem:
                            event_title_text = name_elem.text.strip()
                            for title, link in event_links.items():
                                # So sánh một phần của tiêu đề (để xử lý trường hợp tiêu đề dài bị cắt)
                                if event_title_text in title or title in event_title_text:
                                    detail_link = link
                                    print(f"Tìm thấy link gần đúng: {detail_link}")
                                    break
                        
                        # Phương án dự phòng 2: Xây dựng URL từ tiêu đề
                        if not detail_link and name:
                            # Tạo slug từ tiêu đề để tạo URL
                            import re
                            from unidecode import unidecode
                            
                            def create_slug(text):
                                # Chuyển đổi sang không dấu
                                text = unidecode(text)
                                # Chuyển tất cả sang chữ thường
                                text = text.lower()
                                # Thay thế các ký tự không phải chữ cái, số bằng dấu -
                                text = re.sub(r'[^a-z0-9]+', '-', text)
                                # Loại bỏ dấu - ở đầu và cuối
                                text = text.strip('-')
                                return text
                            
                            slug = create_slug(name)
                            detail_link = f"https://ticketbox.vn/event/{slug}"
                            print(f"Tạo URL từ tiêu đề: {detail_link}")
                    
                    if not detail_link:
                        print(f"Không thể tìm được link chi tiết cho sự kiện: {name}")
                        continue
                    
                    print(f"\nTìm thấy sự kiện: {name}")
                    print(f"URL chi tiết: {detail_link}")
                    
                    # Kiểm tra sự kiện đã tồn tại
                    if Event.objects.filter(title=name, location=event_location).exists():
                        print(f"Sự kiện '{name}' đã tồn tại trong cơ sở dữ liệu, bỏ qua.")
                        continue
                      # Crawl trang chi tiết
                    print(f"Đang truy cập trang chi tiết: {detail_link}")
                    try:
                        driver.get(detail_link)
                        
                        # Chờ trang chi tiết tải với timeout dài hơn
                        try:
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
                            )
                            print("Trang chi tiết đã tải xong")
                        except TimeoutException:
                            print("Timeout khi tải trang chi tiết")
                            # Lưu trang để debug
                            with open(f'detail_debug_{events_crawled}.html', 'w', encoding='utf-8') as f:
                                f.write(driver.page_source)
                            print(f"Đã lưu nội dung trang chi tiết vào file detail_debug_{events_crawled}.html để debug")
                        
                        # Lấy dữ liệu sau khi trang đã tải
                        detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        
                        # Trích xuất mô tả với CSS selectors mới
                        description = ""
                        # Trong trang chi tiết thường có nhiều phần chứa mô tả, thử nhiều selectors
                        description_selectors = [
                            '.event-description',  # Thử selector chung cho mô tả
                            '.event-content',      # Thử selector cho nội dung sự kiện
                            '.sc-ea3bc0cc-0',      # Thử selector cụ thể theo cấu trúc mới
                            '[data-detail="description"]', # Thử selector dựa trên thuộc tính data
                            '.sc-bf5a1139-0',      # Selector chi tiết sự kiện mới
                            '.rich-text',          # Class chung cho nội dung rich text
                            'article',             # Tìm thẻ article nếu có
                            '.sc-a6a7fe23-0'       # Một selector khác ở trang chi tiết
                        ]
                        
                        for selector in description_selectors:
                            description_div = detail_soup.select_one(selector)
                            if description_div:
                                description = str(description_div)
                                print(f"Tìm thấy mô tả với selector: {selector}")
                                break
                        
                        # Nếu không tìm thấy mô tả, lấy tiêu đề làm mô tả đơn giản
                        if not description:
                            description = f"<div><p>Sự kiện: {name}</p></div>"
                            print("Không tìm thấy mô tả, sử dụng tiêu đề mặc định")
                            
                        # Thử trích xuất thông tin địa điểm từ trang chi tiết
                        location_selectors = [
                            '.venue-info',        # Selector thông tin địa điểm
                            '.event-venue',       # Selector khác cho địa điểm
                            '.location-info',     # Selector khác cho địa điểm
                            '.sc-76cbfcea-0',     # Selector cụ thể từ cấu trúc mới
                            '[data-detail="venue"]' # Selector dựa trên thuộc tính data
                        ]
                        
                        for selector in location_selectors:
                            location_div = detail_soup.select_one(selector)
                            if location_div:
                                # Trích xuất thông tin địa điểm
                                event_location = location_div.text.strip()
                                print(f"Tìm thấy địa điểm: {event_location}")
                                break
                            
                    except Exception as e:
                        print(f"Lỗi khi xử lý trang chi tiết: {e}")
                        # Nếu có lỗi, vẫn tiếp tục với thông tin đã có
                    
                    # Lấy thêm thông tin về ban tổ chức (nếu có)
                    organizer_name = ""
                    organizer_description = ""
                    
                    # Cập nhật các selectors cho thông tin nhà tổ chức
                    organizer_selectors = [
                        '.organizer-info',  # Thử selector chung cho thông tin nhà tổ chức
                        '.event-organizer', # Thử selector khác
                        '.sc-7264da03-0'    # Thử selector cụ thể theo cấu trúc mới
                    ]
                    
                    for selector in organizer_selectors:
                        organizer_div = detail_soup.select_one(selector)
                        if organizer_div:
                            organizer_name_elem = organizer_div.select_one('h3, h4')
                            if organizer_name_elem:
                                organizer_name = organizer_name_elem.text.strip()
                            
                            organizer_desc_elem = organizer_div.select_one('p')
                            if organizer_desc_elem:
                                organizer_description = str(organizer_desc_elem)
                            break
                    
                    # Nếu không tìm được thông tin nhà tổ chức, sử dụng thông tin mặc định
                    if not organizer_name:
                        organizer_name = "Ticketbox"
                    
                    # Xác định thể loại
                    category_mapping = {
                        'music': 'concert',
                        'theater': 'theater',
                        'sport': 'sports',
                        'exhibition': 'other',
                        'workshop': 'other'
                    }
                    event_category = category_mapping.get(category, 'other')
                    
                    # Tải ảnh sự kiện
                    image_content = download_image(img_url, name)
                    
                    # Phân tích thời gian sự kiện
                    start_time = parse_date_time(event_time)
                    # Giả định thời gian kết thúc là 2 giờ sau khi bắt đầu
                    end_time = None
                    if start_time:
                        from datetime import timedelta
                        end_time = start_time + timedelta(hours=2)
                    
                    # Tạo sự kiện mới
                    new_event = Event(
                        title=name,
                        description=description,
                        category=event_category,
                        location=event_location,
                        organizer_name=organizer_name,
                        organizer_description=organizer_description
                    )
                    
                    # Gán ảnh nếu tải được
                    if image_content:
                        new_event.image = image_content
                    
                    # Lưu sự kiện
                    new_event.save()
                    
                    # Tạo session cho sự kiện
                    if start_time and end_time:
                        EventSession.objects.create(
                            event=new_event,
                            start_time=start_time,
                            end_time=end_time,
                            is_active=True
                        )
                    
                    print(f"Đã lưu sự kiện: {name}")
                    events_crawled += 1
                    
                except Exception as e:
                    print(f"Lỗi khi xử lý sự kiện: {e}")
                    continue
            
            # Đợi một chút trước khi chuyển trang
            time.sleep(2)
        
        print(f"\nHoàn tất! Đã crawl và lưu {events_crawled} sự kiện.")
        
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
    
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    # Danh sách các thể loại sẵn có trên Ticketbox
    categories = ['music', 'theater', 'sport', 'exhibition', 'workshop']
    
    # Chọn loại sự kiện muốn crawl
    selected_category = 'music'  # Thay đổi nếu muốn crawl thể loại khác
    max_pages = 2  # Số trang tối đa muốn crawl
    
    crawl_ticketbox(category=selected_category, max_pages=max_pages)
