"""Async job manager for long-running backtest operations."""

import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .schemas import BacktestJob, JobStatus


logger = logging.getLogger(__name__)


class JobManager:
    """
    In-memory job manager for async backtest execution.
    
    Jobs are stored in memory and will be lost on server restart.
    This is acceptable for MVP - can add persistence later if needed.
    """
    
    def __init__(self, max_jobs: int = 100):
        """
        Initialize job manager.
        
        Args:
            max_jobs: Maximum number of jobs to keep in memory (oldest are pruned)
        """
        self._jobs: Dict[str, BacktestJob] = {}
        self._lock = threading.Lock()
        self._max_jobs = max_jobs
    
    def create_job(
        self,
        strategy: str,
        tickers: str,
        start_date: str,
        end_date: str
    ) -> BacktestJob:
        """
        Create a new pending job.
        
        Args:
            strategy: Strategy name
            tickers: Comma-separated ticker symbols
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Created BacktestJob
        """
        job_id = str(uuid.uuid4())[:8]  # Short ID for readability
        
        job = BacktestJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            strategy=strategy,
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now()
        )
        
        with self._lock:
            # Prune old jobs if at capacity
            self._prune_if_needed()
            self._jobs[job_id] = job
        
        logger.info(f"Created job {job_id} for strategy {strategy}")
        return job
    
    def get_job(self, job_id: str) -> Optional[BacktestJob]:
        """Get a job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def list_jobs(self, limit: int = 20) -> List[BacktestJob]:
        """
        List recent jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs, newest first
        """
        with self._lock:
            jobs = list(self._jobs.values())
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Update job status.
        
        Args:
            job_id: Job ID to update
            status: New status
            result: Backtest result (for completed jobs)
            error: Error message (for failed jobs)
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found for status update")
                return
            
            job.status = status
            
            if status == JobStatus.RUNNING:
                job.started_at = datetime.now()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.now()
            
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
        
        logger.info(f"Updated job {job_id} status to {status}")
    
    def run_job_async(
        self,
        job_id: str,
        task: Callable[[], Dict[str, Any]]
    ) -> None:
        """
        Run a job asynchronously in a background thread.
        
        Args:
            job_id: Job ID
            task: Callable that runs the backtest and returns result dict
        """
        def worker():
            try:
                self.update_job_status(job_id, JobStatus.RUNNING)
                result = task()
                self.update_job_status(job_id, JobStatus.COMPLETED, result=result)
            except Exception as e:
                logger.exception(f"Job {job_id} failed")
                self.update_job_status(job_id, JobStatus.FAILED, error=str(e))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        logger.info(f"Started background thread for job {job_id}")
    
    def _prune_if_needed(self) -> None:
        """Remove oldest completed/failed jobs if at capacity."""
        if len(self._jobs) < self._max_jobs:
            return
        
        # Get completed/failed jobs sorted by created_at
        prunable = [
            j for j in self._jobs.values()
            if j.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]
        prunable.sort(key=lambda j: j.created_at)
        
        # Remove oldest until under capacity
        to_remove = len(self._jobs) - self._max_jobs + 10  # Remove 10 extra for buffer
        for job in prunable[:to_remove]:
            del self._jobs[job.job_id]
            logger.debug(f"Pruned old job {job.job_id}")


# Global job manager instance
job_manager = JobManager()
