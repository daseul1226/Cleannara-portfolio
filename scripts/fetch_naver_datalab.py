import json
import os
import urllib.request
from datetime import date, timedelta, datetime
from pathlib import Path


API_URL = "https://openapi.naver.com/v1/datalab/search"

KEYWORD_GROUPS = [
    {
        "groupName": "물티슈",
        "keywords": ["물티슈", "아기 물티슈", "휴대용 물티슈"],
        "seasonMonths": [6, 7, 8],
        "seasonBonus": 12,
    },
    {
        "groupName": "화장지",
        "keywords": ["화장지", "휴지", "두루마리 휴지"],
        "seasonMonths": [11, 12, 1, 2],
        "seasonBonus": 6,
    },
    {
        "groupName": "키친타월",
        "keywords": ["키친타월", "주방타월", "키친타올"],
        "seasonMonths": [9, 10, 11, 12],
        "seasonBonus": 8,
    },
    {
        "groupName": "미용티슈",
        "keywords": ["미용티슈", "각티슈", "티슈"],
        "seasonMonths": [11, 12, 1, 2, 3],
        "seasonBonus": 7,
    },
]


def average(values):
    return sum(values) / len(values) if values else 0.0


def clamp(value, low, high):
    return max(low, min(high, value))


def season_bonus(group, month):
    return group["seasonBonus"] if month in group["seasonMonths"] else 0


def fetch_trends(client_id, client_secret):
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    payload = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "timeUnit": "month",
        "keywordGroups": [
            {"groupName": group["groupName"], "keywords": group["keywords"]}
            for group in KEYWORD_GROUPS
        ],
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(API_URL, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8")), payload


def build_output(api_data, payload):
    current_month = date.today().month
    products = []

    for result, group in zip(api_data.get("results", []), KEYWORD_GROUPS):
        ratios = [float(item["ratio"]) for item in result.get("data", [])]
        last3 = ratios[-3:] if len(ratios) >= 3 else ratios
        prev3 = ratios[-6:-3] if len(ratios) >= 6 else ratios[:-3]
        last3_avg = round(average(last3), 2)
        prev3_avg = round(average(prev3), 2)
        raw_momentum = ((last3_avg - prev3_avg) / max(prev3_avg, 1)) * 100
        momentum = round(clamp(raw_momentum, -100, 200), 2)
        bonus = season_bonus(group, current_month)
        score = round(last3_avg * 0.6 + max(momentum, 0) * 0.25 + bonus, 2)

        products.append(
            {
                "name": result.get("title", group["groupName"]),
                "keywords": group["keywords"],
                "last3Avg": last3_avg,
                "prev3Avg": prev3_avg,
                "momentum": momentum,
                "seasonBonus": bonus,
                "score": score,
            }
        )

    ranked = sorted(products, key=lambda item: item["score"], reverse=True)
    top = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None

    recommendation = {
        "priorityProduct": top["name"] if top else "데이터 없음",
        "priorityMessage": (
            f"이번 시기에는 {top['name']} 중심으로 프로모션을 우선 제안할 수 있습니다."
            if top
            else "추천 데이터를 계산하지 못했습니다."
        ),
        "regionalMessage": "지역 추천은 내부 판매 데이터와 결합 시 고도화됩니다.",
        "promoMessage": (
            f"{second['name']}는 보조 판촉군으로 함께 운영을 검토할 수 있습니다."
            if second
            else "보조 판촉군 데이터가 충분하지 않습니다."
        ),
    }

    return {
        "source": "naver-datalab",
        "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "dateRange": {
            "startDate": payload["startDate"],
            "endDate": payload["endDate"],
            "timeUnit": payload["timeUnit"],
        },
        "products": ranked,
        "recommendation": recommendation,
    }


def main():
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET must be set.")

    api_data, payload = fetch_trends(client_id, client_secret)
    output = build_output(api_data, payload)

    out_path = Path("assets/data/datalab.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
