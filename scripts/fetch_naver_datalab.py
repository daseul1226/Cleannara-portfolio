import json
import os
import urllib.request
from datetime import date, timedelta, datetime
from pathlib import Path


API_URL = "https://openapi.naver.com/v1/datalab/search"

CATEGORIES = [
    {
        "id": "toilet-tissue",
        "name": "화장지",
        "seasonMonths": [11, 12, 1, 2, 3],
        "seasonBonus": 8,
        "seasonNote": "사계절 수요가 높고 환절기·연말 수요가 강한 카테고리",
        "brands": [
            {"brand": "깨끗한나라", "keywords": ["깨끗한나라 화장지", "깨끗한나라 휴지", "깨끗한나라 두루마리휴지"]},
            {"brand": "크리넥스", "keywords": ["크리넥스 화장지", "크리넥스 휴지", "크리넥스 두루마리휴지"]},
            {"brand": "커클랜드", "keywords": ["커클랜드 화장지", "커클랜드 휴지", "코스트코 화장지", "커클랜드 두루마리휴지"]},
            {"brand": "잘풀리는집", "keywords": ["잘풀리는집 화장지", "잘풀리는집 휴지", "잘풀리는집 두루마리휴지"]},
        ],
    },
    {
        "id": "wet-wipes",
        "name": "물티슈",
        "seasonMonths": [5, 6, 7, 8, 9],
        "seasonBonus": 12,
        "seasonNote": "여름철·야외활동 시즌에 수요가 높아지는 카테고리",
        "brands": [
            {"brand": "깨끗한나라", "keywords": ["깨끗한나라 물티슈", "깨끗한나라 아기물티슈"]},
            {"brand": "크리넥스", "keywords": ["크리넥스 물티슈", "크리넥스 아기물티슈"]},
            {"brand": "커클랜드", "keywords": ["커클랜드 물티슈", "커클랜드 아기물티슈"]},
            {"brand": "잘풀리는집", "keywords": ["잘풀리는집 물티슈", "잘풀리는집 아기물티슈"]},
        ],
    },
    {
        "id": "kitchen-towel",
        "name": "키친타월",
        "seasonMonths": [9, 10, 11, 12],
        "seasonBonus": 6,
        "seasonNote": "명절·집밥·청소 이슈와 함께 관심이 높아지는 카테고리",
        "brands": [
            {"brand": "깨끗한나라", "keywords": ["깨끗한나라 키친타월", "깨끗한나라 키친타올"]},
            {"brand": "크리넥스", "keywords": ["크리넥스 키친타월", "크리넥스 키친타올"]},
            {"brand": "커클랜드", "keywords": ["커클랜드 키친타월", "코스트코 키친타월", "커클랜드 키친타올"]},
            {"brand": "잘풀리는집", "keywords": ["잘풀리는집 키친타월", "잘풀리는집 키친타올"]},
        ],
    },
    {
        "id": "facial-tissue",
        "name": "미용티슈",
        "seasonMonths": [10, 11, 12, 1, 2, 3],
        "seasonBonus": 7,
        "seasonNote": "환절기·감기 시즌과 함께 수요가 커지는 카테고리",
        "brands": [
            {"brand": "깨끗한나라", "keywords": ["깨끗한나라 미용티슈", "깨끗한나라 각티슈"]},
            {"brand": "크리넥스", "keywords": ["크리넥스 미용티슈", "크리넥스 각티슈"]},
            {"brand": "커클랜드", "keywords": ["커클랜드 미용티슈", "커클랜드 티슈"]},
            {"brand": "잘풀리는집", "keywords": ["잘풀리는집 미용티슈", "잘풀리는집 각티슈"]},
        ],
    },
]


def average(values):
    return sum(values) / len(values) if values else 0.0


def clamp(value, low, high):
    return max(low, min(high, value))


def season_bonus(category, month):
    return category["seasonBonus"] if month in category["seasonMonths"] else 0


def fetch_category_trends(client_id, client_secret, category):
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    payload = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "timeUnit": "month",
        "keywordGroups": [
            {"groupName": brand["brand"], "keywords": brand["keywords"]}
            for brand in category["brands"]
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(API_URL, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8")), payload


def build_category_result(category, api_data):
    month = date.today().month
    products = []

    for result, brand in zip(api_data.get("results", []), category["brands"]):
        ratios = [float(item["ratio"]) for item in result.get("data", [])]
        last3 = ratios[-3:] if len(ratios) >= 3 else ratios
        prev3 = ratios[-6:-3] if len(ratios) >= 6 else ratios[:-3]
        last3_avg = round(average(last3), 2)
        prev3_avg = round(average(prev3), 2)
        raw_momentum = ((last3_avg - prev3_avg) / max(prev3_avg, 1)) * 100
        momentum = round(clamp(raw_momentum, -100, 200), 2)
        bonus = season_bonus(category, month)
        score = round(last3_avg * 0.6 + max(momentum, 0) * 0.25 + bonus, 2)

        products.append(
            {
                "brand": brand["brand"],
                "keywords": brand["keywords"],
                "last3Avg": last3_avg,
                "prev3Avg": prev3_avg,
                "momentum": momentum,
                "score": score,
            }
        )

    ranked = sorted(products, key=lambda item: item["score"], reverse=True)
    leader = ranked[0]["brand"] if ranked else "데이터 없음"

    return {
        "id": category["id"],
        "name": category["name"],
        "seasonNote": category["seasonNote"],
        "leader": leader,
        "products": ranked,
    }


def build_output(all_results, payload_template):
    categories = []
    for category, api_data in all_results:
        categories.append(build_category_result(category, api_data))

    category_rank = sorted(
        categories,
        key=lambda item: item["products"][0]["score"] if item["products"] else 0,
        reverse=True,
    )

    top_category = category_rank[0] if category_rank else None
    top_product = top_category["products"][0] if top_category and top_category["products"] else None
    clean_product = (
        next((item for item in top_category["products"] if item["brand"] == "깨끗한나라"), None)
        if top_category and top_category["products"]
        else None
    )
    second_product = (
        top_category["products"][1]
        if top_category and top_category["products"] and len(top_category["products"]) > 1
        else None
    )
    clean_gap = (
        round((top_product["score"] - clean_product["score"]), 1)
        if top_product and clean_product
        else 0
    )

    recommendation = {
        "priorityCategory": top_category["name"] if top_category else "데이터 없음",
        "priorityBrand": top_product["brand"] if top_product else "데이터 없음",
        "priorityMessage": (
            (
                f"{top_category['name']} 카테고리는 최근 검색 반응이 가장 빠르게 커지는 영역으로, 깨끗한나라가 영업 자원을 먼저 집중해 진열 점유율과 고객 선택률을 확대할 우선 공략 카테고리입니다."
                if top_category
                else "추천 데이터를 계산하지 못했습니다."
            )
            if top_category
            else "추천 데이터를 계산하지 못했습니다."
        ),
        "regionalMessage": (
            (
                f"{top_category['name']}에서는 현재 {top_product['brand']}가 검색 존재감을 선점하고 있어, 깨끗한나라는 비교 진열, 묶음 구성, 핵심 USP 메시지 강화로 고객 선택을 전환해야 합니다. 현재 선도 브랜드와의 점수 차이는 {clean_gap}p입니다."
                if top_category and top_product and clean_product and top_product["brand"] != "깨끗한나라"
                else f"{top_category['name']}에서는 깨끗한나라가 이미 반응 우위에 있으므로, 대표 SKU 노출을 유지하면서 2위 브랜드인 {second_product['brand']}의 추격을 막는 방어형 점유율 확대 전략이 유효합니다."
                if top_category and clean_product and top_product and top_product["brand"] == "깨끗한나라" and second_product
                else "점유율 전환 전략 데이터를 계산하지 못했습니다."
            )
            if top_category
            else "점유율 전환 전략 데이터를 계산하지 못했습니다."
        ),
        "promoMessage": (
            f"대리점·농협 채널에서는 {top_category['name']} 핵심 SKU를 전면 배치하고, 입수량 행사, 시즌성 묶음 프로모션, 생활밀착형 메시지를 연동해 실제 구매 전환까지 이어지도록 실행하는 것이 효과적입니다."
            if top_category
            else "우선 판촉 카테고리 데이터를 계산하지 못했습니다."
        ),
    }

    return {
        "source": "naver-datalab",
        "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "dateRange": {
            "startDate": payload_template["startDate"],
            "endDate": payload_template["endDate"],
            "timeUnit": payload_template["timeUnit"],
        },
        "brands": ["깨끗한나라", "크리넥스", "커클랜드", "잘풀리는집"],
        "categories": categories,
        "recommendation": recommendation,
    }


def main():
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET must be set.")

    all_results = []
    payload_template = None

    for category in CATEGORIES:
        api_data, payload = fetch_category_trends(client_id, client_secret, category)
        payload_template = payload
        all_results.append((category, api_data))

    output = build_output(all_results, payload_template)

    out_path = Path("assets/data/datalab.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
