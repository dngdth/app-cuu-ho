// src/data/mockData.js
// Mock data based on RescueRequest database schema and API

export const mockIncidents = [
  {
    "id": 1,
    "title": "Ngập lụt nghiêm trọng tại Thôn Hồng Thủy, Quảng Bình",
    "location": "Thôn Hồng Thủy, Quảng Bình",
    "coordinate": {
      "type": "Point",
      "coordinates": [106.63, 17.48] // [longitude, latitude]
    },
    "content": "Ngập lụt nghiêm trọng, cần cứu trợ khẩn cấp. Nhiều hộ dân bị cô lập. Nước dâng nhanh, gây nguy hiểm cho người già và trẻ em. Cần hỗ trợ lương thực, nước uống và thuốc men.",
    "map_link": "https://www.google.com/maps?q=17.48,106.63",
    "status": "pending",
    "posted_time": "2h",
    "created_date": "2026-01-23T20:48:00Z",
    "image": "https://images.unsplash.com/photo-1567437259931-5232DE512492?q=80&w=1932",
    "urgency_score": 9.5,
    "reliability_score": 8.7,
    "contact": "0912345678",
    "region_id": 1,
    "affected_people": 450,
    "infrastructure_damage": true,
    "is_isolated": true,
    "deathly": false,
    "has_emergency": true,
    "has_emotion": true,
    "has_emphasis": true,
    "reactions": 234,
    "replies": 45,
    "needs_ids": [1, 2, 3], // Food, Water, Medicine
    "disaster_type_ids": [1] // Flood
  },
  {
    "id": 2,
    "title": "Sạt lở đất chia cắt tuyến đường tại Xã Pả Vi, Hà Giang",
    "location": "Xã Pả Vi, Hà Giang",
    "coordinate": {
      "type": "Point",
      "coordinates": [105.28, 23.23]
    },
    "content": "Sạt lở đất chia cắt tuyến đường chính. Một số nhà dân có nguy cơ bị vùi lấp. Cần máy móc để giải phóng mặt bằng. Khoảng 20 hộ dân bị cô lập hoàn toàn.",
    "map_link": "https://www.google.com/maps?q=23.23,105.28",
    "status": "in_progress",
    "posted_time": "5h",
    "created_date": "2026-01-23T17:48:00Z",
    "image": "https://images.unsplash.com/photo-1601636773954-4375986c7533?q=80&w=1964",
    "urgency_score": 8.2,
    "reliability_score": 9.1,
    "contact": "0923456789",
    "region_id": 2,
    "affected_people": 80,
    "infrastructure_damage": true,
    "is_isolated": true,
    "deathly": false,
    "has_emergency": true,
    "has_emotion": false,
    "has_emphasis": true,
    "reactions": 156,
    "replies": 28,
    "needs_ids": [4, 5], // Equipment, Shelter
    "disaster_type_ids": [2] // Landslide
  },
  {
    "id": 3,
    "title": "Bão số 9 gây thiệt hại nặng tại Đà Nẵng",
    "location": "Quận Hải Châu, Đà Nẵng",
    "coordinate": {
      "type": "Point",
      "coordinates": [108.22, 16.07]
    },
    "content": "Bão số 9 đã đổ bộ vào Đà Nẵng gây thiệt hại nặng nề. Nhiều nhà cửa bị tốc mái, cây đổ la liệt. Mất điện diện rộng. Cần hỗ trợ bạt che chắn, lương thực và nước uống.",
    "map_link": "https://www.google.com/maps?q=16.07,108.22",
    "status": "pending",
    "posted_time": "1d",
    "created_date": "2026-01-22T22:48:00Z",
    "image": "https://images.unsplash.com/photo-1527482797697-8795b05a13fe?q=80&w=2071",
    "urgency_score": 9.0,
    "reliability_score": 9.5,
    "contact": "0934567890",
    "region_id": 3,
    "affected_people": 1200,
    "infrastructure_damage": true,
    "is_isolated": false,
    "deathly": true,
    "has_emergency": true,
    "has_emotion": true,
    "has_emphasis": true,
    "reactions": 892,
    "replies": 134,
    "needs_ids": [1, 2, 5, 6], // Food, Water, Shelter, Clothing
    "disaster_type_ids": [3] // Storm/Typhoon
  },
  {
    "id": 4,
    "title": "Hạn hán kéo dài tại Ninh Thuận",
    "location": "Huyện Thuận Nam, Ninh Thuận",
    "coordinate": {
      "type": "Point",
      "coordinates": [108.99, 11.67]
    },
    "content": "Hạn hán kéo dài hơn 3 tháng. Nguồn nước sinh hoạt cạn kiệt. Mùa màng thất bát. Cần hỗ trợ nước sạch khẩn cấp cho người dân và gia súc.",
    "map_link": "https://www.google.com/maps?q=11.67,108.99",
    "status": "pending",
    "posted_time": "3d",
    "created_date": "2026-01-20T22:48:00Z",
    "image": "https://images.unsplash.com/photo-1595854341625-f33ee0e5e2e5?q=80&w=2070",
    "urgency_score": 7.5,
    "reliability_score": 8.0,
    "contact": "0945678901",
    "region_id": 4,
    "affected_people": 650,
    "infrastructure_damage": false,
    "is_isolated": false,
    "deathly": false,
    "has_emergency": false,
    "has_emotion": true,
    "has_emphasis": false,
    "reactions": 423,
    "replies": 67,
    "needs_ids": [2], // Water
    "disaster_type_ids": [4] // Drought
  },
  {
    "id": 5,
    "title": "Động đất 5.2 độ richter tại Lai Châu",
    "location": "Huyện Mường Tè, Lai Châu",
    "coordinate": {
      "type": "Point",
      "coordinates": [103.17, 22.38]
    },
    "content": "Động đất 5.2 độ richter xảy ra lúc 3h sáng. Nhiều nhà dân bị nứt tường, sập nhà. Người dân hoảng loạn. Cần kiểm tra và hỗ trợ khẩn cấp.",
    "map_link": "https://www.google.com/maps?q=22.38,103.17",
    "status": "resolved",
    "posted_time": "1w",
    "created_date": "2026-01-16T22:48:00Z",
    "image": "https://images.unsplash.com/photo-1587474260584-136574528ed5?q=80&w=2070",
    "urgency_score": 8.8,
    "reliability_score": 9.2,
    "contact": "0956789012",
    "region_id": 5,
    "affected_people": 320,
    "infrastructure_damage": true,
    "is_isolated": false,
    "deathly": false,
    "has_emergency": true,
    "has_emotion": true,
    "has_emphasis": true,
    "reactions": 567,
    "replies": 89,
    "needs_ids": [3, 5, 7], // Medicine, Shelter, Rescue team
    "disaster_type_ids": [5] // Earthquake
  },
  {
    "id": 6,
    "title": "Cháy rừng lan rộng tại Nghệ An",
    "location": "Huyện Quỳ Châu, Nghệ An",
    "coordinate": {
      "type": "Point",
      "coordinates": [105.13, 19.33]
    },
    "content": "Cháy rừng đã lan rộng hơn 50 hecta. Nguy cơ cháy lan sang khu dân cư. Cần huy động lực lượng chữa cháy và sơ tán dân.",
    "map_link": "https://www.google.com/maps?q=19.33,105.13",
    "status": "in_progress",
    "posted_time": "6h",
    "created_date": "2026-01-23T16:48:00Z",
    "image": "https://images.unsplash.com/photo-1603048588665-791ca8aea617?q=80&w=2070",
    "urgency_score": 9.3,
    "reliability_score": 8.9,
    "contact": "0967890123",
    "region_id": 6,
    "affected_people": 150,
    "infrastructure_damage": true,
    "is_isolated": false,
    "deathly": false,
    "has_emergency": true,
    "has_emotion": false,
    "has_emphasis": true,
    "reactions": 678,
    "replies": 112,
    "needs_ids": [7, 8], // Rescue team, Fire fighting equipment
    "disaster_type_ids": [6] // Forest fire
  },
  {
    "id": 7,
    "title": "Lũ quét tại Lào Cai",
    "location": "Huyện Bát Xát, Lào Cai",
    "coordinate": {
      "type": "Point",
      "coordinates": [103.97, 22.65]
    },
    "content": "Lũ quét cuốn trôi 5 căn nhà. 2 người mất tích. Cần tìm kiếm cứu nạn khẩn cấp. Nhiều hộ dân bị cô lập do cầu bị cuốn trôi.",
    "map_link": "https://www.google.com/maps?q=22.65,103.97",
    "status": "in_progress",
    "posted_time": "4h",
    "created_date": "2026-01-23T18:48:00Z",
    "image": "https://images.unsplash.com/photo-1547683905-f686c993aae5?q=80&w=2070",
    "urgency_score": 10.0,
    "reliability_score": 9.8,
    "contact": "0978901234",
    "region_id": 7,
    "affected_people": 200,
    "infrastructure_damage": true,
    "is_isolated": true,
    "deathly": true,
    "has_emergency": true,
    "has_emotion": true,
    "has_emphasis": true,
    "reactions": 1234,
    "replies": 203,
    "needs_ids": [1, 2, 3, 7], // Food, Water, Medicine, Rescue team
    "disaster_type_ids": [7] // Flash flood
  },
  {
    "id": 8,
    "title": "Triều cường gây ngập tại TP.HCM",
    "location": "Quận 7, TP. Hồ Chí Minh",
    "coordinate": {
      "type": "Point",
      "coordinates": [106.72, 10.73]
    },
    "content": "Triều cường kết hợp mưa lớn gây ngập nhiều tuyến đường. Giao thông tê liệt. Nước tràn vào nhà dân.",
    "map_link": "https://www.google.com/maps?q=10.73,106.72",
    "status": "pending",
    "posted_time": "30m",
    "created_date": "2026-01-23T22:18:00Z",
    "image": "https://images.unsplash.com/photo-1547683905-f686c993aae5?q=80&w=2070",
    "urgency_score": 6.5,
    "reliability_score": 7.8,
    "contact": "0989012345",
    "region_id": 8,
    "affected_people": 800,
    "infrastructure_damage": false,
    "is_isolated": false,
    "deathly": false,
    "has_emergency": false,
    "has_emotion": false,
    "has_emphasis": false,
    "reactions": 345,
    "replies": 56,
    "needs_ids": [9], // Drainage support
    "disaster_type_ids": [8] // Tidal flooding
  }
];

// Mock data for disaster types
export const mockDisasterTypes = [
  { "id": 1, "name": "Lũ lụt", "description": "Ngập lụt do mưa lớn hoặc nước sông dâng cao" },
  { "id": 2, "name": "Sạt lở đất", "description": "Đất đá trượt xuống gây nguy hiểm" },
  { "id": 3, "name": "Bão", "description": "Bão nhiệt đới, siêu bão" },
  { "id": 4, "name": "Hạn hán", "description": "Thiếu nước kéo dài" },
  { "id": 5, "name": "Động đất", "description": "Rung chuyển mặt đất" },
  { "id": 6, "name": "Cháy rừng", "description": "Cháy lan rộng trên diện tích rừng" },
  { "id": 7, "name": "Lũ quét", "description": "Lũ ống, lũ quét đột ngột" },
  { "id": 8, "name": "Triều cường", "description": "Nước biển dâng cao bất thường" }
];

// Mock data for needs
export const mockNeeds = [
  { "id": 1, "name": "Lương thực", "description": "Gạo, mì, thực phẩm khô" },
  { "id": 2, "name": "Nước uống", "description": "Nước sạch, nước đóng chai" },
  { "id": 3, "name": "Thuốc men", "description": "Thuốc cơ bản, dụng cụ y tế" },
  { "id": 4, "name": "Thiết bị", "description": "Máy móc, công cụ cứu hộ" },
  { "id": 5, "name": "Nơi trú ẩn", "description": "Lều bạt, chỗ ở tạm" },
  { "id": 6, "name": "Quần áo", "description": "Quần áo, chăn màn" },
  { "id": 7, "name": "Đội cứu hộ", "description": "Lực lượng tìm kiếm cứu nạn" },
  { "id": 8, "name": "Thiết bị chữa cháy", "description": "Máy bơm, vòi phun nước" },
  { "id": 9, "name": "Hỗ trợ thoát nước", "description": "Máy bơm nước, hệ thống thoát nước" }
];

// Mock data for regions
export const mockRegions = [
  { "id": 1, "parent_id": null, "name": "Quảng Bình" },
  { "id": 2, "parent_id": null, "name": "Hà Giang" },
  { "id": 3, "parent_id": null, "name": "Đà Nẵng" },
  { "id": 4, "parent_id": null, "name": "Ninh Thuận" },
  { "id": 5, "parent_id": null, "name": "Lai Châu" },
  { "id": 6, "parent_id": null, "name": "Nghệ An" },
  { "id": 7, "parent_id": null, "name": "Lào Cai" },
  { "id": 8, "parent_id": null, "name": "TP. Hồ Chí Minh" }
];

// Helper function to get disaster type names by IDs
export const getDisasterTypeNames = (ids) => {
  return ids.map(id => {
    const type = mockDisasterTypes.find(t => t.id === id);
    return type ? type.name : '';
  }).filter(name => name);
};

// Helper function to get needs names by IDs
export const getNeedsNames = (ids) => {
  return ids.map(id => {
    const need = mockNeeds.find(n => n.id === id);
    return need ? need.name : '';
  }).filter(name => name);
};

// Helper function to get region name by ID
export const getRegionName = (id) => {
  const region = mockRegions.find(r => r.id === id);
  return region ? region.name : '';
};

// Helper function to format urgency level
export const getUrgencyLevel = (score) => {
  if (score >= 8) return 'critical';
  if (score >= 6) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
};

// Helper function to format posted time
export const formatPostedTime = (timeStr) => {
  const units = {
    'm': 'phút',
    'h': 'giờ',
    'd': 'ngày',
    'w': 'tuần'
  };

  const match = timeStr.match(/^(\d+)([mhdw])$/);
  if (match) {
    return `${match[1]} ${units[match[2]]} trước`;
  }
  return timeStr;
};
