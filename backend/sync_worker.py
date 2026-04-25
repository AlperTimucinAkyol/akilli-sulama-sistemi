"""
sync_worker.py
==============
Arka planda çalışan periyodik iş parçacığı (thread).

Her SYNC_INTERVAL_SECONDS saniyede bir SQLite kuyruğunu kontrol eder.
Kuyrukta bekleyen kayıtlar varsa PostgreSQL'e aktarmayı dener.
Başarılıysa siler, başarısızsa yeniden deneme sayısını artırır.
"""

import time
import logging
import threading
from datetime import datetime

from database import SessionLocal
from db_utils import save_sensor_data, get_field_location
from decision import DecisionLogic
from models.iot import IrrigationLog
import offline_queue as oq

logger = logging.getLogger(__name__)

# Kaç saniyede bir kuyruk kontrol edilsin
SYNC_INTERVAL_SECONDS = 30


def _process_one(row: tuple) -> bool:
    """
    Tek bir kuyruk kaydını PostgreSQL pipeline'ına gönderir.
    Başarılıysa True, hata olursa False döner.
    """
    item_id, lora_id, moisture_value, received_at, retries = row
    db = SessionLocal()
    try:
        # 1) Sensör verisini kaydet
        node = save_sensor_data(lora_id, moisture_value, db)
        if node is None:
            logger.warning(
                f"[SyncWorker] {lora_id} kayıtlı değil, kuyruk kaydı {item_id} atlanıyor."
            )
            # Kayıtlı olmayan cihaz hiç çalışmaz → direkt sil
            oq.delete_item(item_id)
            return True

        # 2) Konum al
        location = get_field_location(node.field_id, db)

        # 3) Sulama kararı ver
        decision = DecisionLogic.decide_irrigation(float(moisture_value), location)
        pump_on = decision == "ON"

        # 4) IrrigationLog kaydet (orijinal received_at zamanını koru)
        original_time = datetime.fromisoformat(received_at)
        log = IrrigationLog(
            field_id=node.field_id,
            node_id=node.id,
            action=pump_on,
            mode=True,
            soil_moisture=float(moisture_value),
            decision_note=(
                f"[KUYRUKTAN] Nem: %{moisture_value}, Konum: {location}, "
                f"Karar: {'ON' if pump_on else 'OFF'}, Alındı: {received_at}"
            ),
            timestamp=original_time,
        )
        db.add(log)
        db.commit()

        logger.info(
            f"[SyncWorker] Kuyruk kaydı {item_id} işlendi → "
            f"Node: {lora_id}, Nem: %{moisture_value}, Karar: {decision}"
        )
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"[SyncWorker] Kuyruk kaydı {item_id} işlenirken hata: {e}")
        return False
    finally:
        db.close()


def _sync_loop() -> None:
    """Ana senkronizasyon döngüsü."""
    logger.info("[SyncWorker] Arka plan sync worker başlatıldı.")
    while True:
        try:
            pending = oq.get_pending(limit=50)
            if pending:
                logger.info(f"[SyncWorker] Kuyrukta {len(pending)} bekleyen kayıt bulundu.")
                for row in pending:
                    success = _process_one(row)
                    if success:
                        oq.delete_item(row[0])
                    else:
                        dropped = oq.increment_retries(row[0])
                        if dropped:
                            logger.warning(
                                f"[SyncWorker] Kayıt {row[0]} max deneme aşıldı, silindi."
                            )
            # else: kuyruk boş, sessizce bekle
        except Exception as e:
            logger.error(f"[SyncWorker] Beklenmedik hata: {e}")

        time.sleep(SYNC_INTERVAL_SECONDS)


def start_sync_worker() -> threading.Thread:
    """
    Sync worker'ı daemon thread olarak başlatır.
    main.py lifespan'ından çağrılmalıdır.
    """
    thread = threading.Thread(target=_sync_loop, daemon=True, name="SyncWorker")
    thread.start()
    logger.info("[SyncWorker] Thread başlatıldı.")
    return thread
