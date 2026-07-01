(.venv) trading-bot@trading-bot-VMware-Virtual-Platform:~/trading-bot$ python phase3_external_data/scripts/smoke_test.py --epic IX.D.STXE.IFM.IP --volume-proxy EXW1.DE
epic=IX.D.STXE.IFM.IP  yf=^STOXX50E  market_open=True  volume_proxy=EXW1.DE
methods:
  drift           : DriftResult(ticker='^STOXX50E', today_open=6325.68017578125, current_price=6277.43994140625, drift_pct=-0.7626094433242844, as_of='2026-07-01T13:10:00.000Z', is_realtime=False)
  momentum_15m    : MomentumResult(ticker='^STOXX50E', window_minutes=15, momentum_pct=-0.20079082053860473, price_now=6277.43994140625, price_start=6290.06982421875, as_of='2026-07-01T13:10:00.000Z', source_resolution='5m', is_realtime=False)
  bars(5m,5)      : 5 bars
  history(30d)    : 5 bars
  volume_anomaly  : VolumeAnomaly(ticker='^STOXX50E', today_volume=188152.0, rolling_mean=1369450.5333333334, rolling_std=2240017.35587112, z_score=-0.5273613305884134, is_anomaly=False, is_extreme=False, lookback_days=30, as_of='2026-06-30T22:00:00.000Z', volume_available=True, volume_source='EXW1.DE')
  high_low        : HighLowDistance(ticker='^STOXX50E', lookback_days=90, rolling_high=6329.419921875, rolling_low=6181.93017578125, current_price=6277.43994140625, distance_to_high_pct=0.8280442497886428, distance_to_low_pct=1.5214763743897204, is_near_high=True, is_near_low=False, as_of='2026-06-30T22:00:00.000Z')
  brain_context   : BrainContext(ticker='IX.D.STXE.IFM.IP', yf_symbol='^STOXX50E', drift=DriftResult(ticker='^STOXX50E', today_open=6325.68017578125, current_price=6277.43994140625, drift_pct=-0.7626094433242844, as_of='2026-07-01T13:10:00.000Z', is_realtime=False), momentum_15m=MomentumResult(ticker='^STOXX50E', window_minutes=15, momentum_pct=-0.20079082053860473, price_now=6277.43994140625, price_start=6290.06982421875, as_of='2026-07-01T13:10:00.000Z', source_resolution='5m', is_realtime=False), volume=VolumeAnomaly(ticker='^STOXX50E', today_volume=188152.0, rolling_mean=1369450.5333333334, rolling_std=2240017.35587112, z_score=-0.5273613305884134, is_anomaly=False, is_extreme=False, lookback_days=30, as_of='2026-06-30T22:00:00.000Z', volume_available=True, volume_source='EXW1.DE'), high_low=HighLowDistance(ticker='^STOXX50E', lookback_days=90, rolling_high=6329.419921875, rolling_low=6181.93017578125, current_price=6277.43994140625, distance_to_high_pct=0.8280442497886428, distance_to_low_pct=1.5214763743897204, is_near_high=True, is_near_low=False, as_of='2026-06-30T22:00:00.000Z'), price_history_30d=[PriceBar(ts='2026-06-24T22:00:00.000Z', open=6211.56982421875, high=6279.52978515625, low=6211.56982421875, close=6267.52978515625, volume=22517200.0), PriceBar(ts='2026-06-25T22:00:00.000Z', open=6261.39013671875, high=6261.39013671875, low=6181.93017578125, close=6221.5498046875, volume=19255900.0), PriceBar(ts='2026-06-28T22:00:00.000Z', open=6224.740234375, high=6240.0, low=6202.490234375, close=6231.6298828125, volume=18393200.0), PriceBar(ts='2026-06-29T22:00:00.000Z', open=6247.85009765625, high=6329.419921875, low=6247.85009765625, close=6328.08984375, volume=24809500.0), PriceBar(ts='2026-06-30T22:00:00.000Z', open=6325.68017578125, high=6327.919921875, low=6275.8798828125, close=6277.43994140625, volume=0.0)], generated_at='2026-07-01T13:25:46.915Z')
{
  "ticker": "IX.D.STXE.IFM.IP",
  "drift_pct": -0.7626094433242844,
  "momentum_15m_pct": -0.20079082053860473,
  "momentum_is_realtime": false,
  "volume_z_score": -0.5273613305884134,
  "volume_available": true,
  "distance_to_high_pct": 0.8280442497886428,
  "distance_to_low_pct": 1.5214763743897204,
  "range_30d": {
    "low": 6181.93017578125,
    "high": 6329.419921875
  },
  "generated_at": "2026-07-01T13:25:46.915Z"
}
(.venv) trading-bot@trading-bot-VMware-Virtual-Platform:~/trading-bot$ python scripts/resolve_epics.py --term "France 40" --term "Netherlands 25" --term "Spain 35" --pace-s 1.0
[resolve] read-only epic resolution (no order, no writes)
[resolve] 'France 40': 4 hit(s)
    IX.D.CAC.IFD.IP  | 'Frankreich 40 Kassa (10€)' | EUR | min=1.0 lot=10.0 | TRADEABLE | ohlcv=yes
    IX.D.CAC.IFM.IP  | 'Frankreich 40 Kassa (2€)' | EUR | min=1.0 lot=2.0 | TRADEABLE | ohlcv=yes
    IX.D.CAC.FWM2.IP  | 'Frankreich 40 (2€)' | EUR | min=1.0 lot=2.0 | TRADEABLE | ohlcv=yes
    IX.D.CAC.IFE.IP  | 'Frankreich 40 Kassa (1€)' | EUR | min=1.0 lot=1.0 | TRADEABLE | ohlcv=yes
[resolve] 'Netherlands 25': no hits
[resolve] 'Spain 35': 4 hit(s)
    IX.D.IBEX.IFD.IP  | 'Spanien 35 Kassa (10€)' | EUR | min=0.5 lot=10.0 | TRADEABLE | ohlcv=yes
    IX.D.IBEX.IFM.IP  | 'Spanien 35 Kassa (2€)' | EUR | min=0.5 lot=2.0 | TRADEABLE | ohlcv=yes
    IX.D.IBEX.FWS2.IP  | 'Spanien 35 (10€)' | EUR | min=0.1 lot=10.0 | TRADEABLE | ohlcv=yes
    IX.D.IBEX.FWM2.IP  | 'Spanien 35 (2€)' | EUR | min=0.5 lot=2.0 | TRADEABLE | ohlcv=yes
[resolve] NOTE: point_value is NOT resolved here — confirm it manually per instrument.
{
  "broker": "ig_demo",
  "connected": true,
  "report": [
    {
      "term": "France 40",
      "search_ok": true,
      "error": null,
      "hits": [
        {
          "epic": "IX.D.CAC.IFD.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Frankreich 40 Kassa (10\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 1.0,
          "lot_size": 10.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.CAC.IFM.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Frankreich 40 Kassa (2\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 1.0,
          "lot_size": 2.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.CAC.FWM2.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Frankreich 40 (2\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 1.0,
          "lot_size": 2.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.CAC.IFE.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Frankreich 40 Kassa (1\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 1.0,
          "lot_size": 1.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        }
      ]
    },
    {
      "term": "Netherlands 25",
      "search_ok": true,
      "error": null,
      "hits": []
    },
    {
      "term": "Spain 35",
      "search_ok": true,
      "error": null,
      "hits": [
        {
          "epic": "IX.D.IBEX.IFD.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Spanien 35 Kassa (10\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 10.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.IBEX.IFM.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Spanien 35 Kassa (2\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 2.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.IBEX.FWS2.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Spanien 35 (10\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.1,
          "lot_size": 10.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.IBEX.FWM2.IP",
          "market_info_ok": true,
          "market_info_error": null,
          "name": "Spanien 35 (2\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 2.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        }
      ]
    }
  ]
}

