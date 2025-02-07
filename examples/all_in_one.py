import asyncio
import logging

from risclog.logging import get_logger, getLogger, log_decorator

logger = get_logger(__name__)
logger.set_level(logging.DEBUG)
file_logger = getLogger(__name__).add_file_handler(
    'test.log', level=logging.WARNING
)


# @log_decorator
@logger.decorator()
def sync_function(a, b):
    result = a + b
    return result


@log_decorator
async def async_function(a, b):
    await asyncio.sleep(1)
    result = a + b
    return result


class AwesomeClass:
    def __init__(self):
        self.logger = getLogger(name='AwesomeLogger')

    @log_decorator
    def class_sync_add(self, a: int, b: int):
        self.logger.warn('Debugging class_sync_add', a=a, b=b)
        self.logger.info('Information in class_sync_add', a=a, b=b)
        self.logger.info('class_sync_add called', a=a, b=b)
        return a + b

    @log_decorator
    async def class_async_add(self, a: int, b: int, c: dict):
        await self.logger.info('class_async_add called', a=a, b=b)
        await self.logger.info(
            'dependency class name:', c=c['dependency'].__class__.__name__
        )
        await asyncio.sleep(1)
        result = a + b
        await self.logger.info('class_async_add result', result=result)
        return result


class DependencyClass:
    def __init__(self):
        pass

    @classmethod
    def direct_method(cls):
        logger.info('Direct method called')


@log_decorator
def sample_function(*args, **kwargs):
    logger.debug('Debugging sample_function', args=args, kwargs=kwargs)
    logger.info('Called with args', args=args)
    logger.info('Called with kwargs', kwargs=kwargs)

    result = {'sum_args': sum(args) if args else 0, **kwargs}
    logger.info('Result', result=result)
    if result['sum_args'] > 5:
        logger.warning(
            'Sum of arguments is greater than 5', sum=result['sum_args']
        )

    try:
        1 / 0
    except ZeroDivisionError:
        logger.error(
            'Division by zero error occurred during calculation. Check the input values',
            exc_info=True,
        )
        pass
    return result


@log_decorator
def sample_critical_function(*args, **kwargs):
    logger.critical(
        'Critical issue in sample_critical_function', args=args, kwargs=kwargs
    )
    raise RuntimeError('Simuliertes kritisches Problem')


async def main():
    dc = DependencyClass()
    ac = AwesomeClass()
    for i in range(1):
        sync_function(3, 5)
        await async_function(4, 6)
        ac.class_sync_add(6, 7)
        await ac.class_async_add(8, 9, {'dependency': dc})
        sample_function(1, 2, 3, name='Alice', age=30)

        try:
            sample_critical_function(10, 20)
        except RuntimeError:
            pass


if __name__ == '__main__':
    # optional set new log level
    # logger.set_level(logging.ERROR)
    sync_result = sync_function(3, 5)
    asyncio.run(main())
    DependencyClass.direct_method()
    # test rich exception format
    raise ValueError('Test')
