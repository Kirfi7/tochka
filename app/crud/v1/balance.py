from decimal import Decimal
from typing import Dict

from sqlalchemy import and_, select, update, or_
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logs.logs import error_log, info_logger
from app.crud.base import CRUDBase
from app.models.balance import Balance


class CRUDBalance(CRUDBase[Balance]):
    def __init__(self):
        super().__init__(Balance, primary_key_name='pk_balance')

    @error_log
    async def get_user_ticker_balance(
            self,
            user_id: str,
            ticker: str,
            session: AsyncSession | None = None,
    ) -> Decimal:
        result = await session.execute(
            select(self.model.amount).where(
                and_(self.model.user_id == user_id, self.model.ticker == ticker)
            )
        )
        balance = result.scalar_one_or_none()
        return balance or Decimal('0.0')

    @error_log
    async def get_user_available_balance(
            self,
            user_id: str,
            ticker: str,
            async_session: AsyncSession,
    ) -> int:
        """Получить доступный баланс пользователя (за вычетом заблокированных средств)"""
        result = await async_session.execute(
            select(self.model.amount, self.model.blocked_amount).where(
                and_(self.model.user_id == user_id, self.model.ticker == ticker)
            )
        )
        balance_row = result.first()
        if not balance_row:
            return 0

        amount, blocked_amount = balance_row
        return amount - blocked_amount

    @error_log
    async def get_user_balances(
            self,
            user_id: str,
            async_session: AsyncSession,
    ) -> Dict[str, int]:
        result = await async_session.execute(
            select(
                self.model.ticker,
                self.model.amount,
                self.model.blocked_amount
            ).where(
                self.model.user_id == user_id
            )
        )
        return {ticker: int(amount) for ticker, amount, blocked_amount in result.all()}

    @error_log
    async def deposit(
            self,
            user_id: str,
            ticker: str,
            amount: int,
            async_session: AsyncSession,
    ) -> Balance:
        error_log(f"Начало deposit: user_id={user_id}, ticker={ticker}, amount={amount}")
        if amount <= 0:
            error_log(f"Ошибка: сумма пополнения должна быть положительной")
            raise ValueError('Сумма пополнения должна быть положительной')

        try:
            error_log(f"Пытаемся обновить существующий баланс")
            result = await async_session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .values(amount=self.model.amount + amount)
                .returning(self.model)
            )
            balance = result.scalar_one_or_none()

            if not balance:
                error_log(f"Баланс не найден, создаем новый")
                balance = self.model(user_id=user_id, ticker=ticker, amount=amount, blocked_amount=0)
                async_session.add(balance)
                await async_session.flush()
                error_log(f"Новый баланс создан")

            await async_session.commit()
            error_log(f"Транзакция завершена успешно")
            return balance

        except IntegrityError as e:
            error_log(f"IntegrityError: {str(e)}")
            await async_session.rollback()
            if 'positive_balance' in str(e):
                raise ValueError('Итоговый баланс не может быть отрицательным')
            raise ValueError('Ошибка при пополнении баланса')
        except DataError as e:
            error_log(f"DataError: {str(e)}")
            await async_session.rollback()
            raise ValueError('Некорректная сумма')
        except Exception as e:
            error_log(f"Неожиданная ошибка: {str(e)}")
            await async_session.rollback()
            raise ValueError(f'Ошибка при пополнении баланса: {str(e)}')

    @error_log
    async def withdraw(
            self,
            user_id: str,
            ticker: str,
            amount: int,
            async_session: AsyncSession | None = None,
    ) -> Balance:
        if amount <= 0:
            raise ValueError('Сумма списания должна быть положительной')

        try:
            # Проверяем доступный баланс (с учетом заблокированных средств)
            available_amount = await self.get_user_available_balance(user_id, ticker, async_session)
            if available_amount < amount:
                raise ValueError('Недостаточно доступных средств на балансе')

            result = await async_session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .values(amount=self.model.amount - amount)
                .returning(self.model)
            )
            balance = result.scalar_one()

            await async_session.commit()
            return balance

        except IntegrityError as e:
            await async_session.rollback()
            if 'positive_balance' in str(e):
                raise ValueError('Итоговый баланс не может быть отрицательным')
            raise ValueError('Ошибка при списании средств')
        except DataError:
            await async_session.rollback()
            raise ValueError('Некорректная сумма')

    @error_log
    async def block_funds(
            self,
            user_id: str,
            ticker: str,
            amount: int,
            async_session: AsyncSession,
    ) -> Balance:
        """Блокировка средств для ордера"""
        if amount <= 0:
            raise ValueError('Сумма блокировки должна быть положительной')

        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            if ticker != "RUB":
                await async_session.execute(
                    select(self.model)
                    .where(and_(self.model.user_id == user_id, self.model.ticker == "RUB"))
                    .with_for_update()
                )
            # Проверяем доступный баланс
            available_amount = await self.get_user_available_balance(user_id, ticker, async_session)
            if available_amount < amount:
                raise ValueError('Недостаточно доступных средств для блокировки')

            result = await async_session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .values(blocked_amount=self.model.blocked_amount + amount)
                .returning(self.model)
            )
            balance = result.scalar_one()

            await async_session.commit()
            return balance
        except IntegrityError as e:
            await async_session.rollback()
            if 'blocked_not_exceed_amount' in str(e):
                raise ValueError('Сумма блокировки не может превышать общий баланс')
            raise ValueError('Ошибка при блокировке средств')

    @error_log
    async def unblock_funds(
            self,
            user_id: str,
            ticker: str,
            amount: int,
            async_session: AsyncSession,
    ) -> Balance:
        """Разблокировка средств при отмене или исполнении ордера"""
        if amount <= 0:
            raise ValueError('Сумма разблокировки должна быть положительной')

        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            if ticker != "RUB":
                await async_session.execute(
                    select(self.model)
                    .where(and_(self.model.user_id == user_id, self.model.ticker == "RUB"))
                    .with_for_update()
                )
            result = await async_session.execute(
                select(self.model)
                .where(
                    and_(self.model.user_id == user_id, self.model.ticker == ticker)
                )
                .with_for_update()
            )
            balance = result.scalar_one_or_none()

            if not balance or balance.blocked_amount < amount:
                raise ValueError('Недостаточно заблокированных средств для разблокировки')

            balance.blocked_amount -= amount
            await async_session.commit()

            return balance
        except IntegrityError:
            await async_session.rollback()
            raise ValueError('Ошибка при разблокировке средств')

    @error_log
    async def block_assets(
            self,
            user_id: str,
            ticker: str,
            qty: int,
            async_session: AsyncSession,
    ) -> Balance:
        info_logger.info("block_assets")
        """Блокировка активов для ордера на продажу"""
        return await self.block_funds(user_id, ticker, qty, async_session)

    @error_log
    async def unblock_assets(
            self,
            user_id: str,
            ticker: str,
            qty: int,
            async_session: AsyncSession,
    ) -> Balance:
        """Разблокировка активов при отмене или исполнении ордера на продажу"""
        return await self.unblock_funds(user_id, ticker, qty, async_session)

    @error_log
    async def complete_buy(
            self,
            user_id: str,
            ticker: str,
            amount_block: int,
            amount_withdraw: int,
            async_session: AsyncSession,
    ):
        """Разблокировка средств при отмене или исполнении ордера"""
        if amount_block <= 0:
            raise ValueError('Сумма разблокировки должна быть положительной')

        if amount_withdraw <= 0:
            raise ValueError('Сумма списывания должна быть положительной')

        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            rub_block = (await async_session.execute(
                select(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == "RUB"))
                .with_for_update()
            )).scalar_one()

            ticker_block = (await async_session.execute(
                select(self.model)
                .where(
                    and_(self.model.user_id == user_id, self.model.ticker == ticker)
                )
                .with_for_update()
            )).scalar_one()

            if rub_block.blocked_amount < amount_block:
                raise ValueError('Недостаточно заблокированных средств для разблокировки')

            if ticker_block.amount < amount_withdraw:
                raise ValueError('Недостаточно доступных средств для блокировки')

            (await async_session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == "RUB"))
                .values(amount=self.model.amount - amount_withdraw,
                        blocked_amount=self.model.blocked_amount - amount_block)
                .returning(self.model)
            )).scalar_one()

            (await async_session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .values(amount=self.model.amount + amount_block)
                .returning(self.model)
            )).scalar_one()

            await async_session.commit()

        except IntegrityError as e:
            await async_session.rollback()
            if 'positive_balance' in str(e):
                raise ValueError('Итоговый баланс не может быть отрицательным')
            raise ValueError('Ошибка при списании средств')
        except DataError:
            await async_session.rollback()
            raise ValueError('Некорректная сумма')

    @error_log
    async def try_block_ticker(
            self,
            user_id: str,
            ticker: str,
            amount: int,
            session: AsyncSession,
    ) -> bool:
        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            ticker_balance = (await session.execute(
                select(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .with_for_update()
            )).scalar_one()

            if ticker_balance.amount < amount:
                raise ValueError('Недостаточно доступных средств для блокировки')

            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .values(blocked_amount=self.model.blocked_amount + amount)
                .returning(self.model)
            )).scalar_one()

            await session.commit()
            return True
        except IntegrityError as e:
            await session.rollback()
            return False

    @error_log
    async def try_block_buy(
            self,
            user_buy_id: str,
            ticker_user_buy: str,
            amount_user_buy: int,

            user_sell_id: str,
            ticker_user_sell: str,
            amount_user_sell: int,

            session: AsyncSession,
    ) -> bool:
        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            ticker_user_buy_block = (await session.execute(
                select(self.model)
                .where(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_buy))
                .with_for_update()
            )).scalar_one()
            ticker_user_sell_block = (await session.execute(
                select(self.model)
                .where(and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_sell))
                .with_for_update()
            )).scalar_one()

            if ticker_user_buy_block.amount < amount_user_buy:
                raise ValueError('Недостаточно доступных средств для блокировки')

            if ticker_user_sell_block.amount < amount_user_sell:
                raise ValueError('Недостаточно доступных средств для блокировки')

            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_buy))
                .values(blocked_amount=self.model.blocked_amount + amount_user_buy)
                .returning(self.model)
            )).scalar_one()
            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_sell))
                .values(blocked_amount=self.model.blocked_amount + amount_user_sell)
                .returning(self.model)
            )).scalar_one()

            await session.commit()
            return True
        except IntegrityError as e:
            await session.rollback()
            return False

    async def commit_buy(
            self,
            user_buy_id: str,
            ticker_user_buy: str,
            amount_user_buy: int,

            user_sell_id: str,
            ticker_user_sell: str,
            amount_user_sell: int,

            session: AsyncSession,
    ) -> bool:
        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            (await session.execute(
                select(self.model)
                .where(or_(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_buy),
                           and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_sell)))
                .with_for_update()
            ))

            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_buy))
                .values(amount=self.model.amount - amount_user_buy,
                        blocked_amount=self.model.blocked_amount - amount_user_buy)
                .returning(self.model)
            )).scalar_one()
            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_sell))
                .values(amount=self.model.amount + amount_user_sell)
                .returning(self.model)
            )).scalar_one()

            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_sell))
                .values(amount=self.model.amount - amount_user_sell,
                        blocked_amount=self.model.blocked_amount - amount_user_sell)
                .returning(self.model)
            )).scalar_one()
            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_buy))
                .values(amount=self.model.amount + amount_user_buy)
                .returning(self.model)
            )).scalar_one()

            await session.commit()
            return True
        except IntegrityError as e:
            await session.rollback()
            return False

    async def try_block_and_buy(
            self,
            user_buy_id: str,
            ticker_user_buy: str,
            amount_user_buy: int,

            user_sell_id: str,
            ticker_user_sell: str,
            amount_user_sell: int,

            session: AsyncSession,
    ) -> bool:
        try:
            # Строгий порядок блокировок: сначала RUB, потом тикер
            ticker_balances = (await session.execute(
                select(self.model)
                .where(or_(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_buy),
                           and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_sell)))
                .with_for_update()
            )).scalars().all()
            ticker_balance_buy = [x for x in ticker_balances if x.user_id == user_buy_id][0]

            if ticker_balance_buy.amount - ticker_balance_buy.blocked_amount < amount_user_buy:
                return False

            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_buy))
                .values(amount=self.model.amount - amount_user_buy)
                .returning(self.model)
            )).scalar_one()
            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_buy_id, self.model.ticker == ticker_user_sell))
                .values(amount=self.model.amount + amount_user_sell)
                .returning(self.model)
            )).scalar_one()

            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_sell))
                .values(amount=self.model.amount - amount_user_sell,
                        blocked_amount=self.model.blocked_amount - amount_user_sell)
                .returning(self.model)
            )).scalar_one()
            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_sell_id, self.model.ticker == ticker_user_buy))
                .values(amount=self.model.amount + amount_user_buy)
                .returning(self.model)
            )).scalar_one()

            await session.commit()
            return True
        except IntegrityError as e:
            await session.rollback()
            return False

    @error_log
    async def release_ticker(
            self,
            user_id: str,
            ticker: str,
            amount: int,
            session: AsyncSession,
    ):
        try:
            (await session.execute(
                update(self.model)
                .where(and_(self.model.user_id == user_id, self.model.ticker == ticker))
                .values(blocked_amount=self.model.blocked_amount - amount)
                .returning(self.model)
            )).scalar_one()

            await session.commit()
        except IntegrityError as e:
            await session.rollback()
            raise e


balance_crud = CRUDBalance()
