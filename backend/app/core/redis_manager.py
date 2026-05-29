import redis
from typing import Optional
import json
import pickle
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisManager:
    """Redis缓存管理器（支持优雅降级到本地缓存，带TTL）"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self._redis_available = False
        # 本地缓存存储格式: { key: { 'data': value, 'expire_at': timestamp } }
        self._local_cache = {}
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=False,
                socket_timeout=2,
                socket_connect_timeout=2
            )
            # 测试连接
            self.client.ping()
            self._redis_available = True
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，将使用本地缓存: {e}")
            self.client = None
    
    @property
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return self._redis_available
    
    def _clean_expired_cache(self):
        """清理过期的本地缓存"""
        now = time.time()
        expired_keys = [key for key, item in self._local_cache.items() 
                        if item.get('expire_at') and item['expire_at'] < now]
        for key in expired_keys:
            del self._local_cache[key]
        return len(expired_keys)
    
    def get(self, key: str) -> Optional[dict]:
        """获取缓存数据"""
        # 优先尝试Redis
        if self._redis_available:
            try:
                data = self.client.get(key)
                if data:
                    return pickle.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Redis get失败，使用本地缓存: {e}")
        
        # 降级到本地缓存（带TTL检查）
        # 定期清理过期缓存（每100次调用清理一次）
        if hash(key) % 100 == 0:
            expired_count = self._clean_expired_cache()
            if expired_count > 0:
                logger.debug(f"清理了 {expired_count} 条过期缓存")
        
        item = self._local_cache.get(key)
        if item:
            now = time.time()
            # 检查是否过期
            if item.get('expire_at') and item['expire_at'] < now:
                del self._local_cache[key]
                return None
            return item.get('data')
        
        return None
    
    def set(self, key: str, value: dict, expire: int = 3600) -> bool:
        """设置缓存数据"""
        # 同时写入Redis和本地缓存
        success = True
        
        if self._redis_available:
            try:
                serialized = pickle.dumps(value)
                self.client.setex(key, expire, serialized)
            except Exception as e:
                logger.warning(f"Redis set失败: {e}")
                success = False
        
        # 同时保存到本地缓存（带过期时间）
        self._local_cache[key] = {
            'data': value,
            'expire_at': time.time() + expire
        }
        
        # 清理本地缓存（保留最近的500条）
        if len(self._local_cache) > 500:
            # 按过期时间排序，删除最早过期的
            sorted_items = sorted(self._local_cache.items(), key=lambda x: x[1].get('expire_at', 0))
            oldest_keys = [k for k, _ in sorted_items[:len(self._local_cache) - 500]]
            for k in oldest_keys:
                del self._local_cache[k]
        
        return success
    
    def delete(self, key: str) -> int:
        """删除缓存"""
        count = 0
        
        if self._redis_available:
            try:
                count = self.client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete失败: {e}")
        
        if key in self._local_cache:
            del self._local_cache[key]
            count += 1
        
        return count
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if self._redis_available:
            try:
                return self.client.exists(key) > 0
            except Exception as e:
                logger.warning(f"Redis exists失败: {e}")
        
        return key in self._local_cache
    
    def clear_all(self) -> int:
        """清空所有缓存"""
        count = 0
        
        if self._redis_available:
            try:
                count = self.client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear_all失败: {e}")
        
        local_count = len(self._local_cache)
        self._local_cache.clear()
        
        return max(count, local_count)

redis_manager = RedisManager()