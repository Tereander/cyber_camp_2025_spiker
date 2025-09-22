from aiogram import types, Dispatcher
from aiogram.types import LabeledPrice, PreCheckoutQuery
import logging
from your_app.models import Order, User  # Пример импорта моделей

logger = logging.getLogger(__name__)

async def create_invoice(message: types.Message):
    """Создание инвойса с валидацией бизнес-логики"""
    user, _ = await User.get_or_create(tg_id=message.from_user.id)
    try:
        # Проверка наличия товара, лимитов пользователя и т.д.
        item_price = await validate_order(user)
        prices = [LabeledPrice(label="Товар", amount=item_price)]

        # Формирование инвойса
        await message.bot.send_invoice(
            chat_id=message.chat.id,
            title="Premium подписка",
            description="Доступ на 30 дней",
            provider_token=config.PAYMENTS_PROVIDER_TOKEN,  # Токен из настроек
            currency="rub",
            prices=prices,
            payload=f"order_{user.id}_{uuid4().hex}",  # Уникальный payload для корреляции
            start_parameter="premium_subscription",
            need_email=True,
            need_phone_number=False
        )
    except ValidationError as e:
        logger.error(f"Invoice validation failed for user {user.tg_id}: {e}")
        await message.answer("В данный момент заказ невозможен.")

async def pre_checkout_handler(query: PreCheckoutQuery):
    """Валидация перед списанием средств"""
    # Декодируем payload, проверяем данные в БД
    payload_parts = query.invoice_payload.split('_')
    if len(payload_parts) != 3:
        await query.answer(ok=False, error_message="Ошибка в данных заказа.")
        return

    order_id = payload_parts[1]
    order_exists = await Order.filter(id=order_id).exists()

    if not order_exists:
        await query.answer(ok=False, error_message="Заказ не найден.")
        return

    await query.answer(ok=True)  # Подтверждаем возможность списания

async def successful_payment_handler(message: types.Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    # Коррелируем платеж с заказом через payload
    order_id = payment.invoice_payload.split('_')[1]

    order = await Order.get(id=order_id)
    order.status = "paid"
    await order.save()

    # Активируем услугу для пользователя
    await activate_premium(order.user)

    logger.info(f"Successful payment for order {order_id}, amount: {payment.total_amount}")

def register_payment_handlers(dp: Dispatcher):
    dp.register_message_handler(create_invoice, commands=["buy"])
    dp.register_pre_checkout_query_handler(pre_checkout_handler)
    dp.register_message_handler(successful_payment_handler, content_types=types.ContentType.SUCCESSFUL_PAYMENT)
