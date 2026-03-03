import jinja2
from aiobotocore.session import get_session

from src.config import get_settings
from src.config.tkq import broker


settings = get_settings()
template_loader = jinja2.FileSystemLoader(searchpath="./src/templates")
template_env = jinja2.Environment(loader=template_loader)


@broker.task(
    retries=3,
    retry_on_error=True,
    default_retry_delay=15,
)
async def send_activation_email_task(email: str, activation_link: str):
    template = template_env.get_template("activation_email.html")
    html_content = template.render(activation_link=activation_link)

    session = get_session()
    async with session.create_client(
        "ses",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ) as client:
        await client.send_email(
            Source=settings.MAIL_FROM,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Account activation Finanser"},
                "Body": {
                    "Html": {"Data": html_content},
                    "Text": {"Data": f"Activation link: {activation_link}"},
                },
            },
        )
