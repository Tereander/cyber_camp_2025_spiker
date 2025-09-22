# Правило 1: Проверка на Card Data Exfiltration
event_source = "bot_server_logs"
http_method = "POST"
target_domain NOT IN ("api.telegram.org", "legit-payment-provider.com", ...)
content_type = "application/octet-stream" OR user_agent = "Python-aiohttp*"
-> ALERT "Possible Card Data Exfiltration from Bot Server"

# Правило 2: Проверка на P2P Polling
event_source = "network_traffic"
source_ip = "bot_server_ip"
destination_domain IN ("api.qiwi.com", "yoomoney.ru", "cryptocurrency-api.com")
http_url = "/v1/bills/*" OR "/api/account*"
AND event_count > 60 per hour # Частые периодические запросы
-> ALERT "Suspicious P2P Payment Polling Activity"

# Правило 3: Проверка на Phishing Domain Propagation
event_source = "telegram_bot_scanning"
bot_response contains "url="
AND domain(extracted_url) is_newly_registered (age < 30 days)
AND domain(extracted_url) has_suspicious_tld (.xyz, .club, .top)
OR idn_homograph_of("telegram.org", "qiwi.com")
-> ALERT "Bot distributing links to potential phishing domain"

