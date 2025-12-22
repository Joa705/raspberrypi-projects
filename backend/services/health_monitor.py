"""
Background health monitoring service for modules and cameras.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import logging

from database.db import AsyncSessionLocal
from database.models import Module, Camera

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor health of registered modules and cameras."""
    
    def __init__(self, check_interval: int = 60, timeout_minutes: int = 2):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Seconds between health checks (default: 60)
            timeout_minutes: Minutes before marking as offline (default: 2)
        """
        self.check_interval = check_interval
        self.timeout_minutes = timeout_minutes
        self._running = False
        self._task = None
    
    async def start(self):
        """Start the health monitoring background task."""
        if self._running:
            logger.warning("Health monitor already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Health monitor started (check every {self.check_interval}s, timeout after {self.timeout_minutes}m)")
    
    async def stop(self):
        """Stop the health monitoring background task."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_health(self):
        """Check health of all modules and cameras."""
        timeout_threshold = datetime.now() - timedelta(minutes=self.timeout_minutes)
        
        async with AsyncSessionLocal() as session:
            try:
                # Check modules
                module_result = await session.execute(
                    update(Module)
                    .where(
                        Module.last_seen < timeout_threshold,
                        Module.status != "offline"
                    )
                    .values(status="offline")
                    .returning(Module.module_id)
                )
                offline_modules = module_result.scalars().all()
                
                if offline_modules:
                    logger.warning(f"Marked {len(offline_modules)} module(s) as offline: {offline_modules}")
                
                # Check cameras
                camera_result = await session.execute(
                    update(Camera)
                    .where(
                        Camera.last_seen < timeout_threshold,
                        Camera.status != "offline"
                    )
                    .values(status="offline")
                    .returning(Camera.camera_id)
                )
                offline_cameras = camera_result.scalars().all()
                
                if offline_cameras:
                    logger.warning(f"Marked {len(offline_cameras)} camera(s) as offline: {offline_cameras}")
                
                await session.commit()
                
            except Exception as e:
                logger.error(f"Error checking health: {e}")
                await session.rollback()


# Global health monitor instance
health_monitor = HealthMonitor(check_interval=60, timeout_minutes=2)
