from dependency_injector import containers, providers

from slackhealthbot.settings import AppSettings, SecretSettings, Settings


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    wiring_config = containers.WiringConfiguration(
        modules=[
            "slackhealthbot.domain.usecases.fitbit.usecase_process_daily_activity",
            "slackhealthbot.domain.usecases.fitbit.usecase_process_new_activity",
            "slackhealthbot.domain.usecases.slack.usecase_post_user_logged_out",
        ],
    )

    app_settings: AppSettings = providers.Factory(AppSettings)
    secret_settings: SecretSettings = providers.Factory(SecretSettings)
    settings: Settings = providers.Singleton(
        Settings,
        app_settings,
        secret_settings,
    )
