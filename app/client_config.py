clients = [
    {
        "email": "granit.g4shii@gmail.com",
        "n8n_webhook": "https://client1.myautomation.com/webhook/facebook-token"
    },
    {
        "email": "another.client@example.com",
        "n8n_webhook": "https://client2.myautomation.com/webhook/facebook-token"
    }
]

def get_n8n_webhook_by_email(email: str) -> str | None:
    for client in clients:
        if client["email"] == email:
            return client["n8n_webhook"]
    return None