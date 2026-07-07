import json
import pathlib
import urllib.request


BASE_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"
REFERER = "https://www.dhlottery.co.kr/lt645/result"
OUT_FILE = pathlib.Path("lotto-history-data.js")
LATEST = 1231


def fetch_batch(params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{BASE_URL}?{query}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": REFERER,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["data"]["list"]


def normalize(item):
    return {
        "round": int(item["ltEpsd"]),
        "date": item["ltRflYmd"],
        "numbers": [
            int(item["tm1WnNo"]),
            int(item["tm2WnNo"]),
            int(item["tm3WnNo"]),
            int(item["tm4WnNo"]),
            int(item["tm5WnNo"]),
            int(item["tm6WnNo"]),
        ],
        "bonus": int(item["bnsWnNo"]),
    }


def main():
    entries = []
    seen = set()

    batch = fetch_batch({"srchDir": "center", "srchLtEpsd": LATEST})
    if not batch:
        raise SystemExit("Failed to fetch the latest lotto batch.")

    while batch:
        # The API returns the latest 10 for center, then older batches as we page back.
        for item in batch:
            round_no = int(item["ltEpsd"])
            if round_no in seen:
                continue
            seen.add(round_no)
            entries.append(normalize(item))

        oldest = min(int(item["ltEpsd"]) for item in batch)
        if oldest <= 1:
            break

        batch = fetch_batch({"srchDir": "older", "srchCursorLtEpsd": oldest})

    entries.sort(key=lambda item: item["round"])

    OUT_FILE.write_text(
        "window.LOTTO_HISTORY = "
        + json.dumps(entries, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(entries)} lotto rounds to {OUT_FILE}")


if __name__ == "__main__":
    main()
