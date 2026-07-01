(.venv) trading-bot@trading-bot-VMware-Virtual-Platform:~/trading-bot$ python scripts/resolve_epics.py
[resolve] read-only epic resolution (no order, no writes)
[resolve] 'Germany 40': 7 hit(s)
    IX.D.DAX.IFMM.IP  | 'Deutschland 40-Kassa (1 €)' | EUR | min=0.5 lot=1.0 | TRADEABLE | ohlcv=yes
    IX.D.DAX.IFD.IP  | 'Deutschland 40-Kassa (25 €)' | EUR | min=0.1 lot=25.0 | TRADEABLE | ohlcv=yes
    IX.D.DAX.IFMG.IP  | 'Deutschland 40-Kassa (5 €)' | EUR | min=0.5 lot=5.0 | TRADEABLE | ohlcv=yes
    IX.D.DAX.FWS2.IP  | 'Deutschland 40 (25 €)' | EUR | min=0.5 lot=25.0 | TRADEABLE | ohlcv=yes
    IX.D.DAX.FWM2.IP  | 'Deutschland 40 (5 €)' | EUR | min=0.5 lot=5.0 | TRADEABLE | ohlcv=yes
    IX.D.DAX.IGN.IP  | 'Deutschland 40-Kassa (1 €)' | EUR | min=0.5 lot=1.0 | TRADEABLE | ohlcv=yes
    IX.D.SUNDAX.IFMM.IP  | 'Wochenend-Deutschland 40-Kassa (1€)' | EUR | min=2.0 lot=1.0 | EDITS_ONLY | ohlcv=yes
[resolve] 'EU Stocks 50': 5 hit(s)
    IX.D.STXE.IFD.IP  | 'EU Stocks 50 Kassa (10€)' | EUR | min=0.5 lot=10.0 | TRADEABLE | ohlcv=yes
    IX.D.STXE.IFM.IP  | 'EU Stocks 50 Kassa (2€)' | EUR | min=0.5 lot=2.0 | TRADEABLE | ohlcv=yes
    IX.D.STXE.FWS2.IP  | 'EU Stocks 50 (10€)' | EUR | min=0.5 lot=10.0 | TRADEABLE | ohlcv=yes
    IX.D.STXE.FWM2.IP  | 'EU Stocks 50 (2€)' | EUR | min=0.5 lot=2.0 | TRADEABLE | ohlcv=yes
    IX.D.StoxxBank.FNI2.IP  | 'EU Stocks Banks Index (50 EUR)' | EUR | min=1.0 lot=50.0 | TRADEABLE | ohlcv=yes
[resolve] 'France 40': 4 hit(s)
    IX.D.CAC.IFD.IP  | 'Frankreich 40 Kassa (10€)' | EUR | min=1.0 lot=10.0 | TRADEABLE | ohlcv=no
    IX.D.CAC.IFM.IP  | None | None | min=None lot=None | None | ohlcv=no
    IX.D.CAC.FWM2.IP  | None | None | min=None lot=None | None | ohlcv=no
    IX.D.CAC.IFE.IP  | None | None | min=None lot=None | None | ohlcv=no
[resolve] 'Netherlands 25': search FAILED (None)
[resolve] 'Spain 35': search FAILED (None)
[resolve] NOTE: point_value is NOT resolved here — confirm it manually per instrument.
{
  "broker": "ig_demo",
  "connected": true,
  "report": [
    {
      "term": "Germany 40",
      "search_ok": true,
      "error": null,
      "hits": [
        {
          "epic": "IX.D.DAX.IFMM.IP",
          "market_info_ok": true,
          "name": "Deutschland 40-Kassa (1 \u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 1.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.DAX.IFD.IP",
          "market_info_ok": true,
          "name": "Deutschland 40-Kassa (25 \u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.1,
          "lot_size": 25.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.DAX.IFMG.IP",
          "market_info_ok": true,
          "name": "Deutschland 40-Kassa (5 \u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 5.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.DAX.FWS2.IP",
          "market_info_ok": true,
          "name": "Deutschland 40 (25 \u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 25.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.DAX.FWM2.IP",
          "market_info_ok": true,
          "name": "Deutschland 40 (5 \u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 5.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.DAX.IGN.IP",
          "market_info_ok": true,
          "name": "Deutschland 40-Kassa (1 \u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 1.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.SUNDAX.IFMM.IP",
          "market_info_ok": true,
          "name": "Wochenend-Deutschland 40-Kassa (1\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 2.0,
          "lot_size": 1.0,
          "market_status": "EDITS_ONLY",
          "ohlcv_available": true
        }
      ]
    },
    {
      "term": "EU Stocks 50",
      "search_ok": true,
      "error": null,
      "hits": [
        {
          "epic": "IX.D.STXE.IFD.IP",
          "market_info_ok": true,
          "name": "EU Stocks 50 Kassa (10\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 10.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.STXE.IFM.IP",
          "market_info_ok": true,
          "name": "EU Stocks 50 Kassa (2\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 2.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.STXE.FWS2.IP",
          "market_info_ok": true,
          "name": "EU Stocks 50 (10\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 10.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.STXE.FWM2.IP",
          "market_info_ok": true,
          "name": "EU Stocks 50 (2\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 0.5,
          "lot_size": 2.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        },
        {
          "epic": "IX.D.StoxxBank.FNI2.IP",
          "market_info_ok": true,
          "name": "EU Stocks Banks Index (50 EUR)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 1.0,
          "lot_size": 50.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": true
        }
      ]
    },
    {
      "term": "France 40",
      "search_ok": true,
      "error": null,
      "hits": [
        {
          "epic": "IX.D.CAC.IFD.IP",
          "market_info_ok": true,
          "name": "Frankreich 40 Kassa (10\u20ac)",
          "instrument_type": "INDICES",
          "currency": "EUR",
          "min_deal_size": 1.0,
          "lot_size": 10.0,
          "market_status": "TRADEABLE",
          "ohlcv_available": false
        },
        {
          "epic": "IX.D.CAC.IFM.IP",
          "market_info_ok": false,
          "name": null,
          "instrument_type": null,
          "currency": null,
          "min_deal_size": null,
          "lot_size": null,
          "market_status": null,
          "ohlcv_available": false
        },
        {
          "epic": "IX.D.CAC.FWM2.IP",
          "market_info_ok": false,
          "name": null,
          "instrument_type": null,
          "currency": null,
          "min_deal_size": null,
          "lot_size": null,
          "market_status": null,
          "ohlcv_available": false
        },
        {
          "epic": "IX.D.CAC.IFE.IP",
          "market_info_ok": false,
          "name": null,
          "instrument_type": null,
          "currency": null,
          "min_deal_size": null,
          "lot_size": null,
          "market_status": null,
          "ohlcv_available": false
        }
      ]
    },
    {
      "term": "Netherlands 25",
      "search_ok": false,
      "error": null,
      "hits": []
    },
    {
      "term": "Spain 35",
      "search_ok": false,
      "error": null,
      "hits": []
    }
  ]
}
(.venv) trading-bot@trading-bot-VMware-Virtual-Platform:~/trading-bot$ 





