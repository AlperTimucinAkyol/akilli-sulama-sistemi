"""
offline_queue.py
================
PostgreSQL meşgul/bakımda olduğunda gelen sensör verilerini
SQLite tablosuna geçici olarak yazar.
Sync worker bu tabloyu periyodik olarak kontrol edip PostgreSQL'e aktarır.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Backend klasörüne komşu olacak şekilde konumlandır
QUEUE_DB_PATH = Path(__file__).parent / "offline_queue.db"

# Maksimum yeniden deneme sayısı — bu kadar başarısız olursa kayıt silinir
MAX_RETRIES = 5


def init_queue() -> None:
    """Uygulama başlangıcında SQLite tablosunu oluşturur (yoksa)."""
    with sqlite3.connect(QUEUE_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_queue (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                lora_id       TEXT    NOT NULL,
                moisture_value REAL   NOT NULL,
                received_at   TEXT    NOT NULL,
                retries       INTEGER DEFAULT 0
            )
        """)
        conn.commit()
    logger.info(f"[OfflineQueue] SQLite kuyruk hazır: {QUEUE_DB_PATH}")


def enqueue(lora_id: str, moisture_value: float) -> None:
    """Yeni bir sensör ölçümünü kuyruğa ekler."""
    with sqlite3.connect(QUEUE_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO sensor_queue (lora_id, moisture_value, received_at) VALUES (?, ?, ?)",
            (lora_id, float(moisture_value), datetime.now().isoformat())
        )
        conn.commit()
    logger.warning(
        f"[OfflineQueue] Veri kuyruğa alındı (PostgreSQL erişilemez) "
        f"→ Node: {lora_id}, Nem: %{moisture_value}"
    )


def get_pending(limit: int = 50) -> list[tuple]:
    """
    İşlenmemiş kayıtları döndürür.
    Her satır: (id, lora_id, moisture_value, received_at, retries)
    """
    with sqlite3.connect(QUEUE_DB_PATH) as conn:
        rows = conn.execute(
            """SELECT id, lora_id, moisture_value, received_at, retries
               FROM sensor_queue
               ORDER BY id ASC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return rows


def delete_item(item_id: int) -> None:
    """Başarıyla işlenen kaydı kuyruktan kaldırır."""
    with sqlite3.connect(QUEUE_DB_PATH) as conn:
        conn.execute("DELETE FROM sensor_queue WHERE id = ?", (item_id,))
        conn.commit()


def increment_retries(item_id: int) -> int:
    """
    Başarısız deneme sayısını artırır.
    MAX_RETRIES'e ulaşıldıysa kaydı siler ve True döndürür.
    """
    with sqlite3.connect(QUEUE_DB_PATH) as conn:
        conn.execute(
            "UPDATE sensor_queue SET retries = retries + 1 WHERE id = ?",
            (item_id,)
        )
        conn.commit()
        retries = conn.execute(
            "SELECT retries FROM sensor_queue WHERE id = ?", (item_id,)
        ).fetchone()

    if retries and retries[0] >= MAX_RETRIES:
        logger.error(
            f"[OfflineQueue] Kayıt {item_id} {MAX_RETRIES} denemeden sonra "
            f"işlenemedi, kuyruktan siliniyor."
        )
        delete_item(item_id)
        return True  # Silindi
    return False  # Hâlâ kuyrukta


def queue_size() -> int:
    """Kuyruktaki bekleyen kayıt sayısını döndürür."""
    with sqlite3.connect(QUEUE_DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) FROM sensor_queue").fetchone()[0]
    return count
