import re
import unicodedata

# Province/city names present in this project's source/training data. Reject
# ambiguous or cross-province matches instead of placing misleading markers.
PROVINCE_NAMES = (
    "Bình Định", "Bắc Giang", "Bắc Kạn", "Bắc Ninh", "Cao Bằng", "Huế", "Hà Giang",
    "Hà Nam", "Hà Nội", "Hà Tĩnh", "Hải Phòng", "Lào Cai", "Lạng Sơn", "Nghệ An",
    "Phú Thọ", "Phú Yên", "Quảng Bình", "Quảng Nam", "Thanh Hóa", "Thái Bình",
    "Thái Nguyên", "Thừa Thiên Huế", "Vĩnh Long", "Vĩnh Phúc", "Điện Biên",
    "Đà Nẵng", "Đồng Nai", "Hồ Chí Minh", "Quảng Ninh", "Quảng Trị", "Quảng Ngãi",
    "Gia Lai", "Đắk Lắk", "Đắk Nông", "Khánh Hòa", "Lâm Đồng", "Bình Thuận",
    "Ninh Thuận", "Bình Dương", "Bình Phước", "Tây Ninh", "Long An", "Tiền Giang",
    "Bến Tre", "Trà Vinh", "Cần Thơ", "Hậu Giang", "Sóc Trăng", "Bạc Liêu",
    "Cà Mau", "An Giang", "Kiên Giang", "Đồng Tháp", "Ninh Bình", "Nam Định",
    "Hưng Yên", "Hải Dương", "Hòa Bình", "Sơn La", "Lai Châu", "Tuyên Quang",
    "Yên Bái", "Bắc Giang", "Bà Rịa", "Kon Tum",
)


def folded(text):
    value = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(char for char in value if unicodedata.category(char) != "Mn")


def expected_provinces(address):
    query = folded(address)
    names = {folded(name) for name in PROVINCE_NAMES
             if re.search(r"\b" + re.escape(folded(name)) + r"\b", query)}
    # These aliases occur together in the source corpus and Mapbox responses.
    if names & {"quang nam", "da nang"}:
        names.update(("quang nam", "da nang"))
    if names & {"hue", "thua thien hue"}:
        names.update(("hue", "thua thien hue"))
    if "ha noi" in names:
        names.add("hanoi")
    if "ho chi minh" in names:
        names.add("ho chi minh city")
    return names

