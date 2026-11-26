#!/usr/bin/env python3
"""엑셀(정선해양 관측 vs 모델 매칭 보고서) -> data.js 변환 스크립트.

사용법:
    python3 build_data.py "data/정선해양_분석.xlsx" data.js

사용하는 시트: '상세_매칭_데이터'
사용하는 열  : 해역, 정선-정점, 위도(°N), 경도(°E), 관측일자, 관측수심(m),
              관측 수온(°C), 관측 염분(psu)
(모델 평균/최저/최고 열은 영역 전체 통계라 위치별 예측에는 쓰지 않습니다.)
"""
import json
import sys

import pandas as pd

DEPTHS = [0, 10, 20, 30, 50]


def main(xlsx, out):
    df = pd.read_excel(xlsx, sheet_name="상세_매칭_데이터", header=3)
    df = df.rename(columns={
        "해역": "area", "정선-정점": "sid", "위도(°N)": "lat", "경도(°E)": "lon",
        "관측수심(m)": "z", "관측 수온(°C)": "T", "관측 염분(psu)": "S",
    })
    df["date"] = pd.to_datetime(df["관측일자"])
    df["m"] = df.date.dt.month
    df = df.dropna(subset=["lat", "lon", "z", "T", "S"])

    stations = []
    for sid, g in df.groupby("sid", sort=True):
        st = {"id": sid, "a": g.area.iloc[0],
              "lat": round(float(g.lat.iloc[0]), 4),
              "lon": round(float(g.lon.iloc[0]), 4), "o": {}}
        for m, gm in g.groupby("m"):
            t = [None] * len(DEPTHS)
            s = [None] * len(DEPTHS)
            for _, r in gm.iterrows():
                zi = DEPTHS.index(int(r.z))
                t[zi] = round(float(r["T"]), 2)
                s[zi] = round(float(r["S"]), 2)
            st["o"][int(m)] = {"d": gm.date.min().strftime("%m-%d"), "t": t, "s": s}
        stations.append(st)

    meta = {
        "source": "KODC 정선해양 관측자료",
        "period": f"{df.date.min():%Y.%m.%d} ~ {df.date.max():%Y.%m.%d}",
        "stations": len(stations),
        "records": int(len(df)),
        "months": sorted(int(x) for x in df.m.unique()),
    }
    data = {"meta": meta, "depths": DEPTHS, "stations": stations}
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.OCEAN_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"{out}: 정점 {len(stations)}개, 관측 {len(df)}건")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
