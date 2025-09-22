# tasks.py (Модуль Celery)
from celery import Celery
from celery.schedules import crontab
import requests

app = Celery('scam_tasks', broker='redis://localhost:6379/0')

# Конфигурация периодических задач
app.conf.beat_schedule = {
    'check-payments-every-minute': {
        'task': 'tasks.check_all_pending_payments',
        'schedule': crontab(minute='*/1'),  # Каждую минуту
    },
}
app.conf.timezone = 'UTC'

@app.task
def check_all_pending_payments():
    """Задача Celery: проверяет все активные кошельки"""
    pending_wallets = get_all_pending_wallets_from_db()  # Функция для получения кошельков из БД
    for wallet in pending_wallets:
        check_single_payment.delay(wallet.number, wallet.amount, wallet.user_id)

@app.task
def check_single_payment(wallet_number, expected_amount, user_id):
    """Проверяет баланс конкретного кошелька"""
    # Используется неофициальное/легальное API
    response = requests.post(
        'https://api.qiwi.com/partner/bill/v1/bills/' + wallet_number,
        auth=('Bearer', config.SCAMMER_QIWI_TOKEN)
    )
    bill_data = response.json()

    if bill_data['status']['value'] == 'PAID':
        amount = float(bill_data['amount']['value'])
        if amount >= expected_amount:
            # Платеж подтвержден
            mark_payment_as_paid_in_db(wallet_number)
            asyncio.run(bot.send_message(user_id, "Оплата подтверждена!"))

# В обработчике команды старта в боте:
@dp.message_handler(commands='buy')
async def cmd_buy(message: types.Message):
    # ... Генерация уникального кошелька через API
    new_wallet = generate_qiwi_wallet(message.from_user.id)
    # Сохраняем номер кошелька и сумму в БД для последующего опроса
    save_wallet_to_db(new_wallet, user_id=message.from_user.id, amount=1000)
    await message.answer(f"Оплатите 1000 руб. на номер {new_wallet}")