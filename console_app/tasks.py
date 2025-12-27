"""
TTS 任务处理 - 发送到 Celery
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_tts_order_to_queue(order):
    """
    将 TTS 任务发送到 Celery 队列。
    
    Args:
        order: TTSOrder 实例
    """
    from celery import Celery
    
    # 配置 Celery 连接
    broker_url = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
    app = Celery('geminar_worker', broker=broker_url)
    
    message = {
        'id': str(order.id),
        'text': order.text,
        'spk_id': order.spk_id,
    }
    
    try:
        # 发送任务到 worker
        app.send_task(
            'worker.tasks.handle_tts_order_created',
            args=[message],
            queue='celery'
        )
        logger.info(f"TTS order {order.id} sent to Celery queue")
        
    except Exception as e:
        logger.error(f"Failed to send TTS order {order.id} to queue: {e}")
        raise
