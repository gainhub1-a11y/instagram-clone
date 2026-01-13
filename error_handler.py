"""
Error handler with retry logic and exponential backoff
"""
import logging
import asyncio
from functools import wraps
from typing import Callable, Any, Optional
from config import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Handles errors with retry logic and exponential backoff"""
    
    def __init__(self):
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
    
    def with_retry(
        self,
        max_retries: Optional[int] = None,
        module_name: str = "Unknown",
        scenario: str = "Unknown operation",
        fallback_func: Optional[Callable] = None
    ):
        """
        Decorator to add retry logic to async functions
        
        Args:
            max_retries: Maximum number of retries (default from config)
            module_name: Name of the module for logging
            scenario: Description of the operation
            fallback_func: Optional fallback function to call if all retries fail
        """
        max_attempts = max_retries if max_retries is not None else self.max_retries
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        logger.info(f"{module_name}: Attempt {attempt}/{max_attempts}")
                        result = await func(*args, **kwargs)
                        
                        if attempt > 1:
                            logger.info(f"{module_name}: Success on attempt {attempt}")
                        
                        return result
                    
                    except Exception as e:
                        last_exception = e
                        logger.warning(
                            f"{module_name}: Attempt {attempt} failed: {str(e)}"
                        )
                        
                        if attempt < max_attempts:
                            delay = self.retry_delay * (2 ** (attempt - 1))
                            logger.info(f"Retrying in {delay} seconds...")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                f"{module_name}: All {max_attempts} attempts failed"
                            )
                
                # All retries failed
                if fallback_func:
                    logger.info(f"{module_name}: Attempting fallback function")
                    try:
                        return await fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"{module_name}: Fallback also failed: {str(fallback_error)}"
                        )
                        raise fallback_error
                
                raise last_exception
            
            return wrapper
        return decorator


def create_error_handler() -> ErrorHandler:
    """Factory function to create an ErrorHandler instance"""
    return ErrorHandler()
