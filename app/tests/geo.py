from geopy.geocoders import Nominatim


def get_coordinates(address: str):
    """
    Lấy tọa độ latitude và longitude từ địa chỉ
    """
    geolocator = Nominatim(user_agent="appcuuho")
    location = geolocator.geocode(address)

    if location:
        print(f"Địa chỉ: {address}")
        print(f"Địa chỉ đầy đủ: {location.address}")
        print(f"Latitude: {location.latitude}")
        print(f"Longitude: {location.longitude}")
        return location.latitude, location.longitude
    else:
        print(f"Không tìm thấy tọa độ cho địa chỉ: {address}")
        return None, None


if __name__ == "__main__":
    address = "Phước Sơn, Quảng Nam, Việt Nam"
    lat, lon = get_coordinates(address)
